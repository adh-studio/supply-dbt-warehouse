-- Classement des produits par chiffre d'affaires, avec segment top, coeur de gamme ou flop.
-- Regles de gestion :
--   - le rang est attribue par chiffre d'affaires decroissant ;
--   - top 10 = les 10 premiers rangs, flop 10 = les 10 derniers rangs parmi
--     les produits reellement vendus ;
--   - un produit sans aucune vente est classe en flop d'office (segment 'sans_vente').

with agregat_produits as (

    select
        p.id_produit,
        p.nom_produit,
        p.famille,
        coalesce(sum(v.quantite), 0) as quantite_vendue,
        round(coalesce(sum(v.montant_ligne), 0), 2) as chiffre_affaires,
        round(coalesce(sum(v.montant_ligne - v.quantite * p.prix_achat), 0), 2) as marge_brute
    from {{ ref('stg_produits') }} as p
    left join {{ ref('stg_ventes') }} as v on p.id_produit = v.id_produit
    group by 1, 2, 3

),

classement as (

    select
        *,
        row_number() over (order by chiffre_affaires desc, id_produit) as rang_ca,
        count(*) over () as nb_produits
    from agregat_produits

),

final as (

    select
        id_produit,
        nom_produit,
        famille,
        quantite_vendue,
        chiffre_affaires,
        marge_brute,
        rang_ca,
        case
            when quantite_vendue = 0 then 'sans_vente'
            when rang_ca <= 10 then 'top'
            when rang_ca > nb_produits - 10 then 'flop'
            else 'coeur_de_gamme'
        end as segment
    from classement

)

select * from final
