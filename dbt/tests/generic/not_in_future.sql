{# Ninguna fecha puede ser posterior a hoy (detecta errores de zona horaria o de la fuente). #}
{% test not_in_future(model, column_name) %}
select * from {{ model }} where {{ column_name }} > current_date()
{% endtest %}
