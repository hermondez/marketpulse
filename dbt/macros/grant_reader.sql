{# post-hook en marts: el rol de solo lectura (Módulo 4) puede leer las tablas nuevas. #}
{% macro grant_select_to_reader() %}
    {% if target.name == 'prod' %}
        grant select on {{ this }} to role MARKETPULSE_READER
    {% else %}
        select 1
    {% endif %}
{% endmacro %}
