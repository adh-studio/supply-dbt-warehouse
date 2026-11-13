#!/usr/bin/env python3
"""Generation deterministe des seeds CSV du domaine Offre et Supply.

Univers : enseigne francaise de decoration et d'ameublement.
Toutes les donnees sont synthetiques et reproductibles (graine fixe).

Usage : python scripts/generer_seeds.py
Sortie : fichiers CSV dans le dossier seeds/
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

GRAINE = 42
DOSSIER_SEEDS = Path(__file__).resolve().parent.parent / "seeds"

FOURNISSEURS = [
    ("F001", "Ateliers du Rhone", "France", 12, "A"),
    ("F002", "Manufacture de Porto", "Portugal", 18, "B"),
    ("F003", "Hanoi Rotin Collective", "Vietnam", 42, "B"),
    ("F004", "Jaipur Textiles", "Inde", 45, "C"),
    ("F005", "Meubles de Poznan", "Pologne", 15, "A"),
    ("F006", "Ceramiche di Faenza", "Italie", 21, "B"),
    ("F007", "Luminaires d'Anjou", "France", 10, "A"),
    ("F008", "Tissages de Flandre", "Belgique", 14, "B"),
]

# famille -> (prefixe de nom, liste de modeles, fourchette prix achat, coefficient de marge)
FAMILLES = {
    "Canapes et fauteuils": (
        ["Canape 3 places", "Canape d'angle", "Fauteuil", "Banquette", "Pouf"],
        ["Oslo", "Bergen", "Rivoli", "Luberon", "Cassis", "Vence"],
        (120.0, 480.0),
        (1.9, 2.4),
    ),
    "Luminaires": (
        ["Suspension", "Lampadaire", "Lampe a poser", "Applique", "Guirlande"],
        ["Luna", "Solstice", "Opale", "Brume", "Eclat", "Aurore"],
        (14.0, 95.0),
        (2.2, 2.9),
    ),
    "Arts de la table": (
        ["Assiette gres", "Service a the", "Carafe", "Set de couverts", "Saladier"],
        ["Faience", "Celadon", "Terracotta", "Jade", "Perle", "Safran"],
        (6.0, 48.0),
        (2.4, 3.1),
    ),
    "Tapis": (
        ["Tapis laine", "Tapis jute", "Tapis berbere", "Descente de lit", "Tapis d'exterieur"],
        ["Atlas", "Sahara", "Kilim", "Agadir", "Fes", "Taroudant"],
        (35.0, 240.0),
        (2.0, 2.6),
    ),
    "Rangement": (
        ["Etagere chene", "Buffet", "Console", "Bibliotheque", "Meuble TV"],
        ["Vendome", "Marais", "Bastille", "Odeon", "Passy", "Auteuil"],
        (60.0, 320.0),
        (1.8, 2.3),
    ),
    "Textile deco": (
        ["Housse de coussin", "Plaid", "Rideau lin", "Jete de canape", "Nappe brodee"],
        ["Camargue", "Sologne", "Ardeche", "Cevennes", "Correze", "Aubrac"],
        (4.0, 38.0),
        (2.5, 3.2),
    ),
}

ENTREPOTS = [
    ("E01", "Entrepot central Lille", "Lille", 48000, "central"),
    ("E02", "Plateforme Lyon Sud", "Lyon", 26000, "regional"),
    ("E03", "Plateforme Bordeaux Lac", "Bordeaux", 21000, "regional"),
    ("E04", "Plateforme Marseille Nord", "Marseille", 18000, "regional"),
]

DEBUT_COMMANDES = date(2026, 4, 1)
FIN_COMMANDES = date(2026, 10, 10)
DATES_INVENTAIRE = [date(2026, 6, 1) + timedelta(weeks=4 * i) for i in range(6)]
DEBUT_VENTES = date(2026, 5, 4)
FIN_VENTES = date(2026, 11, 8)


def ecrire_csv(nom: str, entetes: list[str], lignes: list[tuple]) -> None:
    chemin = DOSSIER_SEEDS / nom
    with chemin.open("w", newline="", encoding="utf-8") as flux:
        ecrivain = csv.writer(flux)
        ecrivain.writerow(entetes)
        ecrivain.writerows(lignes)
    print(f"  {chemin.name} : {len(lignes)} lignes")


def generer_produits(alea: random.Random) -> list[dict]:
    produits = []
    fournisseurs_par_famille = {
        "Canapes et fauteuils": ["F001", "F005"],
        "Luminaires": ["F007", "F003"],
        "Arts de la table": ["F006", "F002"],
        "Tapis": ["F004", "F003"],
        "Rangement": ["F005", "F001"],
        "Textile deco": ["F008", "F004"],
    }
    indice = 1
    for famille, (types, modeles, (p_min, p_max), (m_min, m_max)) in FAMILLES.items():
        combinaisons = [(t, m) for t in types for m in modeles]
        alea.shuffle(combinaisons)
        for type_produit, modele in combinaisons[:10]:
            prix_achat = round(alea.uniform(p_min, p_max), 2)
            prix_vente = round(prix_achat * alea.uniform(m_min, m_max), 2)
            produits.append(
                {
                    "id_produit": f"P{indice:04d}",
                    "nom_produit": f"{type_produit} {modele}",
                    "famille": famille,
                    "id_fournisseur": alea.choice(fournisseurs_par_famille[famille]),
                    "prix_achat": prix_achat,
                    "prix_vente": prix_vente,
                }
            )
            indice += 1
    return produits


def generer_commandes_et_receptions(
    alea: random.Random, produits: list[dict]
) -> tuple[list[tuple], list[tuple]]:
    delais = {f[0]: f[3] for f in FOURNISSEURS}
    commandes: list[tuple] = []
    receptions: list[tuple] = []
    plage_jours = (FIN_COMMANDES - DEBUT_COMMANDES).days
    numero_reception = 1
    for i in range(1, 161):
        produit = alea.choice(produits)
        id_commande = f"CA{i:04d}"
        id_fournisseur = produit["id_fournisseur"]
        id_entrepot = alea.choice(ENTREPOTS)[0]
        date_commande = DEBUT_COMMANDES + timedelta(days=alea.randrange(plage_jours + 1))
        quantite = alea.randrange(10, 121)
        delai_contractuel = delais[id_fournisseur]

        tirage = alea.random()
        if tirage < 0.08:
            statut = "en_cours"
        else:
            # Entre 1 et 2 receptions, jamais plus que la quantite commandee.
            retard = alea.choice([-3, -2, -1, 0, 0, 1, 2, 4, 7, 12])
            date_premiere = date_commande + timedelta(days=max(2, delai_contractuel + retard))
            if tirage < 0.80:
                quantite_recue = quantite
                receptions.append(
                    (f"R{numero_reception:04d}", id_commande, date_premiere.isoformat(), quantite_recue)
                )
                numero_reception += 1
                statut = "recue"
            else:
                premiere = max(1, int(quantite * alea.uniform(0.4, 0.8)))
                receptions.append(
                    (f"R{numero_reception:04d}", id_commande, date_premiere.isoformat(), premiere)
                )
                numero_reception += 1
                if alea.random() < 0.5:
                    solde = quantite - premiere
                    date_seconde = date_premiere + timedelta(days=alea.randrange(4, 15))
                    receptions.append(
                        (f"R{numero_reception:04d}", id_commande, date_seconde.isoformat(), solde)
                    )
                    numero_reception += 1
                    statut = "recue"
                else:
                    statut = "partielle"

        commandes.append(
            (id_commande, produit["id_produit"], id_fournisseur, id_entrepot,
             date_commande.isoformat(), quantite, statut)
        )
    return commandes, receptions


def generer_stocks(alea: random.Random, produits: list[dict]) -> tuple[list[tuple], dict]:
    stocks: list[tuple] = []
    implantations: dict[str, list[str]] = {}
    codes_entrepots = [e[0] for e in ENTREPOTS]
    for produit in produits:
        # Chaque produit est implante dans le central et un regional.
        regional = alea.choice(codes_entrepots[1:])
        implantations[produit["id_produit"]] = ["E01", regional]
        for id_entrepot in implantations[produit["id_produit"]]:
            base = alea.randrange(15, 220)
            for date_inventaire in DATES_INVENTAIRE:
                if alea.random() < 0.07:
                    quantite = 0  # rupture constatee a l'inventaire
                else:
                    quantite = max(0, int(base * alea.uniform(0.35, 1.25)))
                stocks.append(
                    (produit["id_produit"], id_entrepot, date_inventaire.isoformat(), quantite)
                )
    return stocks, implantations


def generer_ventes(
    alea: random.Random, produits: list[dict], implantations: dict
) -> list[tuple]:
    ventes: list[tuple] = []
    plage_jours = (FIN_VENTES - DEBUT_VENTES).days
    # Certains produits tournent beaucoup plus que d'autres (top et flop).
    poids = [alea.uniform(0.3, 1.0) ** 2 * 10 for _ in produits]
    for i in range(1, 751):
        produit = alea.choices(produits, weights=poids, k=1)[0]
        date_vente = DEBUT_VENTES + timedelta(days=alea.randrange(plage_jours + 1))
        canal = "web" if alea.random() < 0.35 else "magasin"
        quantite = alea.choices([1, 2, 3, 4, 6], weights=[55, 22, 12, 7, 4], k=1)[0]
        remise = alea.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.20])
        prix_unitaire = round(produit["prix_vente"] * (1 - remise), 2)
        ventes.append(
            (
                f"V{i:05d}",
                date_vente.isoformat(),
                produit["id_produit"],
                alea.choice(implantations[produit["id_produit"]]),
                canal,
                quantite,
                prix_unitaire,
            )
        )
    return ventes


def principal() -> None:
    alea = random.Random(GRAINE)
    DOSSIER_SEEDS.mkdir(parents=True, exist_ok=True)
    print("Generation des seeds dans", DOSSIER_SEEDS)

    ecrire_csv(
        "fournisseurs.csv",
        ["id_fournisseur", "nom_fournisseur", "pays", "delai_contractuel_jours", "note_rse"],
        [tuple(f) for f in FOURNISSEURS],
    )

    produits = generer_produits(alea)
    ecrire_csv(
        "produits.csv",
        ["id_produit", "nom_produit", "famille", "id_fournisseur", "prix_achat", "prix_vente"],
        [tuple(p.values()) for p in produits],
    )

    ecrire_csv(
        "entrepots.csv",
        ["id_entrepot", "nom_entrepot", "ville", "capacite_m3", "type_entrepot"],
        [tuple(e) for e in ENTREPOTS],
    )

    commandes, receptions = generer_commandes_et_receptions(alea, produits)
    ecrire_csv(
        "commandes_achats.csv",
        ["id_commande", "id_produit", "id_fournisseur", "id_entrepot",
         "date_commande", "quantite_commandee", "statut"],
        commandes,
    )
    ecrire_csv(
        "receptions.csv",
        ["id_reception", "id_commande", "date_reception", "quantite_recue"],
        receptions,
    )

    stocks, implantations = generer_stocks(alea, produits)
    ecrire_csv(
        "stocks.csv",
        ["id_produit", "id_entrepot", "date_inventaire", "quantite_disponible"],
        stocks,
    )

    ventes = generer_ventes(alea, produits, implantations)
    ecrire_csv(
        "ventes.csv",
        ["id_vente", "date_vente", "id_produit", "id_entrepot", "canal", "quantite", "prix_unitaire"],
        ventes,
    )

    print("Termine.")


if __name__ == "__main__":
    principal()
