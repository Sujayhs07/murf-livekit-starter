import pytest
import sys
import os

# Adjust path to find src/schemes_data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import schemes_data


def test_calculate_loan_emi():
    # Principal: 5,00,000 (5 Lakhs), Rate: 8.5%, Tenure: 15 years
    res = schemes_data.calculate_loan_emi(500000, 8.5, 15)
    assert res["monthly_emi"] > 0
    assert res["total_payment"] > 500000
    assert res["total_interest"] > 0
    
    # Verify exact math (approx EMI should be 4923.63 for 5L, 8.5%, 15 years)
    assert abs(res["monthly_emi"] - 4923.63) < 5.0  # Allow slight rounding deviations


def test_calculate_compound_interest():
    # Principal: 10,000, Rate: 8.2% (compounded quarterly), Tenure: 5 years
    res = schemes_data.calculate_compound_interest(10000, 8.2, 5, times_compounded=4)
    assert res["maturity_amount"] > 10000
    assert res["total_interest"] > 0
    assert res["maturity_amount"] == 10000 + res["total_interest"]


def test_get_exchange_rate():
    # INR rate is always 1.0
    rate, timestamp, is_fallback = schemes_data.get_exchange_rate("INR")
    assert rate == 1.0
    assert not is_fallback
    assert timestamp == "real-time"

    # Fetch live or fallback USD rate
    usd_rate, usd_ts, usd_fb = schemes_data.get_exchange_rate("USD")
    assert usd_rate > 0
    assert usd_ts != ""


def test_get_crypto_rate():
    # Test valid cryptos
    btc_price, btc_ts, btc_fb = schemes_data.get_crypto_rate("bitcoin")
    assert btc_price > 0
    assert btc_ts != ""

    eth_price, eth_ts, eth_fb = schemes_data.get_crypto_rate("ethereum")
    assert eth_price > 0
    assert eth_ts != ""

    # Test invalid cryptos
    invalid_price, _, invalid_fb = schemes_data.get_crypto_rate("dogecoin")
    assert invalid_price == 0.0
    assert invalid_fb


def test_financial_database_structure():
    # Check that PMJDY, PMSBY, APY are present
    assert "government_schemes" in schemes_data.FINANCIAL_DATABASE
    schemes = schemes_data.FINANCIAL_DATABASE["government_schemes"]
    assert "pmjdy" in schemes
    assert "pmsby" in schemes
    assert "pmjjby" in schemes
    assert "apy" in schemes
    assert "ssy" in schemes

    pmjdy_info = schemes["pmjdy"]
    assert "description" in pmjdy_info
    assert "rates" in pmjdy_info
    assert "eligibility" in pmjdy_info
    assert "checklist" in pmjdy_info


@pytest.mark.asyncio
async def test_assistant_calculate_financials():
    from agent import Assistant
    # Test Assistant calculate_financials with and without monthly_income
    assistant = Assistant(room=None)
    
    # 1. Test EMI calculation without income
    res_no_inc = await assistant.calculate_financials(
        context=None,
        tool_type="emi",
        principal=100000,
        interest_rate=10,
        tenure_years=1
    )
    assert "EMI calculation results" in res_no_inc
    assert "Please provide your monthly income" in res_no_inc

    # 2. Test EMI calculation with safe income (EMI < 40%)
    res_safe = await assistant.calculate_financials(
        context=None,
        tool_type="emi",
        principal=100000,
        interest_rate=10,
        tenure_years=1,
        monthly_income=30000
    )
    assert "Good news" in res_safe

    # 3. Test EMI calculation with risky income (EMI > 40%)
    res_risky = await assistant.calculate_financials(
        context=None,
        tool_type="emi",
        principal=100000,
        interest_rate=10,
        tenure_years=1,
        monthly_income=10000
    )
    assert "Warning" in res_risky

    # 4. Test compound interest without income
    res_ci_no_inc = await assistant.calculate_financials(
        context=None,
        tool_type="compound_interest",
        principal=50000,
        interest_rate=8,
        tenure_years=5
    )
    assert "Maturity amount" in res_ci_no_inc
    assert "Please provide your monthly income" in res_ci_no_inc

    # 5. Test compound interest with income
    res_ci_inc = await assistant.calculate_financials(
        context=None,
        tool_type="compound_interest",
        principal=50000,
        interest_rate=8,
        tenure_years=5,
        monthly_income=20000
    )
    assert "50/30/20 rule" in res_ci_inc


def test_get_stock_quote():
    # Test valid ticker and mapped name
    price, ticker, resolved_name, is_fallback = schemes_data.get_stock_quote("reliance")
    assert price > 0
    assert ticker == "RELIANCE.NS"
    assert resolved_name == "Reliance"
    
    # Test invalid ticker fallback
    price, ticker, resolved_name, is_fallback = schemes_data.get_stock_quote("INVALID_TICKER")
    assert price == 0.0
    assert is_fallback


@pytest.mark.asyncio
async def test_assistant_lookup_stock_market():
    from agent import Assistant
    assistant = Assistant(room=None)
    
    # Test valid stock query
    res = await assistant.lookup_stock_market(context=None, company_or_symbol="reliance")
    assert "RELIANCE.NS" in res
    assert "Rs " in res


def test_upsert_caller_facts_merging():
    import db
    import uuid
    # Create unique name to prevent collisions
    test_name = f"TestUser_{uuid.uuid4().hex[:6]}"
    user_id = f"test_id_{test_name}"
    
    # 1. First interaction
    facts1 = {
        "schemes_checked": "PMJDY",
        "eligibility_answers": "Meets age limit"
    }
    db.upsert_caller(user_id, test_name, "Hindi", facts1)
    
    caller1 = db.get_caller_by_id_or_name(user_id=user_id)
    assert caller1 is not None
    assert caller1["facts"]["schemes_checked"] == "PMJDY"
    assert caller1["facts"]["eligibility_answers"] == "Meets age limit"
    assert caller1["language_preference"] == "Hindi"
    
    # 2. Second interaction - should merge schemes and eligibility answers
    facts2 = {
        "schemes_checked": "PMSBY, PMJDY",
        "eligibility_answers": "Meets income criteria"
    }
    db.upsert_caller(user_id, test_name, "Hinglish", facts2)
    
    caller2 = db.get_caller_by_id_or_name(user_id=user_id)
    assert caller2 is not None
    assert "PMJDY" in caller2["facts"]["schemes_checked"]
    assert "PMSBY" in caller2["facts"]["schemes_checked"]
    assert "Meets age limit" in caller2["facts"]["eligibility_answers"]
    assert "Meets income criteria" in caller2["facts"]["eligibility_answers"]
    assert caller2["language_preference"] == "Hinglish"



