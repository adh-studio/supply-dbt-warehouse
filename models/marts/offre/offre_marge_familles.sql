-- Performance economique par famille de produits.
-- Regles de gestion :
--   - chiffre d'affaires = somme des lignes de vente au prix reellement pratique ;
--   - marge brute = chiffre d'affaires - cout d'achat des quantites vendues ;
--   - rotation = quantites vendues sur la periode / stock moyen observe aux inventaires.

with ventes_valorisees as (

    select
        p.famille,
        v.quantite,
        v.montant_ligne,
        round(v.quantite * p.prix_achat, 2) as cout_ligne
    from {{ ref('stg_ventes') }} as v
    inner join {{ ref('stg_produits') }} as p on v.id_produit = p.id_produit

),

agregat_ventes as (

    select
        famille,
        sum(quantite) as quantite_vendue,
        round(sum(montant_ligne), 2) as chiffre_affaires,
        round(sum(montant_ligne) - sum(cout_ligne), 2) as marge_brute
    from ventes_valorisees
    group by 1

),

stock_moyen_famille as (

    select
        p.famille,
        round(
            sum(s.quantite_disponible) * 1.0
            / count(distinct s.date_inventaire), 1
        ) as stock_moyen_unites
    from {{ ref('stg_stocks') }} as s
    inner join {{ ref('stg_produits') }} as p on s.id_produit = p.id_produit
    group by 1

),

final as (

    select
        v.famille,
        v.quantite_vendue,
        v.chiffre_affaires,
        v.marge_brute,
        round(v.marge_brute / nullif(v.chiffre_affaires, 0), 4) as taux_marge,
        m.stock_moyen_unites,
        round(v.quantite_vendue / nullif(m.stock_moyen_unites, 0), 2) as rotation_periode
    from agregat_ventes as v
    inner join stock_moyen_famille as m on v.famille = m.famille

)

select * from final
