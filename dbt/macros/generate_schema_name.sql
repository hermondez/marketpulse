{#
  En prod: esquemas limpios (STAGING, MARTS...).
  En dev/ci: prefijo del target (DEV_MARTS, CI_123_MARTS) para no pisar producción.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim | upper }}
    {%- else -%}
        {{ target.schema | upper }}_{{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
