import logging
import re
import os
import sqlite3
import random
from datetime import datetime
import aiohttp
from livekit.agents import RunContext, function_tool

logger = logging.getLogger("agent")

try:
    from db import get_caller_by_id_or_name, upsert_caller
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db import get_caller_by_id_or_name, upsert_caller

try:
    import schemes_data
except ImportError:
    # pyrefly: ignore [missing-import]
    from src import schemes_data

try:
    from db_dashboard import DB_PATH as DASHBOARD_DB_PATH
    from db_dashboard import add_escalation as save_local_escalation
    from db_dashboard import init_db as init_dashboard_db
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db_dashboard import DB_PATH as DASHBOARD_DB_PATH  # type: ignore
    from src.db_dashboard import (  # type: ignore
        add_escalation as save_local_escalation,
    )
    from src.db_dashboard import init_db as init_dashboard_db  # type: ignore


def status_helper(ticker: str) -> str:
    return "INR" if ticker.endswith(".NS") or ticker in ["^NSEI", "^BSESN"] else "USD"


class AssistantTools:
    @function_tool
    async def lookup_financial_service(
        self,
        context: RunContext,
        module_name: str,
        service_name: str,
        target_currency: str = "INR",
    ) -> str:
        """Use this tool to look up detailed information on any financial service, investment, banking help, security guidelines, or government scheme.
        It returns descriptions, eligibility rules, interest rates, charges, and document checklists.
        It supports live exchange rate conversions or live cryptocurrency rate check if requested.

        Args:
            module_name: The name of the category (e.g. banking, digital_payments, loans_credit, investments, insurance, retirement, tax_planning, government_schemes, business_finance, international_finance, financial_security, financial_planning, consumer_banking_help).
            service_name: The name of the specific service (e.g. savings_account, current_account, fd, rd, debit_cards, atm_mobile_banking, upi, qr_payments, imps_neft_rtgs, wallets_bill_payments, personal_loan, home_loan, education_loan, credit_score, stocks_mutual_funds, sip, bonds_etfs_gsec, bitcoin, ethereum, life_insurance, health_insurance, motor_insurance, nps, epf, income_tax_basics, tax_saving_investments, pmjdy, pm_kisan, pmjjby, pmsby, apy, ssy, mudra, business_loan, working_capital, forex_remittances, kyc_safety, otp_fraud_safety, reporting_fraud, budgeting_saving, failed_transactions, card_blocking).
            target_currency: The currency to display money values in (e.g. INR, USD, EUR, GBP). Defaults to INR.
        """
        logger.info(
            f"Looking up financial service. module={module_name}, service={service_name}, currency={target_currency}"
        )

        module = module_name.lower().strip()
        service = service_name.lower().strip()

        # Handle live crypto rate queries under investments category
        if module == "investments" and service in ["bitcoin", "ethereum"]:
            price, timestamp, is_fallback = schemes_data.get_crypto_rate(service)
            source_msg = (
                f"As of {timestamp}" if not is_fallback else f"Notice: {timestamp}"
            )
            status = f"The live price of {service.capitalize()} is Rs {price:,.2f} INR ({source_msg})."
            if is_fallback:
                status = "Notice: Live connection to crypto index is offline. " + status
            return status

        # Handle general database queries
        mod_db = schemes_data.FINANCIAL_DATABASE.get(module)
        if not mod_db:
            return f"Category '{module_name}' not found. Available categories include: banking, digital_payments, loans_credit, investments, insurance, retirement, tax_planning, government_schemes, business_finance, international_finance, financial_security, financial_planning, consumer_banking_help."

        serv_db = mod_db.get(service)
        if not serv_db:
            return f"Service '{service_name}' not found in category '{module_name}'. Please specify a valid service like: {', '.join(mod_db.keys())}."

        desc = serv_db.get("description", "")
        rates = serv_db.get("rates", "")
        elig = serv_db.get("eligibility", "")
        checklist = ", ".join(serv_db.get("checklist", []))

        # Check for currency conversion
        curr = target_currency.upper().strip()
        conv_msg = ""
        if curr != "INR":
            rate, timestamp, is_fallback = schemes_data.get_exchange_rate(curr)
            source_msg = (
                f"As of today's live rate ({timestamp})"
                if not is_fallback
                else f"Notice: Using offline backup rate ({timestamp})"
            )

            # Simple heuristic parser to identify rupees in rates text and convert them
            if "Rs 20" in rates:
                conv_msg += f" Note: Rs 20 premium converts to approx {rate * 20:.2f} {curr} ({source_msg})."
            if "Rs 436" in rates:
                conv_msg += f" Note: Rs 436 premium converts to approx {rate * 436:.2f} {curr} ({source_msg})."
            if "Rs 6,000" in rates:
                conv_msg += f" Note: Rs 6,000 benefit converts to approx {rate * 6000:.2f} {curr} ({source_msg})."
            if "Rs 10,000" in rates:
                conv_msg += f" Note: Rs 10,000 overdraft converts to approx {rate * 10000:.2f} {curr} ({source_msg})."
            if "Rs 10 Lakh" in rates:
                conv_msg += f" Note: Rs 10 Lakh converts to approx {rate * 1000000:.2f} {curr} ({source_msg})."
            if "Rs 2 Lakh" in rates or "2 Lakh" in rates or "2 lakh" in rates:
                conv_msg += f" Note: Rs 2 Lakh coverage converts to approx {rate * 200000:.2f} {curr} ({source_msg})."
            if "Rs 1 Lakh" in rates or "1 Lakh" in rates or "1 lakh" in rates:
                conv_msg += f" Note: Rs 1 Lakh coverage converts to approx {rate * 100000:.2f} {curr} ({source_msg})."
            if is_fallback and not conv_msg:
                conv_msg = f" Note: Using offline backup exchange rate 1 INR = {rate} {curr} due to connection timeout."

        output = f"Service: {service.replace('_', ' ').capitalize()}\nDescription: {desc}\nRates/Charges: {rates}{conv_msg}\nEligibility: {elig}\nRequired Documents Checklist: {checklist}"
        self.call_success = True
        self.success_reason = "LOOKUP_FINANCIAL_SERVICE"
        self.failure_reason = None
        return output

    @function_tool
    async def calculate_financials(
        self,
        context: RunContext,
        tool_type: str,
        principal: float,
        interest_rate: float,
        tenure_years: int,
        times_compounded: int = 1,
        monthly_income: float | None = None,
    ) -> str:
        """Use this tool to calculate monthly EMI for a loan or to calculate compound interest for savings/investments.

        Args:
            tool_type: The type of calculation, either 'emi' or 'compound_interest'.
            principal: The principal amount (loan amount or investment amount) in rupees.
            interest_rate: The annual interest rate percentage (e.g. 8.5 for 8.5%).
            tenure_years: The tenure/duration in years.
            times_compounded: Number of times interest is compounded per year (only for 'compound_interest'). Defaults to 1.
            monthly_income: Optional monthly income of the user in rupees to analyze the financial viability and provide decisions.
        """
        logger.info(
            f"Running financial calculator. type={tool_type}, principal={principal}, rate={interest_rate}, tenure={tenure_years}, monthly_income={monthly_income}"
        )
        ttype = tool_type.lower().strip()
        if ttype in ["emi", "compound_interest"]:
            self.call_success = True
            self.success_reason = "CALCULATE_FINANCIALS"
            self.failure_reason = None
        if ttype == "emi":
            res = schemes_data.calculate_loan_emi(
                principal, interest_rate, tenure_years
            )
            emi = res["monthly_emi"]
            advice = ""
            if monthly_income and monthly_income > 0:
                dti = (emi / monthly_income) * 100
                if dti > 40:
                    advice = f" Decision Advice: Warning. This monthly EMI would consume {dti:.1f}% of your monthly income, which exceeds the recommended 40% threshold. This loan may be financially risky. Consider lower principal, longer tenure, or a lower interest rate."
                else:
                    advice = f" Decision Advice: Good news. This EMI is {dti:.1f}% of your monthly income, which is within the safe zone (under 40%)."
            else:
                advice = " Decision Advice: Please provide your monthly income if you'd like me to analyze whether this loan EMI fits safely within your budget."
            return f"EMI calculation results: Monthly EMI is Rs {emi:,.2f}, Total payment over tenure is Rs {res['total_payment']:,.2f}, Total interest payable is Rs {res['total_interest']:,.2f}.{advice}"
        elif ttype == "compound_interest":
            res = schemes_data.calculate_compound_interest(
                principal, interest_rate, tenure_years, times_compounded
            )
            comp_name = {
                1: "annually",
                2: "semi-annually",
                4: "quarterly",
                12: "monthly",
            }.get(times_compounded, f"{times_compounded} times a year")
            advice = ""
            if monthly_income and monthly_income > 0:
                target_savings_monthly = monthly_income * 0.20
                advice = f" Decision Advice: Based on the 50/30/20 rule, it is highly recommended to save or invest at least 20% of your monthly income, which is Rs {target_savings_monthly:,.2f} per month, to secure your financial future."
            else:
                advice = " Decision Advice: Please provide your monthly income if you'd like me to analyze how this aligns with standard 50/30/20 saving guidelines."
            return f"Compound interest calculation results (compounded {comp_name}): Maturity amount is Rs {res['maturity_amount']:,.2f}, Total interest earned is Rs {res['total_interest']:,.2f}.{advice}"
        else:
            return "Invalid tool_type. Please specify 'emi' or 'compound_interest'."

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str | None = None) -> str:
        """Use this tool to look up a caller in the database.
        It returns information about the caller, such as their name, language preference,
        facts about past interactions, and when they last interacted.

        Args:
            name: The caller's name to search for (optional). If not specified, looks up by participant identity.
        """
        user_id = None
        if self.room:
            participants = list(self.room.remote_participants.values())
            if participants:
                user_id = participants[0].identity

        logger.info(f"Looking up caller. user_id={user_id}, name={name}")
        caller = get_caller_by_id_or_name(user_id=user_id, name=name)
        if caller:
            logger.info(f"Found caller: {caller}")
            lang = caller.get("language_preference", "").lower()
            if "hindi" in lang or "hinglish" in lang:
                self.current_language = "Hindi"
                if self.agent_session:
                    try:
                        self.agent_session.tts.update_options(voice="Anisha")
                        logger.info("Restored database language preference: Anisha")
                    except Exception as e:
                        logger.error(f"Failed to update TTS voice: {e}")
            else:
                self.current_language = "English"
                if self.agent_session:
                    try:
                        self.agent_session.tts.update_options(voice="Anisha")
                        logger.info("Restored database language preference: Anisha")
                    except Exception as e:
                        logger.error(f"Failed to update TTS voice: {e}")
            return f"Caller found: {caller}"

        logger.info("Caller not found")
        return "Caller not found."

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        schemes_checked: str,
        eligibility_answers: str,
    ) -> str:
        """Use this tool to save or update the caller's profile and facts.
        Only call this tool if the user gave explicit verbal consent to remember/save their data.

        Args:
            name: The caller's name.
            language_preference: The language they prefer (e.g. Hindi, English, Hinglish).
            schemes_checked: The schemes checked/discussed (e.g. PMJDY, PMSBY).
            eligibility_answers: Details about eligibility criteria met or discussed.
        """
        user_id = f"voice_assistant_user_{name.lower()}"
        participants = list(self.room.remote_participants.values())
        if participants:
            user_id = participants[0].identity

        facts = {
            "schemes_checked": schemes_checked,
            "eligibility_answers": eligibility_answers,
        }

        logger.info(
            f"Saving caller info. user_id={user_id}, name={name}, language={language_preference}, facts={facts}"
        )
        upsert_caller(user_id, name, language_preference, facts)
        self.call_success = True
        self.success_reason = "SAVE_CALLER_INFO"
        self.failure_reason = None
        return "Caller information saved successfully."

    @function_tool
    async def lookup_stock_market(
        self, context: RunContext, company_or_symbol: str
    ) -> str:
        """Use this tool to look up the real-time share price or stock quote for a company or index.
        It supports popular companies like Reliance, TCS, HDFC Bank, Apple, Google, Tesla, etc., as well as indices like Nifty or Sensex.

        Args:
            company_or_symbol: The name of the company (e.g. 'Reliance', 'TCS', 'Apple') or ticker symbol (e.g. 'RELIANCE.NS', 'AAPL', '^NSEI').
        """
        logger.info(f"Looking up stock market for query: {company_or_symbol}")
        price, ticker, resolved_name, is_fallback = schemes_data.get_stock_quote(
            company_or_symbol
        )

        if price == 0.0:
            return f"Could not find stock quote or fallback price for '{company_or_symbol}'. Please verify the name or ticker."

        status = (
            f"The live price of {resolved_name} ({ticker}) is Rs {price:,.2f} INR."
            if ".NS" in ticker
            or ticker.startswith("^")
            or "INR" in status_helper(ticker)
            else f"The live price of {resolved_name} ({ticker}) is ${price:,.2f} USD."
        )

        if is_fallback:
            status = "Notice: Live connection to stock exchange is offline. " + status

        self.call_success = True
        self.success_reason = "LOOKUP_STOCK_MARKET"
        self.failure_reason = None
        return status

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        reason: str,
        summary: str,
        what_was_checked: str,
        urgency: str,
        language: str,
        preferred_followup: str,
    ) -> str:
        """Use this tool to escalate the caller's issue to a human support representative.
        Only run this tool after explaining the escalation, what is shared, what is excluded, and getting explicit caller consent.

        Args:
            reason: The reason for the escalation (must be either 'possible_fraud' or 'human_decision_required').
            summary: A brief, plain-text summary of the issue. Sensitive details will be filtered out.
            what_was_checked: What steps/information were verified or handled by Dia prior to escalation.
            urgency: Urgency level (LOW, MEDIUM, HIGH, EMERGENCY).
            language: The language preference of the caller (must be exactly 'English' or 'Hindi').
            preferred_followup: Caller's preferred followup channel (e.g. phone, email, sms).
        """
        logger.info("[ESCALATION] Condition detected")
        logger.info("[ESCALATION] Permission received")

        # Validation
        if (
            not reason
            or not summary
            or not what_was_checked
            or not urgency
            or not language
            or not preferred_followup
        ):
            return "Error: All fields are required to submit an escalation request."

        # Clean sensitive information
        def sanitize_sensitive_info(text: str) -> str:
            if not text:
                return text
            # Replace card/account numbers (12-19 digits)
            text = re.sub(r"\b\d{12,19}\b", "Sensitive information excluded.", text)
            # Keywords checks
            keywords = [
                "otp",
                "pin",
                "password",
                "cvv",
                "upi pin",
                "card number",
                "bank account",
                "account number",
                "passcode",
            ]
            for kw in keywords:
                text = re.sub(
                    rf"(?i)({kw}\s*(?:number|code|is|:|value|=|\s)\s*)([a-zA-Z0-9]+)",
                    r"\1Sensitive information excluded.",
                    text,
                )
            # Standalone digits if they resemble OTPs/PINs
            text = re.sub(r"\b\d{4,6}\b", "Sensitive information excluded.", text)
            return text

        clean_summary = sanitize_sensitive_info(summary)
        clean_what_checked = sanitize_sensitive_info(what_was_checked)
        logger.info("[ESCALATION] Sensitive information filtered")

        # Generate Reference ID
        try:
            init_dashboard_db()
            current_year = datetime.now().year
            prefix = f"{getattr(self, 'escalation_prefix', 'FIN')}-{current_year}-"

            conn = sqlite3.connect(DASHBOARD_DB_PATH)
            cursor = conn.cursor()
            while True:
                random_val = random.randint(1, 9999)
                ref_id = f"{prefix}{random_val:04d}"
                cursor.execute(
                    "SELECT 1 FROM escalations WHERE reference_id = ?", (ref_id,)
                )
                if not cursor.fetchone():
                    break
            conn.close()
        except Exception as e:
            logger.error(f"Failed to generate random reference ID: {e}")
            ref_id = f"{getattr(self, 'escalation_prefix', 'FIN')}-{datetime.now().year}-{random.randint(1, 9999):04d}"

        logger.info(f"[ESCALATION] Reference generated: {ref_id}")

        # Save escalation locally to SQLite
        local_saved = False
        try:
            save_local_escalation(
                reference_id=ref_id,
                reason=reason,
                summary=clean_summary,
                what_was_checked=clean_what_checked,
                urgency=urgency,
                language=language,
                preferred_followup=preferred_followup,
                status="OPEN",
            )
            local_saved = True
            logger.info(f"[ESCALATION] Saved locally to database: {ref_id}")
        except Exception as err:
            logger.error(f"[ESCALATION] Failed to save escalation locally: {err}")

        # Send Discord notification
        discord_sent = False
        discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

        if discord_url:
            try:
                discord_payload = {
                    "content": f"🚨 **FINORA AI — HUMAN ESCALATION**\n\n"
                    f"**Reference ID:**\n{ref_id}\n\n"
                    f"**Reason:**\n{reason.replace('_', ' ').title()}\n\n"
                    f"**Summary:**\n{clean_summary}\n\n"
                    f"**What Dia Checked:**\n{clean_what_checked}\n\n"
                    f"**Urgency:**\n{urgency.upper()}\n\n"
                    f"**Language:**\n{language}\n\n"
                    f"**Preferred Follow-up:**\n{preferred_followup.capitalize()}\n\n"
                    f"**Status:**\nOPEN\n\n"
                    f"**Sensitive Information:**\nExcluded"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(discord_url, json=discord_payload) as resp:
                        if resp.status in [200, 204]:
                            discord_sent = True
                            logger.info("[ESCALATION] Discord notification sent")
                            logger.info("[ESCALATION] Status: OPEN")
                        else:
                            resp_text = await resp.text()
                            logger.error(
                                f"[ESCALATION] Discord webhook returned status {resp.status}: {resp_text}"
                            )
            except Exception as e:
                logger.error(f"[ESCALATION] Failed to send Discord notification: {e}")
        else:
            logger.warning("[ESCALATION] Discord Webhook URL is not configured.")

        if discord_sent or local_saved:
            self.call_success = True
            self.success_reason = "ESCALATION_SUCCESS"
            self.failure_reason = None
            return f"Success: Escalation created. Reference ID: {ref_id}. Status: OPEN."
        else:
            self.call_success = False
            self.failure_reason = "ESCALATION_FAILURE"
            return "Error: Could not create escalation request due to database and network failures."
