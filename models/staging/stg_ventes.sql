with source as (
    select * from {{ ref('ventes') }}
)

select
    id_vente,
    date_vente,
    id_produit,
    id_entrepot,
    canal,
    quantite,
    prix_unitaire,
    round(quantite * prix_unitaire, 2) as montant_ligne
from source
