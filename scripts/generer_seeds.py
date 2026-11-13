#!/usr/bin/env python3
"""Generation deterministe des seeds CSV du domaine Offre et Supply.

Univers : import et distribution de produits electroniques a Madagascar.
Replique analytique de l'ERP de l'auteur (lots d'import Chine -> Tana,
fret AIR ou SEA, douane, depots et boutiques d'Antananarivo et Tamatave).
Montants en ariary (MGA). Toutes les donnees sont synthetiques et
reproductibles (graine fixe) ; en local, scripts/exporter_depuis_erp.py
peut regenerer les memes CSV depuis la base PostgreSQL de l'ERP reel.

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

# id, nom, pays, mode_fret (AIR ~10-15 j, SEA ~40-55 j), delai_contractuel_jours, note_rse
# delai_contractuel_jours = delai de fret promis entre la commande du lot et
# l'arrivee RECEIVED_TANA (douane comprise, selon le contrat transitaire).
FOURNISSEURS = [
    ("F001", "Shenzhen Gametech Electronics", "Chine", "AIR", 12, "B"),
    ("F002", "Guangzhou Audio Factory", "Chine", "AIR", 14, "B"),
    ("F003", "Huaqiangbei Digital Trading", "Chine", "AIR", 10, "C"),
    ("F004", "Yiwu Smart Accessories", "Chine", "SEA", 45, "B"),
    ("F005", "Dongguan LED Technologies", "Chine", "SEA", 50, "C"),
    ("F006", "Guangzhou Home Appliances Co", "Chine", "SEA", 55, "B"),
    ("F007", "Shenzhen Wearables Lab", "Chine", "AIR", 15, "A"),
    ("F008", "Dubai Electronics Hub", "Emirats arabes unis", "AIR", 12, "A"),
]

# Catalogue explicite : (nom, famille, id_fournisseur, prix_achat (cout de
# revient debarque, MGA), prix_vente (MGA), poids_vente, profil_stock).
# poids_vente pilote la frequence de vente ; profil_stock force des situations
# parlantes : rupture (produits qui tournent), surstock (paris rates),
# dormant (accessoires d'un modele depasse), normal sinon.
PRODUITS_CATALOGUE = [
    # Consoles et gaming (marges console ~30 %, accessoires plus genereuses)
    ("Console PS5 Slim 1To", "Consoles et gaming", "F001", 2450000, 3490000, 9.0, "rupture"),
    ("Console PS5 Digital", "Consoles et gaming", "F001", 2090000, 2990000, 6.0, "normal"),
    ("Manette DualSense blanche", "Consoles et gaming", "F001", 240000, 390000, 10.0, "rupture"),
    ("Manette Xbox sans fil", "Consoles et gaming", "F008", 230000, 370000, 4.0, "normal"),
    ("Casque gaming RGB", "Consoles et gaming", "F001", 95000, 180000, 5.0, "normal"),
    ("Console retro portable 520 jeux", "Consoles et gaming", "F003", 60000, 125000, 4.0, "normal"),
    ("Tapis de souris XXL RGB", "Consoles et gaming", "F003", 25000, 55000, 2.0, "normal"),
    # Audio
    ("Ecouteurs TWS Pro reduction de bruit", "Audio", "F003", 75000, 155000, 10.0, "rupture"),
    ("Ecouteurs TWS Sport", "Audio", "F003", 55000, 110000, 7.0, "normal"),
    ("Enceinte Bluetooth 20W etanche", "Audio", "F002", 90000, 175000, 6.0, "normal"),
    ("Enceinte karaoke mobile avec micros", "Audio", "F002", 280000, 490000, 3.0, "normal"),
    ("Barre de son TV 80W", "Audio", "F002", 220000, 390000, 2.5, "normal"),
    ("Casque Bluetooth supra-aural", "Audio", "F003", 85000, 165000, 4.0, "normal"),
    ("Micro cravate sans fil", "Audio", "F002", 45000, 95000, 3.0, "normal"),
    # Telephonie et accessoires
    ("Chargeur GaN 65W double USB-C", "Telephonie et accessoires", "F004", 38000, 85000, 10.0, "rupture"),
    ("Powerbank 20000 mAh charge rapide", "Telephonie et accessoires", "F004", 70000, 145000, 8.0, "normal"),
    ("Cable USB-C tresse 1m", "Telephonie et accessoires", "F004", 8000, 20000, 6.0, "normal"),
    ("Coque silicone iPhone 15", "Telephonie et accessoires", "F008", 9000, 25000, 5.0, "normal"),
    ("Verre trempe 9H universel", "Telephonie et accessoires", "F004", 4000, 12000, 5.0, "normal"),
    ("Support telephone voiture magnetique", "Telephonie et accessoires", "F004", 18000, 40000, 3.0, "normal"),
    ("Coque Tecno Spark 8", "Telephonie et accessoires", "F004", 7000, 18000, 0.0, "dormant"),
    # Montres connectees
    ("Montre connectee Serie 9 AMOLED", "Montres connectees", "F007", 95000, 190000, 8.0, "normal"),
    ("Montre connectee ronde acier", "Montres connectees", "F007", 120000, 230000, 4.0, "normal"),
    ("Montre GPS sport multisport", "Montres connectees", "F007", 180000, 330000, 3.0, "normal"),
    ("Bracelet connecte fitness", "Montres connectees", "F007", 45000, 95000, 5.0, "normal"),
    ("Bracelet silicone 22mm", "Montres connectees", "F007", 6000, 16000, 2.0, "normal"),
    ("Montre connectee enfant GPS", "Montres connectees", "F008", 85000, 170000, 4.0, "normal"),
    ("Chargeur magnetique montre", "Montres connectees", "F007", 12000, 28000, 0.0, "dormant"),
    # Eclairage LED (paris rates -> surstock)
    ("Ruban LED RGB 5m telecommande", "Eclairage LED", "F005", 22000, 50000, 5.0, "normal"),
    ("Lampe sunset fantaisie", "Eclairage LED", "F005", 28000, 62000, 1.0, "surstock"),
    ("Lampe lune 3D 18cm", "Eclairage LED", "F005", 35000, 78000, 1.0, "surstock"),
    ("Projecteur galaxie etoiles", "Eclairage LED", "F005", 65000, 135000, 3.0, "normal"),
    ("Guirlande LED exterieur 10m", "Eclairage LED", "F005", 30000, 65000, 3.0, "normal"),
    ("Ampoule connectee WiFi", "Eclairage LED", "F005", 18000, 42000, 2.5, "normal"),
    ("Lampadaire LED salon", "Eclairage LED", "F005", 140000, 265000, 2.0, "normal"),
    # Electromenager
    ("Friteuse a air 5L", "Electromenager", "F006", 240000, 420000, 7.0, "normal"),
    ("Bouilloire electrique inox 1.8L", "Electromenager", "F006", 55000, 105000, 5.0, "normal"),
    ("Blender mixeur 2L 1000W", "Electromenager", "F006", 95000, 175000, 4.0, "normal"),
    ("Fer a repasser vapeur", "Electromenager", "F006", 60000, 115000, 3.0, "normal"),
    ("Ventilateur sur pied silencieux", "Electromenager", "F006", 110000, 205000, 4.0, "normal"),
    ("Machine a cafe expresso 15 bars", "Electromenager", "F006", 320000, 560000, 2.0, "normal"),
    ("Mini refrigerateur 45L", "Electromenager", "F006", 480000, 795000, 1.0, "normal"),
]

# id, nom, ville, capacite_m3, type_entrepot
ENTREPOTS = [
    ("E01", "Depot central Ankorondrano", "Antananarivo", 1200, "central"),
    ("E02", "Boutique Analakely", "Antananarivo", 150, "boutique"),
    ("E03", "Boutique Behoririka", "Antananarivo", 120, "boutique"),
    ("E04", "Depot Tamatave", "Toamasina", 400, "depot_regional"),
]

DEBUT_COMMANDES = date(2026, 4, 1)
FIN_COMMANDES = date(2026, 10, 10)
DATES_INVENTAIRE = [date(2026, 6, 1) + timedelta(weeks=4 * i) for i in range(6)]
DEBUT_VENTES = date(2026, 5, 4)
FIN_VENTES = date(2026, 11, 8)

# Retards de fret et de douane constates par rapport au delai promis
# (dedouanement CUSTOMS_CLEARING qui traine, vols annules, congestion du port
# de Tamatave). Tolerance OTIF : +2 jours.
RETARDS_AIR = [-2, -1, 0, 0, 1, 1, 2, 2, 4, 7, 12]
RETARDS_SEA = [-4, -2, -1, 0, 1, 2, 2, 5, 9, 14, 24]


def ecrire_csv(nom: str, entetes: list[str], lignes: list[tuple]) -> None:
    chemin = DOSSIER_SEEDS / nom
    with chemin.open("w", newline="", encoding="utf-8") as flux:
        ecrivain = csv.writer(flux)
        ecrivain.writerow(entetes)
        ecrivain.writerows(lignes)
    print(f"  {chemin.name} : {len(lignes)} lignes")


def generer_produits() -> list[dict]:
    produits = []
    for indice, (nom, famille, id_fournisseur, prix_achat, prix_vente, poids, profil) in enumerate(
        PRODUITS_CATALOGUE, start=1
    ):
        produits.append(
            {
                "id_produit": f"P{indice:04d}",
                "nom_produit": nom,
                "famille": famille,
                "id_fournisseur": id_fournisseur,
                "prix_achat": prix_achat,
                "prix_vente": prix_vente,
                "poids_vente": poids,
                "profil_stock": profil,
            }
        )
    return produits


def quantite_lot(alea: random.Random, prix_achat: int) -> int:
    """Taille de lot realiste selon la valeur unitaire du produit."""
    if prix_achat >= 1_000_000:
        return alea.randrange(4, 16)
    if prix_achat >= 100_000:
        return alea.randrange(10, 41)
    return alea.randrange(20, 121)


def generer_commandes_et_receptions(
    alea: random.Random, produits: list[dict]
) -> tuple[list[tuple], list[tuple]]:
    delais = {f[0]: f[4] for f in FOURNISSEURS}
    modes = {f[0]: f[3] for f in FOURNISSEURS}
    commandes: list[tuple] = []
    receptions: list[tuple] = []
    plage_jours = (FIN_COMMANDES - DEBUT_COMMANDES).days
    numero_reception = 1
    for i in range(1, 161):
        produit = alea.choice(produits)
        id_commande = f"CA{i:04d}"
        id_fournisseur = produit["id_fournisseur"]
        mode_fret = modes[id_fournisseur]
        # Les lots AIR atterrissent a Ivato (depot central) ; les lots SEA
        # debarquent au port de Tamatave et sont parfois stockes sur place.
        if mode_fret == "SEA":
            id_entrepot = "E04" if alea.random() < 0.45 else "E01"
        else:
            id_entrepot = "E01"
        date_commande = DEBUT_COMMANDES + timedelta(days=alea.randrange(plage_jours + 1))
        quantite = quantite_lot(alea, produit["prix_achat"])
        delai_contractuel = delais[id_fournisseur]

        tirage = alea.random()
        if tirage < 0.08:
            statut = "en_cours"  # lot encore SOURCING / IN_TRANSIT / CUSTOMS_CLEARING
        else:
            # Entre 1 et 2 receptions RECEIVED_TANA, jamais plus que la quantite commandee.
            retard = alea.choice(RETARDS_SEA if mode_fret == "SEA" else RETARDS_AIR)
            date_premiere = date_commande + timedelta(days=max(2, delai_contractuel + retard))
            if tirage < 0.84:
                quantite_recue = quantite
                receptions.append(
                    (f"R{numero_reception:04d}", id_commande, date_premiere.isoformat(), quantite_recue)
                )
                numero_reception += 1
                statut = "recue"
            else:
                # Lot splitte : une partie bloquee en douane ou reexpediee.
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


def generer_implantations(alea: random.Random, produits: list[dict]) -> dict[str, list[str]]:
    """Chaque produit est stocke au depot central, dans une boutique de Tana,
    et parfois au depot de Tamatave."""
    implantations: dict[str, list[str]] = {}
    for produit in produits:
        sites = ["E01", alea.choice(["E02", "E03"])]
        if alea.random() < 0.30:
            sites.append("E04")
        implantations[produit["id_produit"]] = sites
    return implantations


def generer_ventes(
    alea: random.Random, produits: list[dict], implantations: dict
) -> list[tuple]:
    ventes: list[tuple] = []
    plage_jours = (FIN_VENTES - DEBUT_VENTES).days
    vendables = [p for p in produits if p["poids_vente"] > 0]
    poids = [p["poids_vente"] for p in vendables]
    for i in range(1, 751):
        produit = alea.choices(vendables, weights=poids, k=1)[0]
        date_vente = DEBUT_VENTES + timedelta(days=alea.randrange(plage_jours + 1))
        # web = commande en ligne livree sur Tana, magasin = vente boutique.
        canal = "web" if alea.random() < 0.35 else "magasin"
        quantite = alea.choices([1, 2, 3, 4, 5], weights=[72, 18, 6, 3, 1], k=1)[0]
        remise = alea.choice([0.0, 0.0, 0.0, 0.0, 0.05, 0.10])
        prix_unitaire = int(round(produit["prix_vente"] * (1 - remise) / 500) * 500)
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


def generer_stocks(
    alea: random.Random,
    produits: list[dict],
    implantations: dict,
    ventes: list[tuple],
) -> list[tuple]:
    """Inventaires mensuels par produit x site, calibres sur les ventes reelles
    des 90 derniers jours pour produire des situations parlantes :
    ruptures sur les produits qui tournent, surstock sur les paris rates,
    stock dormant sur les accessoires depasses."""
    date_seuil_90j = (FIN_VENTES - timedelta(days=90)).isoformat()
    ventes_90j: dict[tuple[str, str], int] = {}
    for (_, date_vente, id_produit, id_entrepot, _, quantite, _) in ventes:
        if date_vente > date_seuil_90j:
            cle = (id_produit, id_entrepot)
            ventes_90j[cle] = ventes_90j.get(cle, 0) + quantite

    stocks: list[tuple] = []
    derniere_date = DATES_INVENTAIRE[-1]
    for produit in produits:
        profil = produit["profil_stock"]
        for id_entrepot in implantations[produit["id_produit"]]:
            vente_jour = ventes_90j.get((produit["id_produit"], id_entrepot), 0) / 90.0
            if profil == "dormant":
                stock_final = alea.randrange(12, 45)
            elif profil == "rupture":
                stock_final = 0  # rupture constatee au dernier inventaire
            elif profil == "surstock":
                stock_final = max(25, int(vente_jour * alea.uniform(120, 200)) + alea.randrange(20, 60))
            else:
                # Couverture cible saine (18 a 50 jours), plancher pour les
                # produits a faible rotation locale.
                stock_final = max(2, int(vente_jour * alea.uniform(18, 50)))

            for date_inventaire in DATES_INVENTAIRE:
                if date_inventaire == derniere_date:
                    quantite = stock_final
                elif profil == "rupture" and alea.random() < 0.30:
                    quantite = 0  # ruptures recurrentes avant reassort
                elif profil != "rupture" and alea.random() < 0.05:
                    quantite = 0  # rupture ponctuelle constatee a l'inventaire
                else:
                    base = max(stock_final, int(vente_jour * 30) + 4)
                    quantite = max(0, int(base * alea.uniform(0.5, 1.4)))
                stocks.append(
                    (produit["id_produit"], id_entrepot, date_inventaire.isoformat(), quantite)
                )
    return stocks


def principal() -> None:
    alea = random.Random(GRAINE)
    DOSSIER_SEEDS.mkdir(parents=True, exist_ok=True)
    print("Generation des seeds dans", DOSSIER_SEEDS)

    ecrire_csv(
        "fournisseurs.csv",
        ["id_fournisseur", "nom_fournisseur", "pays", "mode_fret",
         "delai_contractuel_jours", "note_rse"],
        [tuple(f) for f in FOURNISSEURS],
    )

    produits = generer_produits()
    ecrire_csv(
        "produits.csv",
        ["id_produit", "nom_produit", "famille", "id_fournisseur", "prix_achat", "prix_vente"],
        [
            (p["id_produit"], p["nom_produit"], p["famille"], p["id_fournisseur"],
             p["prix_achat"], p["prix_vente"])
            for p in produits
        ],
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

    implantations = generer_implantations(alea, produits)
    ventes = generer_ventes(alea, produits, implantations)
    stocks = generer_stocks(alea, produits, implantations, ventes)
    ecrire_csv(
        "stocks.csv",
        ["id_produit", "id_entrepot", "date_inventaire", "quantite_disponible"],
        stocks,
    )
    ecrire_csv(
        "ventes.csv",
        ["id_vente", "date_vente", "id_produit", "id_entrepot", "canal", "quantite", "prix_unitaire"],
        ventes,
    )

    print("Termine.")


if __name__ == "__main__":
    principal()
