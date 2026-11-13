-- Test singulier : la quantite receptionnee cumulee d'une commande d'achat
-- ne doit jamais depasser la quantite commandee. Un depassement signalerait
-- une erreur de saisie en entrepot ou un doublon de reception.

with cumul_receptions as (

    select
        id_commande,
        sum(quantite_recue) as quantite_recue_totale
    from {{ ref('stg_receptions') }}
    group by 1

)

select
    c.id_commande,
    c.quantite_commandee,
    r.quantite_recue_totale
from {{ ref('stg_commandes_achats') }} as c
inner join cumul_receptions as r on c.id_commande = r.id_commande
where r.quantite_recue_totale > c.quantite_commandee
