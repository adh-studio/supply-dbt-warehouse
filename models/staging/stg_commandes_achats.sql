with source as (
    select * from {{ ref('commandes_achats') }}
)

select
    id_commande,
    id_produit,
    id_fournisseur,
    id_entrepot,
    date_commande,
    quantite_commandee,
    statut
from source
