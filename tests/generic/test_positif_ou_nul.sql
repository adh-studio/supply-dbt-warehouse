{% test positif_ou_nul(model, column_name) %}

-- Test generique personnalise : echoue si la colonne contient une valeur
-- strictement negative. Les valeurs nulles sont tolerees (a combiner avec
-- not_null si la colonne est obligatoire).

select *
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} < 0

{% endtest %}
