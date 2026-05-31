import pytest
from datetime import datetime
from simulator.simulator import (
    generate_id,
    generate_ip,
    generate_amount,
    random_timestamp,
    generate_card_profiles,
    generate_normal_transaction,
    generate_amount_fraud_transaction,
    generate_geo_fraud_transaction,
    generate_merchant_fraud_transaction,
    generate_velocity_fraud_transactions,
    generate_transactions,
    MERCHANT_CATEGORIES,
    CITIES,
)

START = datetime(2026, 1, 1)
END = datetime(2026, 1, 7)


# -----------------------
# UTILITY FUNCTIONS
# -----------------------

def test_generate_id_format():
    assert generate_id("txn", 1) == "txn_0001"
    assert generate_id("card", 99) == "card_0099"
    assert generate_id("merchant", 0) == "merchant_0000"

def test_generate_ip_format():
    ip = generate_ip()
    parts = ip.split(".")
    assert len(parts) == 4
    assert all(1 <= int(p) <= 255 for p in parts)

def test_generate_amount_always_positive():
    for _ in range(100):
        amount = generate_amount(50.0, 20.0)
        assert amount >= 1.0

def test_generate_amount_rounded():
    for _ in range(100):
        amount = generate_amount(50.0, 20.0)
        assert round(amount, 2) == amount

def test_random_timestamp_in_range():
    for _ in range(50):
        ts = random_timestamp(START, END)
        assert START <= ts <= END


# -----------------------
# CARD PROFILES
# -----------------------

def test_generate_card_profiles_count():
    profiles = generate_card_profiles(10)
    assert len(profiles) == 10

def test_card_profile_fields():
    profiles = generate_card_profiles(5)
    required_fields = [
        "card_id", "cardholder_id", "home_city", "home_state",
        "home_country", "home_latitude", "home_longitude",
        "usual_categories", "avg_amount", "amount_stddev",
        "usual_channel", "active_hour_start", "active_hour_end",
        "device_id", "ip_region",
    ]
    for profile in profiles:
        for field in required_fields:
            assert field in profile, f"Missing field: {field}"

def test_card_profile_usual_categories_valid():
    profiles = generate_card_profiles(10)
    for profile in profiles:
        assert 2 <= len(profile["usual_categories"]) <= 4
        for cat in profile["usual_categories"]:
            assert cat in MERCHANT_CATEGORIES

def test_card_profile_ids_unique():
    profiles = generate_card_profiles(10)
    card_ids = [p["card_id"] for p in profiles]
    assert len(card_ids) == len(set(card_ids))

def test_card_profile_home_city_valid():
    profiles = generate_card_profiles(10)
    valid_cities = [c["city"] for c in CITIES]
    for profile in profiles:
        assert profile["home_city"] in valid_cities


# -----------------------
# NORMAL TRANSACTIONS
# -----------------------

def test_normal_transaction_is_not_fraud():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    txn = generate_normal_transaction(profile, START, END, 0)
    assert txn["is_fraud_ground_truth"] == 0
    assert txn["fraud_type"] == "none"

def test_normal_transaction_fields():
    profiles = generate_card_profiles(5)
    txn = generate_normal_transaction(profiles[0], START, END, 0)
    required = [
        "transaction_id", "event_ts", "card_id", "cardholder_id",
        "merchant_id", "merchant_category", "amount", "currency",
        "channel", "txn_type", "city", "state", "country",
        "latitude", "longitude", "device_id", "ip_address",
        "is_fraud_ground_truth", "fraud_type",
    ]
    for field in required:
        assert field in txn, f"Missing field: {field}"

def test_normal_transaction_category_from_profile():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    for _ in range(20):
        txn = generate_normal_transaction(profile, START, END, 0)
        assert txn["merchant_category"] in profile["usual_categories"]


# -----------------------
# FRAUD TRANSACTIONS
# -----------------------

def test_amount_fraud_is_flagged():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    txn = generate_amount_fraud_transaction(profile, START, END, 0)
    assert txn["is_fraud_ground_truth"] == 1
    assert txn["fraud_type"] == "amount"

def test_amount_fraud_is_large():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    for _ in range(20):
        txn = generate_amount_fraud_transaction(profile, START, END, 0)
        assert txn["amount"] >= profile["avg_amount"] * 5

def test_geo_fraud_is_flagged():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    txn = generate_geo_fraud_transaction(profile, START, END, 0)
    assert txn["is_fraud_ground_truth"] == 1
    assert txn["fraud_type"] == "geo"

def test_geo_fraud_city_differs_from_home():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    for _ in range(20):
        txn = generate_geo_fraud_transaction(profile, START, END, 0)
        assert txn["city"] != profile["home_city"]

def test_merchant_fraud_is_flagged():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    txn = generate_merchant_fraud_transaction(profile, START, END, 0)
    assert txn["is_fraud_ground_truth"] == 1
    assert txn["fraud_type"] == "merchant"

def test_merchant_fraud_category_not_in_profile():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    for _ in range(20):
        txn = generate_merchant_fraud_transaction(profile, START, END, 0)
        assert txn["merchant_category"] not in profile["usual_categories"]

def test_velocity_fraud_is_flagged():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    burst = generate_velocity_fraud_transactions(profile, START, END, 0)
    for txn in burst:
        assert txn["is_fraud_ground_truth"] == 1
        assert txn["fraud_type"] == "velocity"

def test_velocity_fraud_burst_size():
    profiles = generate_card_profiles(5)
    profile = profiles[0]
    for _ in range(20):
        burst = generate_velocity_fraud_transactions(profile, START, END, 0)
        assert 3 <= len(burst) <= 5


# -----------------------
# GENERATE TRANSACTIONS
# -----------------------

def test_generate_transactions_total_count():
    profiles = generate_card_profiles(10)
    transactions = generate_transactions(profiles, 100, 0.0, START, END)
    assert len(transactions) == 100

def test_generate_transactions_no_fraud_when_zero_rate():
    profiles = generate_card_profiles(10)
    transactions = generate_transactions(profiles, 100, 0.0, START, END)
    assert all(t["is_fraud_ground_truth"] == 0 for t in transactions)

def test_generate_transactions_all_fraud_types_present():
    profiles = generate_card_profiles(10)
    transactions = generate_transactions(profiles, 1000, 0.08, START, END)
    fraud_types = {t["fraud_type"] for t in transactions}
    assert "amount" in fraud_types
    assert "geo" in fraud_types
    assert "merchant" in fraud_types
    assert "velocity" in fraud_types

def test_generate_transactions_unique_ids():
    profiles = generate_card_profiles(10)
    transactions = generate_transactions(profiles, 200, 0.0, START, END)
    ids = [t["transaction_id"] for t in transactions]
    assert len(ids) == len(set(ids))