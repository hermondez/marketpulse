{# Usado por CI para borrar los esquemas efímeros CI_PR_<n>_*. Solo permite prefijo CI_. #}
{% macro drop_schema_if_exists(schema) %}
    {% if not schema.upper().startswith('CI_') %}
        {{ exceptions.raise_compiler_error('Solo se pueden borrar esquemas CI_*') }}
    {% endif %}
    {% do run_query('drop schema if exists ' ~ target.database ~ '.' ~ schema ~ ' cascade') %}
    {{ log('Esquema borrado: ' ~ schema, info=True) }}
{% endmacro %}
