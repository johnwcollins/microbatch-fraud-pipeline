import random
from datetime import datetime, timedelta
import pandas as pd

# -----------------------
# CONSTANTS
# -----------------------

MERCHANT_CATEGORIES = [
    "grocery",
    "gas",
    "restaurant",
    "travel",
    "electronics",
    "pharmacy",
    "retail",
    "entertainment",
]

CHANNELS = [
    "card_present",
    "online",
    "mobile_wallet",
]

TXN_TYPES = [
    "purchase",
    "refund",
    "cash_withdrawal",
]

CURRENCY = "USD"

CITIES = [
    {"city": "San Diego", "state": "CA", "country": "US", "lat": 32.7157, "lon": -117.1611},
    {"city": "Los Angeles", "state": "CA", "country": "US", "lat": 34.0522, "lon": -118.2437},
    {"city": "Phoenix", "state": "AZ", "country": "US", "lat": 33.4484, "lon": -112.0740},
    {"city": "Dallas", "state": "TX", "country": "US", "lat": 32.7767, "lon": -96.7970},
    {"city": "Miami", "state": "FL", "country": "US", "lat": 25.7617, "lon": -80.1918},
    {"city": "Seattle", "state": "WA", "country": "US", "lat": 47.6062, "lon": -122.3321},
]

FRAUD_TYPES = [
    "none",
    "velocity",
    "geo",
    "merchant",
    "amount",
]

def random_choice(lst):
    return random.choice(lst)

def random_timestamp(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)

def generate_amount(avg: float, stddev: float) -> float:
    amount = random.gauss(avg, stddev)
    return round(max(1.0, amount), 2)

def generate_id(prefix: str, num: int) -> str:
    return f"{prefix}_{num:04d}"

def generate_ip() -> str:
    return ".".join(str(random.randint(1, 255)) for _ in range(4))

def generate_card_profiles(num_cardholders: int) -> list[dict]:
    profiles = []

    for i in range(num_cardholders):
        card_id = generate_id("card", i)
        cardholder_id = generate_id("user", i)

        city_info = random_choice(CITIES)

        num_categories = random.randint(2, 4)
        usual_categories = random.sample(MERCHANT_CATEGORIES, num_categories)

        avg_amount = random.uniform(20, 150)
        amount_stddev = avg_amount * 0.4

        usual_channel = random.choices(
            CHANNELS,
            weights=[0.6, 0.3, 0.1]
        )[0]

        start_hour = random.randint(6, 10)
        end_hour = random.randint(18, 23)

        profile = {
            "card_id": card_id,
            "cardholder_id": cardholder_id,
            "home_city": city_info["city"],
            "home_state": city_info["state"],
            "home_country": city_info["country"],
            "home_latitude": city_info["lat"],
            "home_longitude": city_info["lon"],
            "usual_categories": usual_categories,
            "avg_amount": round(avg_amount, 2),
            "amount_stddev": round(amount_stddev, 2),
            "usual_channel": usual_channel,
            "active_hour_start": start_hour,
            "active_hour_end": end_hour,
            "device_id": generate_id("device", i),
            "ip_region": city_info["state"],
        }

        profiles.append(profile)

    return profiles


def generate_normal_transaction(profile: dict, start: datetime, end: datetime, txn_num: int) -> dict:
    timestamp = random_timestamp(start, end)
    merchant_category = random_choice(profile["usual_categories"])
    amount = generate_amount(profile["avg_amount"], profile["amount_stddev"])

    return {
        "transaction_id": generate_id("txn", txn_num),
        "event_ts": timestamp,
        "card_id": profile["card_id"],
        "cardholder_id": profile["cardholder_id"],
        "merchant_id": generate_id("merchant", random.randint(1, 200)),
        "merchant_category": merchant_category,
        "amount": amount,
        "currency": CURRENCY,
        "channel": profile["usual_channel"],
        "txn_type": "purchase",
        "city": profile["home_city"],
        "state": profile["home_state"],
        "country": profile["home_country"],
        "latitude": profile["home_latitude"],
        "longitude": profile["home_longitude"],
        "device_id": profile["device_id"],
        "ip_address": generate_ip(),
        "is_fraud_ground_truth": 0,
        "fraud_type": "none",
    }


def generate_normal_transactions(
    profiles: list[dict],
    num_transactions: int,
    start: datetime,
    end: datetime
) -> list[dict]:
    transactions = []
    for txn_num in range(num_transactions):
        profile = random_choice(profiles)
        txn = generate_normal_transaction(profile, start, end, txn_num)
        transactions.append(txn)
    return transactions


def generate_amount_fraud_transaction(
    profile: dict,
    start: datetime,
    end: datetime,
    txn_num: int
) -> dict:
    timestamp = random_timestamp(start, end)
    merchant_category = random_choice(profile["usual_categories"])
    amount = round(profile["avg_amount"] * random.uniform(5, 12), 2)

    return {
        "transaction_id": generate_id("txn", txn_num),
        "event_ts": timestamp,
        "card_id": profile["card_id"],
        "cardholder_id": profile["cardholder_id"],
        "merchant_id": generate_id("merchant", random.randint(1, 200)),
        "merchant_category": merchant_category,
        "amount": amount,
        "currency": CURRENCY,
        "channel": profile["usual_channel"],
        "txn_type": "purchase",
        "city": profile["home_city"],
        "state": profile["home_state"],
        "country": profile["home_country"],
        "latitude": profile["home_latitude"],
        "longitude": profile["home_longitude"],
        "device_id": profile["device_id"],
        "ip_address": generate_ip(),
        "is_fraud_ground_truth": 1,
        "fraud_type": "amount",
    }


def generate_geo_fraud_transaction(
    profile: dict,
    start: datetime,
    end: datetime,
    txn_num: int
) -> dict:
    timestamp = random_timestamp(start, end)
    merchant_category = random_choice(profile["usual_categories"])
    amount = generate_amount(profile["avg_amount"], profile["amount_stddev"])

    foreign_cities = [c for c in CITIES if c["city"] != profile["home_city"]]
    foreign_city = random_choice(foreign_cities)

    return {
        "transaction_id": generate_id("txn", txn_num),
        "event_ts": timestamp,
        "card_id": profile["card_id"],
        "cardholder_id": profile["cardholder_id"],
        "merchant_id": generate_id("merchant", random.randint(1, 200)),
        "merchant_category": merchant_category,
        "amount": amount,
        "currency": CURRENCY,
        "channel": profile["usual_channel"],
        "txn_type": "purchase",
        "city": foreign_city["city"],
        "state": foreign_city["state"],
        "country": foreign_city["country"],
        "latitude": foreign_city["lat"],
        "longitude": foreign_city["lon"],
        "device_id": profile["device_id"],
        "ip_address": generate_ip(),
        "is_fraud_ground_truth": 1,
        "fraud_type": "geo",
    }


def generate_merchant_fraud_transaction(
    profile: dict,
    start: datetime,
    end: datetime,
    txn_num: int
) -> dict:
    timestamp = random_timestamp(start, end)
    amount = generate_amount(profile["avg_amount"], profile["amount_stddev"])

    unusual_categories = [c for c in MERCHANT_CATEGORIES if c not in profile["usual_categories"]]
    merchant_category = random_choice(unusual_categories)

    return {
        "transaction_id": generate_id("txn", txn_num),
        "event_ts": timestamp,
        "card_id": profile["card_id"],
        "cardholder_id": profile["cardholder_id"],
        "merchant_id": generate_id("merchant", random.randint(1, 200)),
        "merchant_category": merchant_category,
        "amount": amount,
        "currency": CURRENCY,
        "channel": profile["usual_channel"],
        "txn_type": "purchase",
        "city": profile["home_city"],
        "state": profile["home_state"],
        "country": profile["home_country"],
        "latitude": profile["home_latitude"],
        "longitude": profile["home_longitude"],
        "device_id": profile["device_id"],
        "ip_address": generate_ip(),
        "is_fraud_ground_truth": 1,
        "fraud_type": "merchant",
    }


def generate_velocity_fraud_transactions(
    profile: dict,
    start: datetime,
    end: datetime,
    txn_num: int
) -> list[dict]:
    burst_anchor = random_timestamp(start, end)
    num_burst = random.randint(3, 5)
    transactions = []

    for i in range(num_burst):
        offset_seconds = random.randint(0, 300)
        timestamp = burst_anchor + timedelta(seconds=offset_seconds)
        amount = generate_amount(profile["avg_amount"], profile["amount_stddev"])
        merchant_category = random_choice(profile["usual_categories"])

        transactions.append({
            "transaction_id": generate_id("txn", txn_num + i),
            "event_ts": timestamp,
            "card_id": profile["card_id"],
            "cardholder_id": profile["cardholder_id"],
            "merchant_id": generate_id("merchant", random.randint(1, 200)),
            "merchant_category": merchant_category,
            "amount": amount,
            "currency": CURRENCY,
            "channel": profile["usual_channel"],
            "txn_type": "purchase",
            "city": profile["home_city"],
            "state": profile["home_state"],
            "country": profile["home_country"],
            "latitude": profile["home_latitude"],
            "longitude": profile["home_longitude"],
            "device_id": profile["device_id"],
            "ip_address": generate_ip(),
            "is_fraud_ground_truth": 1,
            "fraud_type": "velocity",
        })

    return transactions


def generate_transactions(
    profiles: list[dict],
    num_transactions: int,
    fraud_rate: float,
    start: datetime,
    end: datetime
) -> list[dict]:
    transactions = []

    num_fraud = int(num_transactions * fraud_rate)
    num_normal = num_transactions - num_fraud

    txn_num = 0

    for _ in range(num_normal):
        profile = random_choice(profiles)
        txn = generate_normal_transaction(profile, start, end, txn_num)
        transactions.append(txn)
        txn_num += 1

    fraud_types = ["amount", "geo", "merchant", "velocity"]
    fraud_per_type = num_fraud // len(fraud_types)

    for _ in range(fraud_per_type):
        profile = random_choice(profiles)
        transactions.append(generate_amount_fraud_transaction(profile, start, end, txn_num))
        txn_num += 1

    for _ in range(fraud_per_type):
        profile = random_choice(profiles)
        transactions.append(generate_geo_fraud_transaction(profile, start, end, txn_num))
        txn_num += 1

    for _ in range(fraud_per_type):
        profile = random_choice(profiles)
        transactions.append(generate_merchant_fraud_transaction(profile, start, end, txn_num))
        txn_num += 1

    for _ in range(fraud_per_type):
        profile = random_choice(profiles)
        burst = generate_velocity_fraud_transactions(profile, start, end, txn_num)
        transactions.extend(burst)
        txn_num += len(burst)

    return transactions


def save_transactions(df: pd.DataFrame, output_path: str):
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} transactions to {output_path}")


def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1200)

    profiles = generate_card_profiles(10)

    start = datetime(2026, 1, 1)
    end = datetime(2026, 1, 7)

    transactions = generate_transactions(
        profiles=profiles,
        num_transactions=1000,
        fraud_rate=0.08,
        start=start,
        end=end,
    )

    df = pd.DataFrame(transactions)
    df = df.sample(frac=1).reset_index(drop=True)

    print(df.head(10))
    print()
    print("Total transactions:", len(df))
    print("Fraud count:", df["is_fraud_ground_truth"].sum())
    print()
    print(df["fraud_type"].value_counts())

    save_transactions(df, "data/transactions.csv")


if __name__ == "__main__":
    main()