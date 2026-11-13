-- Delai reel et taux de service par fournisseur.
-- Regles de gestion :
--   - delai reel = nombre de jours entre la commande et la premiere reception ;
--   - commande a l'heure = derniere reception au plus tard a la date promise
--     (date de commande + delai contractuel + 2 jours de tolerance) ;
--   - commande complete = quantite recue cumulee >= quantite commandee ;
--   - taux de service OTIF = commandes a l'heure et completes / commandes receptionnees.

with receptions_par_commande as (

    select
        id_commande,
        min(date_reception) as date_premiere_reception,
        max(date_reception) as date_derniere_reception,
        sum(quantite_recue) as quantite_recue_totale
    from {{ ref('stg_receptions') }}
    group by 1

),

commandes_enrichies as (

    select
        c.id_commande,
        c.id_fournisseur,
        c.date_commande,
        c.quantite_commandee,
        f.delai_contractuel_jours,
        r.date_premiere_reception,
        r.date_derniere_reception,
        r.quantite_recue_totale,
        datediff('day', c.date_commande, r.date_premiere_reception) as delai_reel_jours,
        case
            when r.id_commande is null then 0
            when datediff('day', c.date_commande, r.date_derniere_reception)
                 <= f.delai_contractuel_jours + 2
                 and r.quantite_recue_totale >= c.quantite_commandee then 1
            else 0
        end as commande_otif
    from {{ ref('stg_commandes_achats') }} as c
    inner join {{ ref('stg_fournisseurs') }} as f
        on c.id_fournisseur = f.id_fournisseur
    left join receptions_par_commande as r
        on c.id_commande = r.id_commande

),

final as (

    select
        c.id_fournisseur,
        f.nom_fournisseur,
        f.pays,
        f.note_rse,
        f.delai_contractuel_jours,
        count(*) as nb_commandes,
        count(c.date_premiere_reception) as nb_commandes_receptionnees,
        round(avg(c.delai_reel_jours), 1) as delai_moyen_reel_jours,
        round(avg(c.delai_reel_jours) - f.delai_contractuel_jours, 1) as ecart_moyen_jours,
        round(
            sum(c.commande_otif) * 1.0 / nullif(count(c.date_premiere_reception), 0), 4
        ) as taux_service_otif
    from commandes_enrichies as c
    inner join {{ ref('stg_fournisseurs') }} as f
        on c.id_fournisseur = f.id_fournisseur
    group by 1, 2, 3, 4, 5

)

select * from final
