import asyncio
import logging
import sys
import io

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError with Devanagari (Hindi) text
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import SYSTEM_PROMPT
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.prompt import SYSTEM_PROMPT

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


class Assistant(Agent):
    def __init__(self, room: rtc.Room | None = None, session: AgentSession | None = None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.room = room
        self.agent_session = session

    @function_tool
    async def lookup_financial_service(
        self,
        context: RunContext,
        module_name: str,
        service_name: str,
        target_currency: str = "INR"
    ) -> str:
        """Use this tool to look up detailed information on any financial service, investment, banking help, security guidelines, or government scheme.
        It returns descriptions, eligibility rules, interest rates, charges, and document checklists.
        It supports live exchange rate conversions or live cryptocurrency rate check if requested.

        Args:
            module_name: The name of the category (e.g. banking, digital_payments, loans_credit, investments, insurance, retirement, tax_planning, government_schemes, business_finance, international_finance, financial_security, financial_planning, consumer_banking_help).
            service_name: The name of the specific service (e.g. savings_account, current_account, fd, rd, debit_cards, atm_mobile_banking, upi, qr_payments, imps_neft_rtgs, wallets_bill_payments, personal_loan, home_loan, education_loan, credit_score, stocks_mutual_funds, sip, bonds_etfs_gsec, bitcoin, ethereum, life_insurance, health_insurance, motor_insurance, nps, epf, income_tax_basics, tax_saving_investments, pmjdy, pm_kisan, pmjjby, pmsby, apy, ssy, mudra, business_loan, working_capital, forex_remittances, kyc_safety, otp_fraud_safety, reporting_fraud, budgeting_saving, failed_transactions, card_blocking).
            target_currency: The currency to display money values in (e.g. INR, USD, EUR, GBP). Defaults to INR.
        """
        logger.info(f"Looking up financial service. module={module_name}, service={service_name}, currency={target_currency}")
        
        module = module_name.lower().strip()
        service = service_name.lower().strip()

        # Handle live crypto rate queries under investments category
        if module == "investments" and service in ["bitcoin", "ethereum"]:
            price, timestamp, is_fallback = schemes_data.get_crypto_rate(service)
            source_msg = f"As of {timestamp}" if not is_fallback else f"Notice: {timestamp}"
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
            source_msg = f"As of today's live rate ({timestamp})" if not is_fallback else f"Notice: Using offline backup rate ({timestamp})"
            
            # Simple heuristic parser to identify rupees in rates text and convert them
            # e.g. "Rs 20 per annum" or "Rs 2 Lakh" or "Rs 10,000" or "Rs 6,000"
            # Let's extract numbers and convert them
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
        monthly_income: float | None = None
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
        logger.info(f"Running financial calculator. type={tool_type}, principal={principal}, rate={interest_rate}, tenure={tenure_years}, monthly_income={monthly_income}")
        ttype = tool_type.lower().strip()
        if ttype == "emi":
            res = schemes_data.calculate_loan_emi(principal, interest_rate, tenure_years)
            emi = res['monthly_emi']
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
            res = schemes_data.calculate_compound_interest(principal, interest_rate, tenure_years, times_compounded)
            comp_name = {1: "annually", 2: "semi-annually", 4: "quarterly", 12: "monthly"}.get(times_compounded, f"{times_compounded} times a year")
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
            # Restore user's language voice setting
            if self.agent_session:
                lang = caller.get("language_preference", "").lower()
                if "hindi" in lang or "hinglish" in lang:
                    try:
                        self.agent_session.tts.update_options(voice="hi-IN-anisha")
                        logger.info("Restored database language preference: hi-IN-anisha (Hindi/Hinglish)")
                    except Exception as e:
                        logger.error(f"Failed to update TTS voice: {e}")
                else:
                    try:
                        self.agent_session.tts.update_options(voice="en-IN-anisha")
                        logger.info("Restored database language preference: en-IN-anisha (English)")
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
        return "Caller information saved successfully."

    @function_tool
    async def lookup_stock_market(
        self,
        context: RunContext,
        company_or_symbol: str
    ) -> str:
        """Use this tool to look up the real-time share price or stock quote for a company or index.
        It supports popular companies like Reliance, TCS, HDFC Bank, Apple, Google, Tesla, etc., as well as indices like Nifty or Sensex.

        Args:
            company_or_symbol: The name of the company (e.g. 'Reliance', 'TCS', 'Apple') or ticker symbol (e.g. 'RELIANCE.NS', 'AAPL', '^NSEI').
        """
        logger.info(f"Looking up stock market for query: {company_or_symbol}")
        price, ticker, resolved_name, is_fallback = schemes_data.get_stock_quote(company_or_symbol)
        
        if price == 0.0:
            return f"Could not find stock quote or fallback price for '{company_or_symbol}'. Please verify the name or ticker."
            
        status = f"The live price of {resolved_name} ({ticker}) is Rs {price:,.2f} INR." if ".NS" in ticker or ticker.startswith("^") or "INR" in status_helper(ticker) else f"The live price of {resolved_name} ({ticker}) is ${price:,.2f} USD."
        
        if is_fallback:
            status = "Notice: Live connection to stock exchange is offline. " + status
            
        return status

def status_helper(ticker: str) -> str:
    return "INR" if ticker.endswith(".NS") or ticker in ["^NSEI", "^BSESN"] else "USD"



server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    import json
    is_outbound = False
    recipient_name = "User"
    call_type = "scheme_deadline"
    custom_message = ""
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
            is_outbound = metadata.get("is_outbound", False)
            recipient_name = metadata.get("recipient_name", "User")
            call_type = metadata.get("call_type", "scheme_deadline")
            custom_message = metadata.get("custom_message", "")
            logger.info(f"Loaded job metadata: is_outbound={is_outbound}, recipient_name={recipient_name}, call_type={call_type}, custom_message={custom_message}")
        except Exception as e:
            logger.error(f"Failed to parse job metadata: {e}")
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-2", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="en-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=3),
            text_pacing=True,
        ),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.0,
        min_interruption_duration=0.2,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for stop request
        stop_keywords = ["stop the call", "stop calling", "opt out", "stop", "cancel", "stop this call"]
        if any(keyword in transcript for keyword in stop_keywords):
            logger.info("User requested to stop/opt-out. Say goodbye and disconnect.")
            async def end_call():
                try:
                    await session.say("Understood. I will end the call now and update your preferences. Goodbye.")
                    await asyncio.sleep(4.0)
                except Exception as e:
                    logger.error(f"Error during shutdown message: {e}")
                await ctx.room.disconnect()
            asyncio.create_task(end_call())
            return

        # Check for Devanagari script characters (native Hindi)
        has_devanagari = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in transcript)

        # Check for common Hinglish/Hindi romanized keywords
        hindi_keywords = {
            "kya",
            "hai",
            "aur",
            "main",
            "haan",
            "nahin",
            "aap",
            "namaste",
            "shukriya",
            "yojana",
            "batao",
            "bataiye",
            "samjhao",
            "dhan",
            "suraksha",
            "bima",
            "pension",
            "mein",
            "ke",
            "ki",
            "se",
            "ko",
            "ka",
            "jo",
            "toh",
            "bhi",
            "ho",
            "kar",
            "raha",
            "rahi",
            "rha",
            "rhi",
            "mujhe",
            "mera",
            "meri",
            "hum",
            "tum",
            "apna",
            "apni",
            "karke",
            "karo",
            "karna",
            "tha",
            "thi",
            "the",
            "ab",
            "kab",
            "tab",
            "sab",
        }
        words = set(transcript.split())
        has_hindi_words = not words.isdisjoint(hindi_keywords)

        # Helper to safely update TTS voice
        def _set_tts_voice(voice_id: str) -> None:
            try:
                session.tts.update_options(voice=voice_id)
                logger.info(f"TTS voice switched to {voice_id}")
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Failed to set TTS voice to {voice_id}: {e}")

        if has_devanagari or has_hindi_words:
            logger.info(
                f"Detected Hindi/Hinglish speech: '{ev.transcript}'. Switching TTS to Hindi voice."
            )
            _set_tts_voice("hi-IN-anisha")
        else:
            logger.info(
                f"Detected English speech: '{ev.transcript}'. Switching TTS to English voice."
            )
            _set_tts_voice("en-IN-anisha")

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    logger.info("Initializing AgentSession with voice pipeline")
    try:
        await session.start(
            agent=Assistant(room=ctx.room, session=session),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(),
            ),
        )
        logger.info("AgentSession started successfully")
    except Exception as e:
        logger.error(f"Failed to start AgentSession: {e}")
        raise

    # Join the room and connect to the user
    await ctx.connect()

    # Automatically speak initial greeting
    async def greet_user_on_entry():
        try:
            if is_outbound:
                # Wait for any remote participant to connect/join the room
                logger.info("Outbound call: waiting for participant to join...")
                
                connected_event = asyncio.Event()
                
                @ctx.room.on("participant_connected")
                def on_participant_connected(participant: rtc.RemoteParticipant):
                    logger.info(f"Participant connected event received for: {participant.identity}")
                    connected_event.set()
                
                # Check if participant is already present
                if len(ctx.room.remote_participants) > 0:
                    logger.info("Participant already present in room.")
                    connected_event.set()
                
                try:
                    await asyncio.wait_for(connected_event.wait(), timeout=45.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for participant to join.")
                    return
                
                logger.info("Participant joined, speaking greeting.")
                await asyncio.sleep(2.0) # Brief delay to let the user put the phone to their ear
                
                session.tts.update_options(voice="en-IN-anisha")
                if custom_message:
                    session.say(custom_message)
                elif call_type == "payment_reminder":
                    session.say(
                        "Namaste! This is Dia calling from Bharat Finance Services. We are calling to remind you that your monthly loan EMI payment is due in three days. "
                        "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                    )
                elif call_type == "itr_deadline":
                    session.say(
                        "Namaste! This is Dia calling from the National Financial Literacy Council of India. We are calling to remind you that the deadline for filing your Income Tax Return is approaching on July thirty-first. "
                        "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                    )
                else: # default scheme_deadline
                    session.say(
                        "Namaste! This is Dia calling from the National Financial Literacy Council of India regarding the approaching deadline for the PM-Kisan scheme. "
                        "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                    )
                logger.info(f"Spoke outbound welcome greeting for {call_type} on entry")
            else:
                await asyncio.sleep(1.0)
                session.tts.update_options(voice="hi-IN-anisha")
                session.say("नमस्ते! मैं दीया हूँ। मुझे अपनी फाइनेंशियल दोस्त समझिए। मैं सरकारी फाइनेंशियल स्कीम्स और सेफ बैंकिंग से जुड़े सवालों में आपकी मदद करने के लिए यहाँ हूँ। बताइए, आज मैं आपकी कैसे मदद कर सकती हूँ? क्या मैं आपका शुभ नाम जान सकती हूँ?")
                logger.info("Spoke inbound welcome greeting to user on entry")
        except Exception as err:
            logger.error(f"Failed to speak welcome greeting: {err}")

    asyncio.create_task(greet_user_on_entry())


if __name__ == "__main__":
    cli.run_app(server)
