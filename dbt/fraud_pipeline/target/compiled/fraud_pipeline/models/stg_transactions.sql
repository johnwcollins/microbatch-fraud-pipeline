with source as (
    select * from raw_transactions
),

renamed as (
    select
        transaction_id,
        cast(event_ts as timestamp) as event_ts,
        card_id,
        cardholder_id,
        merchant_id,
        merchant_category,
        cast(amount as double) as amount,
        currency,
        channel,
        txn_type,
        city,
        state,
        country,
        cast(latitude as double) as latitude,
        cast(longitude as double) as longitude,
        device_id,
        ip_address,
        cast(is_fraud_ground_truth as integer) as is_fraud_ground_truth,
        fraud_type
    from source
)

select * from renamed