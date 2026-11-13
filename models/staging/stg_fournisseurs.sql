with source as (
    select * from {{ ref('fournisseurs') }}
)

select
    id_fournisseur,
    nom_fournisseur,
    pays,
    delai_contractuel_jours,
    note_rse
from source
