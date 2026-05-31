# Transaction Schema

## Columns

| Column | Type | Description |
|---|---|---|
| transaction_id | string | Unique transaction identifier |
| event_ts | timestamp | Event timestamp |
| card_id | string | Card identifier |
| cardholder_id | string | Cardholder identifier |
| merchant_id | string | Merchant identifier |
| merchant_category | string | Merchant category |
| amount | float | Transaction amount in USD |
| currency | string | Currency code |
| channel | string | Payment channel |
| txn_type | string | Transaction type |
| city | string | Transaction city |
| state | string | Transaction state |
| country | string | Transaction country |
| latitude | float | Transaction latitude |
| longitude | float | Transaction longitude |
| device_id | string | Device identifier |
| ip_address | string | IP address |
| is_fraud_ground_truth | integer | 1 if simulator injected fraud, else 0 |

## Accepted Values

### currency
- USD

### channel
- card_present
- online
- mobile_wallet

### txn_type
- purchase
- refund
- cash_withdrawal

### merchant_category
- grocery
- gas
- restaurant
- travel
- electronics
- pharmacy
- retail
- entertainment