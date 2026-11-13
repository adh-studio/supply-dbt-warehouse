# supply-dbt-warehouse

[![CI](https://github.com/adh-studio/supply-dbt-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/adh-studio/supply-dbt-warehouse/actions/workflows/ci.yml)

Entrepot analytique dbt du domaine **Offre et Supply** d'une enseigne de decoration et d'ameublement. Le projet transforme des donnees operationnelles (fournisseurs, produits, entrepots, commandes d'achats, receptions, stocks, ventes) en data products analytiques testes, documentes et prets a consommer.

Documentation dbt publiee : https://adh-studio.github.io/supply-dbt-warehouse/

## Contexte metier

Une enseigne de decoration pilote son activite autour de deux enjeux :

- **Supply** : securiser la disponibilite produit tout en maitrisant le stock. Les equipes ont besoin de connaitre la couverture de stock en jours, le taux de rupture, les delais reels des fournisseurs et leur taux de service OTIF (a l'heure et complet).
- **Offre** : piloter la rentabilite de l'assortiment. Les equipes suivent la marge et la rotation par famille, ainsi que le classement top et flop des produits.

Les donnees sont synthetiques, generees par un script deterministe commite dans le depot (`scripts/generer_seeds.py`), avec un univers realiste : canapes, luminaires, arts de la table, tapis, rangement, textile deco, 4 entrepots, 8 fournisseurs.

## Architecture

```
seeds (CSV generes)          staging (vues)            marts (tables)
--------------------         -----------------         -------------------------------
fournisseurs           --->  stg_fournisseurs    --->  marts/supply
produits               --->  stg_produits              - supply_couverture_stock
entrepots              --->  stg_entrepots             - supply_taux_rupture
commandes_achats       --->  stg_commandes_achats      - supply_delais_fournisseurs
receptions             --->  stg_receptions      --->  marts/offre
stocks                 --->  stg_stocks                - offre_marge_familles
ventes                 --->  stg_ventes                - offre_top_flop_produits
```

- **Moteur** : dbt-core + dbt-duckdb, aucun service externe, tout tourne en local.
- **Staging** : typage et renommage, aucune logique metier.
- **Marts** : regles de gestion documentees en tete de chaque modele SQL et dans les schema.yml.
- **Qualite** : 132 tests dbt executes a chaque build (unique, not_null, accepted_values, relationships, dbt_utils, 2 tests generiques personnalises `positif_ou_nul` et `ratio_entre_bornes`, 1 test singulier de coherence receptions vs commandes).
- **Documentation** : site dbt docs genere et versionne dans `docs/` pour GitHub Pages.

## Installation

Prerequis : Python 3.11 a 3.13.

```bash
git clone https://github.com/adh-studio/supply-dbt-warehouse.git
cd supply-dbt-warehouse
./run_e2e.sh
```

Le script cree l'environnement virtuel, installe les dependances epinglees, regenere les seeds, puis enchaine `dbt deps`, `dbt seed` et `dbt build`.

## Rejouer les tests

```bash
./run_e2e.sh
```

Ou, une fois l'environnement en place :

```bash
export DBT_PROFILES_DIR="$PWD"
.venv/bin/dbt build
```

La CI GitHub Actions (`.github/workflows/ci.yml`) execute exactement le meme scenario a chaque push.

## Ce que ce projet demontre pour un role de Product Owner Data et IA

- **Data products definis par le metier** : chaque mart repond a une question d'une equipe Offre ou Supply, avec un grain explicite, des regles de gestion ecrites et des criteres d'acceptation traduits en tests dbt.
- **Qualite contractualisee** : les attentes sur les donnees (unicite, integrite referentielle, bornes des ratios, coherence receptions vs commandes) sont versionnees et verifiees a chaque build, comme le prevoit une demarche de data contracts.
- **Documentation self-service** : le catalogue dbt (lineage, descriptions de colonnes, tests) est publie sur GitHub Pages et consultable par les equipes sans outil supplementaire, premiere brique d'un catalogue de data products.
- **Domain-Driven Data** : la separation marts/supply et marts/offre reflete un decoupage par domaine metier, aligne avec une organisation Data Mesh ou chaque domaine possede ses produits.
- **Industrialisation** : pipeline reproductible de bout en bout (donnees synthetiques deterministes, dependances epinglees, CI sur chaque push), condition du passage a l'echelle et de la mesure d'adoption.

## Structure du depot

```
scripts/generer_seeds.py   generation deterministe des donnees synthetiques
seeds/                     CSV sources versionnes
models/staging/            vues de staging + tests
models/marts/supply/       data products supply + tests
models/marts/offre/        data products offre + tests
tests/generic/             tests generiques personnalises
tests/                     test singulier
docs/                      site dbt docs pour GitHub Pages
run_e2e.sh                 test de bout en bout
.github/workflows/ci.yml   CI GitHub Actions
```
