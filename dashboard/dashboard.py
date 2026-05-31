import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/fraud.duckdb")

st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide"
)

@st.cache_data(ttl=10)
def load_data() -> pd.DataFrame:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    df = conn.execute("SELECT * FROM scored_transactions ORDER BY event_ts DESC").df()
    conn.close()
    df["event_ts"] = pd.to_datetime(df["event_ts"])
    return df

df = load_data()

st.title("Real-Time Payment Fraud Detection")
st.caption("Micro-batch pipeline | Rule-based scorer | DuckDB backend")

st.divider()

total = len(df)
flagged = int(df["fraud_score"].sum())
ground_truth = int(df["is_fraud_ground_truth"].sum())
true_pos = int(((df["fraud_score"] == 1) & (df["is_fraud_ground_truth"] == 1)).sum())
false_pos = int(((df["fraud_score"] == 1) & (df["is_fraud_ground_truth"] == 0)).sum())
false_neg = int(((df["fraud_score"] == 0) & (df["is_fraud_ground_truth"] == 1)).sum())
fraud_rate = round(flagged / total * 100, 2) if total > 0 else 0
precision = round(true_pos / (true_pos + false_pos) * 100, 2) if (true_pos + false_pos) > 0 else 0
recall = round(true_pos / (true_pos + false_neg) * 100, 2) if (true_pos + false_neg) > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Transactions", f"{total:,}")
col2.metric("Flagged as Fraud", f"{flagged:,}", delta=f"{fraud_rate}% of total", delta_color="inverse")
col3.metric("Precision", f"{precision}%")
col4.metric("Recall", f"{recall}%")
col5.metric("False Positives", f"{false_pos:,}", delta_color="inverse")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Fraud Flags by Rule")
    reason_counts = df[df["score_reason"] != "none"]["score_reason"].value_counts().reset_index()
    reason_counts.columns = ["rule", "count"]
    st.bar_chart(reason_counts.set_index("rule"))

with col_right:
    st.subheader("Transactions Over Time")
    df["date"] = df["event_ts"].dt.date
    timeline = df.groupby(["date", "fraud_score"]).size().unstack(fill_value=0).reset_index()
    timeline.columns = ["date", "normal", "flagged"] if 0 in df["fraud_score"].values else ["date", "flagged"]
    timeline = timeline.set_index("date")
    st.bar_chart(timeline)

st.divider()

st.subheader("Transaction Feed")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    show_filter = st.selectbox("Show", ["All", "Flagged Only", "Normal Only"])

with filter_col2:
    reason_filter = st.selectbox("Score Reason", ["All"] + sorted(df["score_reason"].unique().tolist()))

with filter_col3:
    card_filter = st.selectbox("Card ID", ["All"] + sorted(df["card_id"].unique().tolist()))

filtered = df.copy()

if show_filter == "Flagged Only":
    filtered = filtered[filtered["fraud_score"] == 1]
elif show_filter == "Normal Only":
    filtered = filtered[filtered["fraud_score"] == 0]

if reason_filter != "All":
    filtered = filtered[filtered["score_reason"] == reason_filter]

if card_filter != "All":
    filtered = filtered[filtered["card_id"] == card_filter]

display_cols = [
    "transaction_id", "event_ts", "card_id", "merchant_category",
    "amount", "city", "channel", "fraud_score", "score_reason",
    "is_fraud_ground_truth", "fraud_type"
]

def highlight_fraud(row):
    if row["fraud_score"] == 1 and row["is_fraud_ground_truth"] == 1:
        return ["background-color: #3d1f1f"] * len(row)
    elif row["fraud_score"] == 1:
        return ["background-color: #3d3000"] * len(row)
    return [""] * len(row)

st.dataframe(
    filtered[display_cols].style.apply(highlight_fraud, axis=1),
    use_container_width=True,
    height=500
)

st.caption("Red = true positive | Yellow = false positive | No highlight = normal")