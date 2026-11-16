# supply-dbt-warehouse

[![CI](https://github.com/adh-studio/supply-dbt-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/adh-studio/supply-dbt-warehouse/actions/workflows/ci.yml)

Entrepot analytique dbt + DuckDB du domaine **Offre et Supply** d'une activite reelle : l'import et la distribution de produits electroniques a Madagascar (consoles et gaming, audio, telephonie, montres connectees, eclairage LED, electromenager). C'est la replique analytique de l'ERP de l'auteur : les lots d'import Chine -> Tana (fret AIR via Ivato, SEA via le port de Tamatave), le passage en douane, les stocks des depots et boutiques d'Antananarivo et les ventes en ariary (MGA) y deviennent des data products testes, documentes et prets a consommer.

Documentation dbt publiee : https://adh-studio.github.io/supply-dbt-warehouse/

## Contexte metier

L'activite consiste a sourcer des produits aupres d'usines et de grossistes de Shenzhen, Guangzhou, Yiwu, Dongguan et Dubai, a les importer par lots (fret aerien en 10 a 15 jours, fret maritime en 40 a 55 jours), puis a les vendre en boutique a Antananarivo et en ligne avec livraison sur Tana. Deux enjeux pilotent l'activite :

- **Supply** : securiser la disponibilite produit malgre des delais d'import longs et incertains (douane, congestion du port de Tamatave). Les indicateurs cles sont la couverture de stock en jours, le taux de rupture, les delais reels des fournisseurs et leur taux de service OTIF (a l'heure et complet).
- **Offre** : piloter la rentabilite de l'assortiment importe. Marge et rotation par famille, classement top et flop des produits, detection des paris rates (surstock) et des references dormantes.

## Correspondance ERP (Prisma) -> entrepot

L'ERP source est une application PostgreSQL + Prisma. Chaque seed de l'entrepot correspond a une ou plusieurs tables de l'ERP :

| Table de l'ERP (Prisma) | Seed de l'entrepot | Notes |
|---|---|---|
| `ShipmentBatch` + `BatchItem` | `commandes_achats` | un lot d'import par produit, fret AIR ou SEA |
| Lots passes en `RECEIVED_TANA` (apres `CUSTOMS_CLEARING`) | `receptions` | arrivees apres douane, parfois en plusieurs fois |
| `Order` / `OrderItem` | `ventes` | ventes boutique et web, prix figes en MGA |
| `StockMovement` / `SerialItem` | `stocks` | photographies de stock par produit et par site |
| `Product` / `ProductVariant` | `produits` | cout de revient debarque (`landedCostMga`) et prix de vente (`sellingPriceMga`) |
| Fournisseurs sources sur les lots | `fournisseurs` | delai de fret promis par mode, note RSE d'audit usine |

Dans le depot public, les donnees sont **synthetiques et representatives**, generees par un script deterministe commite dans le depot (`scripts/generer_seeds.py`, graine fixe). En local, les seeds peuvent etre regeneres depuis l'ERP reel avec `scripts/exporter_depuis_erp.py` (optionnel, voir plus bas). Tous les montants sont en ariary (MGA) : une PS5 autour de 3 500 000 MGA, des ecouteurs TWS autour de 150 000 MGA.

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
- **Qualite** : 132 tests dbt executes a chaque build (unique, not_null, accepted_values, relationships, dbt_utils, 2 tests generiques personnalises `positif_ou_nul` et `ratio_entre_bornes`, 1 test singulier de coherence receptions vs lots d'import).
- **Documentation** : site dbt docs genere et versionne dans `docs/` pour GitHub Pages.

## Installation

Prerequis : Python 3.11 a 3.13.

```bash
git clone https://github.com/adh-studio/supply-dbt-warehouse.git
cd supply-dbt-warehouse
./run_e2e.sh
```

Le script cree l'environnement virtuel, installe les dependances epinglees, genere les seeds s'ils sont absents, puis enchaine `dbt deps`, `dbt seed` et `dbt build`.

### Protection des seeds saisis

Les seeds CSV sont desormais alimentes par la plateforme de saisie SupplyOps : `run_e2e.sh` ne les regenere plus s'ils existent deja (message `Seeds existants conserves`). La generation synthetique (`scripts/generer_seeds.py`) ne s'execute que si un des sept CSV manque, ou sur demande explicite :

```bash
REGENERER_SEEDS=1 ./run_e2e.sh   # repart des donnees synthetiques, ecrase les saisies
```

Deux fichiers d'etat non versionnes vivent a la racine du repo : `etat_build.json` (dernier build dbt : statut, pass/fail/total, duree, declencheur, historique des 20 derniers), ecrit par le module `pipeline` du repo [supply-data-agents](https://github.com/adh-studio/supply-data-agents), et `supplyops_etat.json` (saisies en attente de publication), ecrit par SupplyOps. Le verrou `.pipeline.lock` empeche deux builds concurrents.

## Le catalogue de data products (`catalogue/`)

Les 5 marts sont declares comme **data products** dans `catalogue/`, un YAML par produit de donnees, ranges par domaine (vision Data Mesh, cote producteur) :

```
catalogue/
  schema/data_product.schema.json   JSON Schema qui valide chaque declaration
  supply/couverture_stock.yaml            -> mart supply_couverture_stock
  supply/performance_fournisseurs.yaml    -> marts supply_delais_fournisseurs + supply_taux_rupture
  offre/rentabilite_familles.yaml         -> mart offre_marge_familles
  offre/palmares_produits.yaml            -> mart offre_top_flop_produits
```

Chaque declaration porte : la description metier en francais, l'owner (nom et role), les ports de sortie (table, grain, colonnes cles et leur sens), le contrat ODCS de `contracts/` qui gouverne ses sources, les SLO (fraicheur 26 h pour un build nocturne a 2 h 30 plus marge, completude, disponibilite), les consommateurs declares (vues SupplySense, modules agents, exports), une question exemple pour l'assistant, la version et son changelog.

Ces declarations sont **vivantes** : le module `catalogue` de [supply-data-agents](https://github.com/adh-studio/supply-data-agents) les valide contre le JSON Schema, verifie les references croisees (le mart existe dans l'entrepot DuckDB, le contrat existe dans `contracts/`, les consommateurs sont connus) et calcule leur etat reel (fraicheur contre SLO via `etat_build.json`, volumes, statut du contrat, score de maturite). La vue **Catalogue** de SupplySense les expose en marketplace self-service.

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

## Regenerer les seeds depuis l'ERP reel (optionnel, local uniquement)

```bash
pip install "psycopg[binary]"
export ERP_DATABASE_URL="postgresql://user:motdepasse@hote:5432/erp"
python scripts/exporter_depuis_erp.py
.venv/bin/dbt seed --full-refresh && .venv/bin/dbt build
```

Sans `ERP_DATABASE_URL`, le script affiche une aide et sort proprement : la CI et le depot public n'utilisent que les donnees synthetiques.

## Ce que ce projet demontre pour un role de Product Owner Data et IA

- **Data products definis par le metier** : chaque mart repond a une question concrete de l'activite d'import (quelles references commander avant la rupture, quel fournisseur penalise la promesse client, quelle famille porte la marge), avec un grain explicite, des regles de gestion ecrites et des criteres d'acceptation traduits en tests dbt.
- **Qualite contractualisee** : les attentes sur les donnees (unicite, integrite referentielle, bornes des ratios, coherence receptions vs lots d'import) sont versionnees et verifiees a chaque build. Le dossier `contracts/` publie en plus 4 **contrats de donnees ODCS v3** (standard [Bitol](https://bitol.io)) sur les seeds : referentiel produits, stocks quotidiens (SLA de fraicheur), ventes et lots d'import, avec purpose, semantique des colonnes, regles de qualite, SLA et owner. Ces contrats sont vivants : le pipeline de [supply-data-agents](https://github.com/adh-studio/supply-data-agents) les valide AVANT chaque dbt build et refuse la publication a la moindre regle violee.
- **Documentation self-service** : le catalogue dbt (lineage, descriptions de colonnes, tests) est publie sur GitHub Pages et consultable sans outil supplementaire, premiere brique d'un catalogue de data products.
- **Domain-Driven Data** : la separation marts/supply et marts/offre reflete un decoupage par domaine metier, aligne avec une organisation Data Mesh ou chaque domaine possede ses produits.
- **Industrialisation** : pipeline reproductible de bout en bout (donnees synthetiques deterministes, dependances epinglees, CI sur chaque push) et chemin documente vers les donnees reelles de l'ERP, condition du passage a l'echelle.

## Structure du depot

```
scripts/generer_seeds.py        generation deterministe des donnees synthetiques
scripts/exporter_depuis_erp.py  export optionnel depuis la base PostgreSQL de l'ERP
seeds/                          CSV sources versionnes
contracts/                      contrats de donnees ODCS v3 (Bitol) des seeds
catalogue/                      declarations des data products (YAML + JSON Schema)
models/staging/                 vues de staging + tests
models/marts/supply/            data products supply + tests
models/marts/offre/             data products offre + tests
tests/generic/                  tests generiques personnalises
tests/                          test singulier
docs/                           site dbt docs pour GitHub Pages
run_e2e.sh                      test de bout en bout
.github/workflows/ci.yml        CI GitHub Actions
```
