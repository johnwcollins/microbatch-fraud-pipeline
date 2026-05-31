
  
  create view "fraud"."main"."fct_fraud_signals__dbt_tmp" as (
    with fct as (
    select * from "fraud"."main"."fct_transactions"
),

signals as (
    select
        *,
        case
            when amount_zscore > 3.0 then 1
            when geo_distance_km > 500 then 1
            else 0
        end as fraud_signal,
        case
            when amount_zscore > 3.0 then 'amount_anomaly'
            when geo_distance_km > 500 then 'geo_anomaly'
            else 'none'
        end as signal_reason
    from fct
)

select * from signals
  );
