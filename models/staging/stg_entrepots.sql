with source as (
    select * from {{ ref('entrepots') }}
)

select
    id_entrepot,
    nom_entrepot,
    ville,
    capacite_m3,
    type_entrepot
from source
