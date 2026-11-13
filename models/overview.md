{% docs __overview__ %}

# Entrepot analytique Offre et Supply

Entrepot dbt du domaine **Offre et Supply** d'une enseigne de decoration et
d'ameublement. Il transforme les donnees operationnelles (fournisseurs,
produits, entrepots, commandes d'achats, receptions, stocks, ventes) en
data products analytiques prets a consommer.

## Architecture

- **seeds** : donnees sources synthetiques versionnees (CSV).
- **staging** : une vue par source, typage et renommage, aucune logique metier.
- **marts/supply** : couverture de stock, taux de rupture, delais fournisseurs
  et taux de service OTIF.
- **marts/offre** : marge et rotation par famille, classement top et flop produits.

## Regles de qualite

Chaque modele est couvert par des tests dbt : unicite et non nullite des cles,
valeurs acceptees, integrite referentielle, tests generiques personnalises
(valeurs positives, ratios bornes) et un test singulier de coherence entre
receptions et commandes.

{% enddocs %}
