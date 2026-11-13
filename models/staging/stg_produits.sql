with source as (
    select * from {{ ref('produits') }}
)

select
    id_produit,
    nom_produit,
    famille,
    id_fournisseur,
    prix_achat,
    prix_vente,
    round(prix_vente - prix_achat, 2) as marge_unitaire,
    round((prix_vente - prix_achat) / nullif(prix_vente, 0), 4) as taux_marge_unitaire
from source
