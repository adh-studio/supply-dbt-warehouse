{% docs __overview__ %}

# Entrepot analytique Offre et Supply

Entrepot dbt du domaine **Offre et Supply** d'une activite d'import et de
distribution de produits electroniques a Madagascar. Il transforme les
donnees operationnelles (fournisseurs de Chine et de Dubai, produits,
depots et boutiques, lots d'import AIR/SEA, arrivees apres douane, stocks,
ventes en ariary) en data products analytiques prets a consommer.

C'est la replique analytique de l'ERP de l'auteur : les lots d'import
(ShipmentBatch), les arrivees RECEIVED_TANA, les commandes clients
(Order/OrderItem) et le ledger de stock (StockMovement) y deviennent des
seeds, puis des marts testes et documentes.

## Architecture

- **seeds** : donnees sources synthetiques versionnees (CSV), representatives
  de l'activite reelle.
- **staging** : une vue par source, typage et renommage, aucune logique metier.
- **marts/supply** : couverture de stock, taux de rupture, delais d'import
  des fournisseurs et taux de service OTIF.
- **marts/offre** : marge et rotation par famille, classement top et flop produits.

## Regles de qualite

Chaque modele est couvert par des tests dbt : unicite et non nullite des cles,
valeurs acceptees, integrite referentielle, tests generiques personnalises
(valeurs positives, ratios bornes) et un test singulier de coherence entre
receptions et lots d'import.

{% enddocs %}
