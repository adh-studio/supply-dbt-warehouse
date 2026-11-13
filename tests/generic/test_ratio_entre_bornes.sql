{% test ratio_entre_bornes(model, column_name, borne_min=0, borne_max=1) %}

-- Test generique personnalise : echoue si un ratio sort de l'intervalle
-- [borne_min, borne_max]. Utilise pour les taux (rupture, marge, service)
-- qui doivent rester des proportions valides.

select *
from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ borne_min }} or {{ column_name }} > {{ borne_max }})

{% endtest %}
