from pathlib import Path
import duckdb
import pandas as pd


CSV_PATH = Path("data/transactions.csv")
DB_PATH = Path("data/fraud.duckdb")
TABLE_NAME = "raw_transactions"


def load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError(f"CSV file is empty: {csv_path}")

    return df


def connect_duckdb(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def create_table_and_load(conn, df: pd.DataFrame, table_name: str) -> None:
    conn.register("transactions_df", df)

    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    conn.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT *
        FROM transactions_df
    """)


def validate_row_counts(df: pd.DataFrame, conn, table_name: str) -> None:
    csv_row_count = len(df)
    db_row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    print(f"CSV row count: {csv_row_count}")
    print(f"DuckDB row count: {db_row_count}")

    if csv_row_count != db_row_count:
        raise ValueError(
            f"Row count mismatch: CSV has {csv_row_count}, DuckDB has {db_row_count}"
        )

    print("Row count validation passed.")


def main():
    print("Starting ingestion...")

    df = load_csv(CSV_PATH)
    conn = connect_duckdb(DB_PATH)

    try:
        create_table_and_load(conn, df, TABLE_NAME)
        validate_row_counts(df, conn, TABLE_NAME)

        print(f"Loaded data into DuckDB: {DB_PATH}")
        print(f"Table created: {TABLE_NAME}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()