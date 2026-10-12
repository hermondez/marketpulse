{# División segura: evita errores por división entre cero. #}
{% macro safe_divide(numerator, denominator) -%}
    ({{ numerator }}) / nullif({{ denominator }}, 0)
{%- endmacro %}

{# Media móvil simple: NULL hasta tener `n` observaciones (evita SMA "parciales" engañosas). #}
{% macro sma(col, n, partition='ticker', order='trade_date') -%}
    case when count({{ col }}) over (partition by {{ partition }} order by {{ order }}
                                     rows between {{ n - 1 }} preceding and current row) = {{ n }}
         then avg({{ col }}) over (partition by {{ partition }} order by {{ order }}
                                   rows between {{ n - 1 }} preceding and current row)
    end
{%- endmacro %}

{# Volatilidad anualizada: desviación estándar de retornos diarios * raíz(252). #}
{% macro annualized_volatility(return_col, n, partition='ticker', order='trade_date') -%}
    case when count({{ return_col }}) over (partition by {{ partition }} order by {{ order }}
                                            rows between {{ n - 1 }} preceding and current row) = {{ n }}
         then stddev_samp({{ return_col }}) over (partition by {{ partition }} order by {{ order }}
                                                  rows between {{ n - 1 }} preceding and current row)
              * sqrt({{ var('trading_days_per_year') }})
    end
{%- endmacro %}

{#
  Filtro incremental con "lookback": recalcula los últimos N días para absorber
  correcciones de la fuente. Solo actúa cuando el modelo corre en modo incremental.
#}
{% macro incremental_lookback_filter(date_col, days=var('incremental_lookback_days')) -%}
    {% if is_incremental() %}
        {{ date_col }} >= (select dateadd(day, -{{ days }}, max({{ date_col }})) from {{ this }})
    {% else %}
        true
    {% endif %}
{%- endmacro %}
