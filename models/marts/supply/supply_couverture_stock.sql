-- Couverture de stock en jours par produit et entrepot.
-- Regle de gestion : couverture = stock du dernier inventaire / vente moyenne journaliere
-- calculee sur les 90 derniers jours de l'historique de ventes.

with dernier_stock as (

    select
        id_produit,
        id_entrepot,
        date_inventaire,
        quantite_disponible
    from {{ ref('stg_stocks') }}
    qualify row_number() over (
        partition by id_produit, id_entrepot
        order by date_inventaire desc
    ) = 1

),

borne_ventes as (

    select max(date_vente) as date_max from {{ ref('stg_ventes') }}

),

ventes_90_jours as (

    select
        v.id_produit,
        v.id_entrepot,
        sum(v.quantite) as quantite_vendue_90j
    from {{ ref('stg_ventes') }} as v
    cross join borne_ventes as b
    where v.date_vente > b.date_max - interval 90 day
    group by 1, 2

),

final as (

    select
        s.id_produit,
        p.nom_produit,
        p.famille,
        s.id_entrepot,
        e.nom_entrepot,
        s.date_inventaire as date_dernier_inventaire,
        s.quantite_disponible,
        coalesce(v.quantite_vendue_90j, 0) as quantite_vendue_90j,
        round(coalesce(v.quantite_vendue_90j, 0) / 90.0, 3) as vente_moyenne_jour,
        case
            when coalesce(v.quantite_vendue_90j, 0) = 0 then null
            else round(s.quantite_disponible * 90.0 / v.quantite_vendue_90j, 1)
        end as couverture_jours,
        case
            when s.quantite_disponible = 0 then 'rupture'
            when coalesce(v.quantite_vendue_90j, 0) = 0 then 'dormant'
            when s.quantite_disponible * 90.0 / v.quantite_vendue_90j < 15 then 'tendu'
            when s.quantite_disponible * 90.0 / v.quantite_vendue_90j <= 60 then 'sain'
            else 'surstock'
        end as statut_couverture
    from dernier_stock as s
    inner join {{ ref('stg_produits') }} as p on s.id_produit = p.id_produit
    inner join {{ ref('stg_entrepots') }} as e on s.id_entrepot = e.id_entrepot
    left join ventes_90_jours as v
        on s.id_produit = v.id_produit
        and s.id_entrepot = v.id_entrepot

)

select * from final
