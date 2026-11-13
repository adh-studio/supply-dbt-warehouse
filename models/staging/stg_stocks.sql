with source as (
    select * from {{ ref('stocks') }}
)

select
    id_produit,
    id_entrepot,
    date_inventaire,
    quantite_disponible,
    cast(quantite_disponible = 0 as integer) as indicateur_rupture
from source
