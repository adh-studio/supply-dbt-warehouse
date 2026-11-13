-- Taux de rupture par entrepot et famille de produits.
-- Regle de gestion : une rupture est un couple produit x entrepot observe a zero
-- lors d'un inventaire. Le taux rapporte les observations en rupture au total
-- des observations de la periode.

with observations as (

    select
        s.id_entrepot,
        p.famille,
        s.indicateur_rupture
    from {{ ref('stg_stocks') }} as s
    inner join {{ ref('stg_produits') }} as p on s.id_produit = p.id_produit

),

final as (

    select
        o.id_entrepot,
        e.nom_entrepot,
        o.famille,
        count(*) as nb_observations,
        sum(o.indicateur_rupture) as nb_ruptures,
        round(sum(o.indicateur_rupture) * 1.0 / count(*), 4) as taux_rupture
    from observations as o
    inner join {{ ref('stg_entrepots') }} as e on o.id_entrepot = e.id_entrepot
    group by 1, 2, 3

)

select * from final
