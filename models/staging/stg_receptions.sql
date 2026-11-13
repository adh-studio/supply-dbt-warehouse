with source as (
    select * from {{ ref('receptions') }}
)

select
    id_reception,
    id_commande,
    date_reception,
    quantite_recue
from source
