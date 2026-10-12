{#
  Snapshot (SCD tipo 2) del portafolio simulado: si editas el seed (compras/ventas
  hipotéticas), queda el historial con dbt_valid_from / dbt_valid_to.
#}
{% snapshot snap_portfolio_holdings %}
{{
    config(
      target_schema=('SNAPSHOTS' if target.name == 'prod' else target.schema ~ '_SNAPSHOTS'),
      unique_key="portfolio_id || '-' || ticker",
      strategy='check',
      check_cols=['shares', 'avg_cost'],
    )
}}
select * from {{ ref('seed_portfolio_holdings') }}
{% endsnapshot %}
