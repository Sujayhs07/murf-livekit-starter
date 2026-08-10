import json
import logging
import urllib.request
import urllib.error
import time
import math

logger = logging.getLogger("schemes_data")

# Hardcoded fallback exchange rates (updated as of August 2026)
FALLBACK_EXCHANGE_RATES = {
    "USD": 0.012,
    "EUR": 0.011,
    "GBP": 0.0094,
    "AED": 0.044,
    "CAD": 0.016,
    "SGD": 0.016,
    "INR": 1.0
}

# Hardcoded fallback cryptocurrency prices in INR (updated as of August 2026)
FALLBACK_CRYPTO_RATES = {
    "BITCOIN": 5000000.0,
    "ETHEREUM": 250000.0
}

# The comprehensive 14-module financial database
FINANCIAL_DATABASE = {
    "banking": {
        "savings_account": {
            "description": "An interest-bearing deposit account held at a bank or other financial institution. Provides safety and a modest interest rate.",
            "rates": "Typically 2.7% to 4.0% per annum depending on the bank.",
            "eligibility": "All individuals (citizens, residents, minors through guardians) are eligible.",
            "checklist": ["Aadhaar Card", "PAN Card", "Passport size photographs", "Address proof (Electricity bill, Rent agreement)"]
        },
        "current_account": {
            "description": "A deposit account for businesses, liquid transactions, and merchants with no limit on the number of daily transactions.",
            "rates": "Typically 0% interest.",
            "eligibility": "Proprietorships, partnerships, private/public companies, and trusts.",
            "checklist": ["Business Registration Certificate", "PAN Card of the entity", "Partnership Deed / Board Resolution", "Address proof of business"]
        },
        "fd": {
            "description": "Fixed Deposit (FD) is a financial instrument where you invest a lump sum for a fixed tenure at a guaranteed interest rate.",
            "rates": "Typically 6.0% to 7.5% per annum depending on the bank and tenure (senior citizens get 0.5% extra).",
            "eligibility": "All residents, HUFs, and firms.",
            "checklist": ["Aadhaar Card", "PAN Card", "Bank account details"]
        },
        "rd": {
            "description": "Recurring Deposit (RD) allows you to save a fixed amount monthly for a fixed period at a set interest rate.",
            "rates": "Similar to Fixed Deposit rates (typically 6.0% to 7.2%).",
            "eligibility": "All resident individuals and minors through parents/guardians.",
            "checklist": ["Aadhaar Card", "PAN Card", "Initial monthly contribution"]
        },
        "debit_cards": {
            "description": "A card issued by a bank allowing you to access your deposits at ATMs or perform online transactions.",
            "rates": "Annual fees range from Rs 150 to Rs 500 depending on the card type (RuPay classic is often free).",
            "eligibility": "Anyone holding a savings or current account.",
            "checklist": ["Linked savings/current account", "Debit card application form"]
        },
        "atm_mobile_banking": {
            "description": "Automated Teller Machines (ATMs) and internet/mobile banking applications for remote cash withdrawal, balance checks, and money transfers.",
            "rates": "First 3-5 transactions free per month, then Rs 20-21 per withdrawal. Mobile apps are free to use.",
            "eligibility": "All account holders with registered mobile numbers.",
            "checklist": ["Registered mobile number", "Smart phone / internet connection", "Registered debit card for PIN setup"]
        }
    },
    "digital_payments": {
        "upi": {
            "description": "Unified Payments Interface (UPI) is a real-time instant payment system allowing bank-to-bank transfers via mobile numbers or virtual payment addresses.",
            "rates": "Zero transaction fees for consumers.",
            "eligibility": "Any individual with an active Indian bank account and registered mobile number.",
            "checklist": ["Indian bank account", "Active debit card", "Registered mobile SIM in smartphone"]
        },
        "qr_payments": {
            "description": "Quick Response (QR) code payments allow users to make instant bank transfers by scanning a printed or digital merchant QR code using a UPI app.",
            "rates": "Zero transaction fees for consumers.",
            "eligibility": "All UPI-enabled mobile app users.",
            "checklist": ["Smartphone with camera", "UPI application", "Active internet connection"]
        },
        "imps_neft_rtgs": {
            "description": "IMPS is instant 24/7 transfer up to 5 Lakhs. NEFT is batch-based transfer. RTGS is real-time transfer for amounts above 2 Lakhs.",
            "rates": "NEFT/RTGS are online-free. IMPS is Rs 1 to Rs 15 depending on bank.",
            "eligibility": "All retail and corporate netbanking users.",
            "checklist": ["Payee account number", "Payee IFSC code", "Active netbanking / mobile app"]
        },
        "wallets_bill_payments": {
            "description": "Digital wallets (like Paytm, PhonePe) hold cash for micro-transactions, utility bills, and recharges.",
            "rates": "Free wallet creation. Small charges may apply when transferring money from wallet back to bank account.",
            "eligibility": "All smartphone users.",
            "checklist": ["Mobile number", "Basic KYC (Aadhaar or PAN)"]
        }
    },
    "loans_credit": {
        "personal_loan": {
            "description": "An unsecured loan to meet personal expenses like medical bills, travel, or weddings.",
            "rates": "Typically 10.5% to 24.0% per annum based on credit score.",
            "eligibility": "Salaried or self-employed individuals aged 21-60 with a stable income stream.",
            "checklist": ["PAN Card", "Aadhaar Card", "Salary slips (last 3 months)", "Bank statement (last 6 months)"]
        },
        "home_loan": {
            "description": "A secured loan to purchase, construct, or renovate a residential property.",
            "rates": "Typically 8.3% to 9.5% per annum.",
            "eligibility": "Salaried/self-employed individuals aged 18-70 with a solid repayment capacity.",
            "checklist": ["Property ownership documents", "Income proof / ITR (last 2 years)", "Identity proof", "Bank statements"]
        },
        "education_loan": {
            "description": "A loan to cover academic tuition, accommodation, and travel fees for studies in India or abroad.",
            "rates": "Typically 8.5% to 12.0% per annum (interest subsidy available for BPL students).",
            "eligibility": "Indian national students who secured admission to recognized institutions.",
            "checklist": ["Admission letter", "Fee structure details", "Co-applicant income proof", "Academic mark sheets"]
        },
        "credit_score": {
            "description": "A 3-digit number (typically CIBIL, ranging from 300 to 900) representing your creditworthiness.",
            "rates": "Free annual credit report from bureau websites.",
            "eligibility": "Anyone who has taken a loan or used a credit card.",
            "checklist": ["PAN Card details", "Mobile number linked to credit accounts"]
        }
    },
    "investments": {
        "stocks_mutual_funds": {
            "description": "Stocks represent ownership in a company. Mutual Funds pool public money to invest in equity/debt markets.",
            "rates": "No guaranteed returns. Equity mutual funds historically deliver 12% to 15% long term.",
            "eligibility": "Any individual, minor through guardian, or corporate entity.",
            "checklist": ["PAN Card", "Aadhaar Card for e-KYC", "Active bank account", "Demat Account"]
        },
        "sip": {
            "description": "Systematic Investment Plan (SIP) allows you to invest a small fixed sum periodically (monthly/quarterly) in mutual funds.",
            "rates": "Compounded market returns. Minimum investment starts at Rs 100/month.",
            "eligibility": "All citizens with a valid KYC.",
            "checklist": ["KYC verification", "Bank mandate for auto-debit"]
        },
        "bonds_etfs_gsec": {
            "description": "Bonds are debt instruments. ETFs are stock basket securities. G-Secs are government debt securities representing low-risk state borrowings.",
            "rates": "Yields vary (G-Sec rates typically 7.0% to 7.5% per annum).",
            "eligibility": "All resident individuals, firms, and institutions.",
            "checklist": ["Demat account", "Trading portal registration", "PAN Card"]
        }
    },
    "insurance": {
        "life_insurance": {
            "description": "A contract between an insurer and policyholder guaranteeing a sum assured to beneficiaries upon death.",
            "rates": "Premium depends on age and health history.",
            "eligibility": "Aged 18 to 65 years.",
            "checklist": ["Age proof (Birth certificate/10th Board sheet)", "Address proof", "Medical check-up records (for high covers)"]
        },
        "health_insurance": {
            "description": "Covers medical expenses arising from illnesses, accidents, or hospitalization.",
            "rates": "Premium varies by age, pre-existing conditions, and cover size.",
            "eligibility": "All age groups (infants to senior citizens).",
            "checklist": ["Proposal form", "Identity proof", "Previous medical reports (if any)"]
        },
        "motor_insurance": {
            "description": "Third-party motor insurance is legally mandatory in India. First-party covers theft and own damage.",
            "rates": "IRDAI-regulated tariffs for third-party; own-damage varies by car model.",
            "eligibility": "All vehicle owners.",
            "checklist": ["Vehicle Registration Certificate (RC)", "Previous insurance copy (if any)", "Invoice copy"]
        }
    },
    "retirement": {
        "nps": {
            "description": "National Pension System (NPS) is a voluntary, long-term retirement savings scheme designed to provide systematic pensions.",
            "rates": "Market-linked returns, historically 9.0% to 12.0% per annum.",
            "eligibility": "Indian citizens aged 18 to 70 years.",
            "checklist": ["Aadhaar or PAN Card", "Canceled cheque / Bank statement", "Signature upload"]
        },
        "epf": {
            "description": "Employees' Provident Fund (EPF) is a mandatory savings scheme for salaried employees in India.",
            "rates": "Typically 8.1% to 8.25% per annum (notified annually by EPFO).",
            "eligibility": "Salaried employees in establishments with 20+ workers.",
            "checklist": ["Universal Account Number (UAN) registration", "Salary records", "Aadhaar Card linkage"]
        }
    },
    "tax_planning": {
        "income_tax_basics": {
            "description": "The tax levied on individual or business income. India operates under Old and New tax regimes.",
            "rates": "Progressive tax slabs. Income up to Rs 7 Lakhs is tax-free under the New Tax Regime rebate.",
            "eligibility": "Any individual whose annual income exceeds the tax exemption threshold.",
            "checklist": ["Form 16 from employer", "ITR-1/ITR-2 filing form", "Tax payment challans"]
        },
        "tax_saving_investments": {
            "description": "Investments that qualify for deductions under Section 80C, 80D, etc. to reduce taxable income.",
            "rates": "Deduction limits of up to Rs 1.5 Lakhs per year under Section 80C.",
            "eligibility": "Individuals and HUFs under the Old Tax Regime.",
            "checklist": ["ELSS mutual fund statements", "PPF deposit slip", "Premium receipts for life/health insurance"]
        }
    },
    "government_schemes": {
        "pmjdy": {
            "description": "Pradhan Mantri Jan Dhan Yojana (PMJDY) is a national mission for financial inclusion to ensure access to financial services like savings bank accounts.",
            "rates": "Standard savings account interest (approx 3% per annum). Overdraft facility up to Rs 10,000 available.",
            "eligibility": "Any Indian citizen aged 10 years or older who does not have an active bank account.",
            "checklist": ["Aadhaar Card", "Voter ID Card / NREGA Card if Aadhaar is missing", "Two passport size photographs"]
        },
        "pm_kisan": {
            "description": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a central sector scheme providing income support of Rs 6,000 per year in three equal installments to all landholding farmer families.",
            "rates": "Direct benefit transfer of Rs 6,000 per annum (Rs 2,000 every 4 months).",
            "eligibility": "Landholding farmer families (subject to exclusion categories like institutional landholders, taxpayers, etc.).",
            "checklist": ["Land ownership papers (Farad/Jamabandi)", "Aadhaar Card", "Bank account details"]
        },
        "pmjjby": {
            "description": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY) is a one-year life insurance scheme renewable from year to year offering life insurance cover for death due to any reason.",
            "rates": "Premium of Rs 436 per annum. Benefits: Rs 2 Lakh life cover.",
            "eligibility": "Indian citizens aged 18 to 50 years with an active savings bank account who consent to auto-debit.",
            "checklist": ["Aadhaar Card", "Auto-debit consent form", "Active bank account"]
        },
        "pmsby": {
            "description": "Pradhan Mantri Suraksha Bima Yojana (PMSBY) is a one-year accidental insurance scheme renewable from year to year offering coverage for accidental death and disability.",
            "rates": "Premium of Rs 20 per annum. Benefits: Rs 2 Lakh for accidental death/total disability; Rs 1 Lakh for partial disability.",
            "eligibility": "Indian citizens aged 18 to 70 years with an active savings bank account who consent to auto-debit.",
            "checklist": ["Aadhaar Card", "Auto-debit consent form", "Active bank account"]
        },
        "apy": {
            "description": "Atal Pension Yojana (APY) is a pension scheme focused on the unorganized sector workers, guaranteeing a minimum monthly pension.",
            "rates": "Guaranteed minimum monthly pension of Rs 1,000 to Rs 5,000 after age 60 based on contribution tables.",
            "eligibility": "Indian citizens aged 18 to 40 years with a savings bank account. Note: Taxpayers are NOT eligible to join.",
            "checklist": ["Aadhaar Card", "Active savings account", "Mobile number"]
        },
        "ssy": {
            "description": "Sukanya Samriddhi Yojana (SSY) is a girl child prosperity scheme to promote education and marriage savings.",
            "rates": "8.2% per annum (compounded annually, updated for 2026). Interest is tax-free.",
            "eligibility": "Girl child who is an Indian resident under the age of 10. Only two accounts allowed per family.",
            "checklist": ["Birth Certificate of the girl child", "Guardian's Aadhaar Card", "Guardian's PAN Card"]
        },
        "mudra": {
            "description": "Pradhan Mantri MUDRA Yojana (PMMY) provides loans up to Rs 10 Lakhs to non-corporate, non-farm small/micro enterprises under Shishu, Kishor, and Tarun categories.",
            "rates": "Interest rate is market-linked (generally 8.5% to 12.0% per annum). No collateral required.",
            "eligibility": "Non-farm micro-enterprise owner, shopkeeper, artisan, or small manufacturer.",
            "checklist": ["Mudra Application Form", "Business identity and address proof", "Quotation of machinery/assets to purchase", "Income proof"]
        }
    },
    "business_finance": {
        "business_loan": {
            "description": "Unsecured or secured funding to expand business operations, buy equipment, or finance working capital.",
            "rates": "Ranges from 11.0% to 22.0% based on business turnover and vintage.",
            "eligibility": "Businesses operating for at least 2 years with profitable balance sheets.",
            "checklist": ["ITR filings (last 2 years)", "GST returns (last 12 months)", "Bank statements", "Business proof"]
        },
        "working_capital": {
            "description": "Overdraft, cash credit, or short-term loans to manage day-to-day business operational expenses.",
            "rates": "Typically interest is charged on utilized balance (approx 9.0% to 14.0%).",
            "eligibility": "Registered businesses, manufacturers, and traders.",
            "checklist": ["Stock and book debt statements", "Audited balance sheets", "GST details"]
        }
    },
    "international_finance": {
        "forex_remittances": {
            "description": "Foreign Exchange services, international outward transfers, inward remittances, and payment of overseas fees.",
            "rates": "Requires checking live exchange rates. Tax Collected at Source (TCS) of 5% or 20% applies to outward remittances under LRS exceeding Rs 7 Lakhs.",
            "eligibility": "All residents and non-residents with KYC-compliant accounts.",
            "checklist": ["Form A2 (for outward remittance)", "PAN Card copy", "Beneficiary bank account details and SWIFT code"]
        }
    },
    "financial_security": {
        "kyc_safety": {
            "description": "Know Your Customer (KYC) details must be protected. Never share original documents on unverified portals. Regular re-KYC can be done via bank portals.",
            "rates": "Free compliance service. Banks never charge for KYC updates.",
            "eligibility": "All account and wallet holders.",
            "checklist": ["Aadhaar online XML/e-Aadhaar", "PAN Card verification"]
        },
        "otp_fraud_safety": {
            "description": "One-Time Passwords (OTPs) and UPI PINs are for authorization. Bank personnel will NEVER ask for your OTP or PIN. Sharing them grants full access to transfer your funds.",
            "rates": "N/A",
            "eligibility": "All citizens using digital finance.",
            "checklist": ["Do not share PINs/OTPs", "Report suspicious calls to cybercrime portal"]
        },
        "reporting_fraud": {
            "description": "In case of online financial fraud, block your accounts immediately and report to the cybercrime authorities within 24 hours.",
            "rates": "Toll-free national cyber helpline 1930.",
            "eligibility": "Any victim of online financial crime.",
            "checklist": ["Transaction screenshot", "Bank statement copy", "Phishing SMS/email headers"]
        }
    },
    "financial_planning": {
        "budgeting_saving": {
            "description": "Managing your income. A recommended practice is the 50/30/20 rule: 50% for Needs (rent, food), 30% for Wants (hobbies, dining), and 20% for Savings/Debt repayment.",
            "rates": "N/A",
            "eligibility": "All income earners.",
            "checklist": ["Monthly income tracking sheet", "Goal list for saving"]
        }
    },
    "consumer_banking_help": {
        "failed_transactions": {
            "description": "Under RBI guidelines, if a transaction fails but money is debited, the bank must auto-refund the money within T+1 to T+5 days, else pay Rs 100/day penalty.",
            "rates": "N/A",
            "eligibility": "All card, UPI, and ATM transaction users.",
            "checklist": ["Transaction Reference Number (RRN)", "Bank account statement", "Complaint ticket details"]
        },
        "card_blocking": {
            "description": "If your debit/credit card is lost, blocked, or stolen, block it immediately via SMS, netbanking, or bank customer care to prevent unauthorized transactions.",
            "rates": "Free card blocking service.",
            "eligibility": "All active cardholders.",
            "checklist": ["Card number / linked mobile number", "Bank customer care helpline"]
        }
    }
}


def get_exchange_rate(target_currency: str) -> tuple[float, str, bool]:
    """
    Fetches real-time exchange rate for target_currency relative to INR.
    Returns (rate, timestamp_str, is_fallback_used).
    """
    target = target_currency.upper()
    if target == "INR":
        return 1.0, "real-time", False

    url = "https://open.er-api.com/v6/latest/INR"
    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DiaFinanceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                data = json.loads(response.read().decode())
                rates = data.get("rates", {})
                rate = rates.get(target)
                if rate:
                    last_update = data.get("time_last_update_utc", "today")
                    logger.info(f"Successfully fetched exchange rate for {target}: {rate}")
                    return rate, last_update, False
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to fetch exchange rates: {e}")
            if attempt < retries - 1:
                time.sleep(0.5)

    # Fallback path if all retries fail
    logger.error("All exchange rate retries failed. Using local fallback.")
    rate = FALLBACK_EXCHANGE_RATES.get(target, 0.012)
    return rate, "Local cached backup (updated August 2026)", True


def get_crypto_rate(crypto_id: str) -> tuple[float, str, bool]:
    """
    Fetches real-time cryptocurrency rates in INR from CoinGecko.
    Returns (price_in_inr, timestamp_str, is_fallback_used).
    """
    cid = crypto_id.lower()
    if cid not in ["bitcoin", "ethereum"]:
        return 0.0, "unknown", True

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=inr"
    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DiaFinanceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                data = json.loads(response.read().decode())
                price = data.get(cid, {}).get("inr")
                if price:
                    return price, "today's live price", False
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to fetch crypto rates: {e}")
            if attempt < retries - 1:
                time.sleep(0.5)

    # Fallback path if all retries fail
    logger.error("All crypto rate retries failed. Using local fallback.")
    price = FALLBACK_CRYPTO_RATES.get(cid.upper(), 0.0)
    return price, "Local cached backup (updated August 2026)", True


def calculate_loan_emi(principal: float, annual_rate: float, tenure_years: int) -> dict:
    """
    Calculates Equated Monthly Installment (EMI).
    """
    monthly_rate = (annual_rate / 12) / 100
    tenure_months = tenure_years * 12
    if monthly_rate == 0:
        emi = principal / tenure_months
    else:
        emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)) / (
            math.pow(1 + monthly_rate, tenure_months) - 1
        )
    total_payment = emi * tenure_months
    total_interest = total_payment - principal

    return {
        "monthly_emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2)
    }


def calculate_compound_interest(principal: float, annual_rate: float, tenure_years: int, times_compounded: int = 1) -> dict:
    """
    Calculates compounding interest returns.
    """
    rate_fraction = annual_rate / 100
    total_amount = principal * math.pow(1 + (rate_fraction / times_compounded), times_compounded * tenure_years)
    total_interest = total_amount - principal

    return {
        "maturity_amount": round(total_amount, 2),
        "total_interest": round(total_interest, 2)
    }


# Mappings for popular Indian and US stocks and major indices
COMPANY_TICKER_MAP = {
    # Indian Stocks (NSE)
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "tata consultancy services": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "state bank of india": "SBIN.NS",
    "sbin": "SBIN.NS",
    "wipro": "WIPRO.NS",
    "tata motors": "TATAMOTORS.NS",
    "itc": "ITC.NS",
    "bharti airtel": "BHARTIARTL.NS",
    "airtel": "BHARTIARTL.NS",
    "l&t": "LT.NS",
    "larsen & toubro": "LT.NS",
    "adani": "ADANIENT.NS",
    "adani enterprises": "ADANIENT.NS",
    
    # US Stocks
    "apple": "AAPL",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    
    # Indices
    "nifty": "^NSEI",
    "nifty 50": "^NSEI",
    "nifty50": "^NSEI",
    "sensex": "^BSESN",
    "sp500": "^GSPC",
    "s&p 500": "^GSPC",
    "nasdaq": "^IXIC",
    "nasdaq 100": "^NDX"
}

FALLBACK_STOCK_RATES = {
    "RELIANCE.NS": 1325.40,
    "TCS.NS": 4200.50,
    "INFY.NS": 1850.20,
    "HDFCBANK.NS": 1650.00,
    "ICICIBANK.NS": 1150.30,
    "SBIN.NS": 850.75,
    "WIPRO.NS": 510.40,
    "TATAMOTORS.NS": 980.20,
    "ITC.NS": 490.10,
    "BHARTIARTL.NS": 1420.60,
    "LT.NS": 3600.00,
    "ADANIENT.NS": 3100.00,
    "AAPL": 220.50,
    "GOOGL": 170.80,
    "MSFT": 420.25,
    "TSLA": 200.10,
    "NVDA": 115.40,
    "AMZN": 180.30,
    "META": 490.80,
    "NFLX": 640.50,
    "^NSEI": 24200.00,
    "^BSESN": 79500.00,
    "^GSPC": 5350.00,
    "^IXIC": 16800.00,
    "^NDX": 18900.00
}


def get_stock_quote(query_symbol: str) -> tuple[float, str, str, bool]:
    """
    Resolves a company name or ticker to its Yahoo Finance ticker, and fetches its live price.
    Returns (price, symbol, resolved_name, is_fallback_used).
    """
    clean_query = query_symbol.lower().strip()
    
    # Check mapping
    symbol = COMPANY_TICKER_MAP.get(clean_query)
    resolved_name = query_symbol
    if symbol:
        resolved_name = query_symbol.title()
    else:
        # Default to clean uppercase query if it looks like a symbol
        symbol = query_symbol.upper().strip()
        resolved_name = symbol
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                data = json.loads(response.read().decode())
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                if price is not None:
                    return float(price), symbol, resolved_name, False
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to fetch stock rate for {symbol}: {e}")
            if attempt < retries - 1:
                time.sleep(0.5)
                
    # Fallback path if all retries fail
    logger.error(f"All stock rate retries failed for {symbol}. Using local fallback.")
    price = FALLBACK_STOCK_RATES.get(symbol, 0.0)
    return price, symbol, resolved_name, True

