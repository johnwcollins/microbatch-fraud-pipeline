with stg as (
    select * from {{ ref('stg_transactions') }}
),

card_baselines as (
    select
        card_id,
        avg(amount) as card_mean_amount,
        stddev(amount) as card_std_amount,
        median(latitude) as card_home_lat,
        median(longitude) as card_home_lon,
        count(*) as card_txn_count
    from stg
    where is_fraud_ground_truth = 0
    group by card_id
),

joined as (
    select
        stg.*,
        baselines.card_mean_amount,
        baselines.card_std_amount,
        baselines.card_home_lat,
        baselines.card_home_lon,
        baselines.card_txn_count,
        (stg.amount - baselines.card_mean_amount) / nullif(baselines.card_std_amount, 0) as amount_zscore,
        sqrt(
            power(stg.latitude - baselines.card_home_lat, 2) +
            power(stg.longitude - baselines.card_home_lon, 2)
        ) * 111 as geo_distance_km
    from stg
    left join card_baselines as baselines
        on stg.card_id = baselines.card_id
)

select * from joined