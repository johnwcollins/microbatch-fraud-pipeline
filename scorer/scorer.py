import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/fraud.duckdb")
RAW_TABLE = "raw_transactions"
SCORED_TABLE = "scored_transactions"

AMOUNT_ZSCORE_THRESHOLD = 3.0
VELOCITY_WINDOW_MINUTES = 5
VELOCITY_TXN_THRESHOLD = 3
GEO_DISTANCE_KM_THRESHOLD = 500


def load_transactions(conn) -> pd.DataFrame:
    df = conn.execute(f"SELECT * FROM {RAW_TABLE}").df()
    df["event_ts"] = pd.to_datetime(df["event_ts"])
    return df


def compute_card_baselines(df: pd.DataFrame) -> pd.DataFrame:
    normal = df[df["is_fraud_ground_truth"] == 0]
    baselines = (
        normal.groupby("card_id")
        .agg(
            card_mean_amount=("amount", "mean"),
            card_std_amount=("amount", "std"),
            card_home_lat=("latitude", "median"),
            card_home_lon=("longitude", "median"),
            card_usual_categories=("merchant_category", lambda x: list(x.unique())),
        )
        .reset_index()
    )
    return baselines


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    import math
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def flag_amount(df: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(baselines[["card_id", "card_mean_amount", "card_std_amount"]], on="card_id", how="left")
    df["amount_zscore"] = (df["amount"] - df["card_mean_amount"]) / df["card_std_amount"]
    flag = df["amount_zscore"] > AMOUNT_ZSCORE_THRESHOLD
    df.loc[flag, "fraud_score"] = 1
    df.loc[flag, "score_reason"] = "amount_anomaly"
    df = df.drop(columns=["card_mean_amount", "card_std_amount", "amount_zscore"])
    return df


def flag_geo(df: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(baselines[["card_id", "card_home_lat", "card_home_lon"]], on="card_id", how="left")
    df["geo_distance_km"] = df.apply(
        lambda row: haversine_km(row["card_home_lat"], row["card_home_lon"], row["latitude"], row["longitude"]),
        axis=1
    )
    flag = df["geo_distance_km"] > GEO_DISTANCE_KM_THRESHOLD
    df.loc[flag & (df["fraud_score"] == 0), "score_reason"] = "geo_anomaly"
    df.loc[flag, "fraud_score"] = 1
    df = df.drop(columns=["card_home_lat", "card_home_lon", "geo_distance_km"])
    return df


def flag_merchant(df: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(baselines[["card_id", "card_usual_categories"]], on="card_id", how="left")
    flag = df.apply(
        lambda row: row["merchant_category"] not in row["card_usual_categories"],
        axis=1
    )
    df.loc[flag & (df["fraud_score"] == 0), "score_reason"] = "merchant_anomaly"
    df.loc[flag, "fraud_score"] = 1
    df = df.drop(columns=["card_usual_categories"])
    return df


def flag_velocity(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["card_id", "event_ts"]).reset_index(drop=True)
    velocity_flags = set()

    for card_id, group in df.groupby("card_id"):
        timestamps = group["event_ts"].tolist()
        indices = group.index.tolist()

        for i in range(len(timestamps)):
            window = [
                indices[j] for j in range(i, len(timestamps))
                if (timestamps[j] - timestamps[i]).total_seconds() <= VELOCITY_WINDOW_MINUTES * 60
            ]
            if len(window) >= VELOCITY_TXN_THRESHOLD:
                for idx in window:
                    velocity_flags.add(idx)

    flag = df.index.isin(velocity_flags)
    df.loc[flag & (df["fraud_score"] == 0), "score_reason"] = "velocity_anomaly"
    df.loc[flag, "fraud_score"] = 1
    return df


def score_transactions(df: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    df["fraud_score"] = 0
    df["score_reason"] = "none"

    df = flag_amount(df, baselines)
    df = flag_geo(df, baselines)
    df = flag_merchant(df, baselines)
    df = flag_velocity(df)

    return df


def write_scored_table(conn, df: pd.DataFrame, table_name: str) -> None:
    conn.register("scored_df", df)
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM scored_df")


def summarize(df: pd.DataFrame) -> None:
    print(f"Total transactions scored: {len(df)}")
    print(f"Flagged as fraud:          {df['fraud_score'].sum()}")
    print(f"Ground truth fraud:        {df['is_fraud_ground_truth'].sum()}")
    print()
    true_pos  = ((df["fraud_score"] == 1) & (df["is_fraud_ground_truth"] == 1)).sum()
    false_pos = ((df["fraud_score"] == 1) & (df["is_fraud_ground_truth"] == 0)).sum()
    false_neg = ((df["fraud_score"] == 0) & (df["is_fraud_ground_truth"] == 1)).sum()
    print(f"True positives:  {true_pos}")
    print(f"False positives: {false_pos}")
    print(f"False negatives: {false_neg}")
    print()
    print("Score reason breakdown:")
    print(df["score_reason"].value_counts())


def main():
    print("Scorer running...")
    conn = duckdb.connect(str(DB_PATH))
    try:
        df = load_transactions(conn)
        baselines = compute_card_baselines(df)
        scored = score_transactions(df, baselines)
        write_scored_table(conn, scored, SCORED_TABLE)
        summarize(scored)
        print(f"\nScored transactions written to table: {SCORED_TABLE}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()