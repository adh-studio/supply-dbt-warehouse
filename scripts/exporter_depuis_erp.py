#!/usr/bin/env python3
"""Export OPTIONNEL des tables de l'ERP reel vers les CSV de seeds.

Ce script n'est requis ni par les tests ni par la CI (il ne touche jamais au
reseau si ERP_DATABASE_URL n'est pas posee). Il permet, en local uniquement,
de regenerer les seeds de l'entrepot a partir de la base PostgreSQL de l'ERP
d'import/distribution (schema Prisma : ShipmentBatch, BatchItem, Product,
Order, OrderItem, StockMovement, SerialItem).

Correspondance ERP -> seeds :
  ShipmentBatch + BatchItem      -> commandes_achats.csv (une ligne par produit de lot)
  ShipmentBatch RECEIVED_TANA    -> receptions.csv
  Product / ProductVariant       -> produits.csv
  Order / OrderItem              -> ventes.csv
  StockMovement / SerialItem     -> stocks.csv (photo du stock a la date d'export)
  Fournisseurs des lots          -> fournisseurs.csv
  Sites de stockage              -> entrepots.csv (referentiel local, l'ERP
                                    etant mono-depot a ce jour)

Usage :
  export ERP_DATABASE_URL="postgresql://user:motdepasse@hote:5432/erp"
  python scripts/exporter_depuis_erp.py

Prerequis : pip install "psycopg[binary]"
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import date
from pathlib import Path

DOSSIER_SEEDS = Path(__file__).resolve().parent.parent / "seeds"

AIDE = """\
exporter_depuis_erp.py : la variable d'environnement ERP_DATABASE_URL n'est pas posee.

Ce script est optionnel : il regenere les CSV de seeds depuis la base
PostgreSQL de l'ERP reel. Sans ERP_DATABASE_URL, rien n'est exporte et les
seeds restent ceux generes par scripts/generer_seeds.py (donnees synthetiques
representatives, utilisees par la CI et le depot public).

Pour exporter depuis l'ERP :
  export ERP_DATABASE_URL="postgresql://user:motdepasse@hote:5432/erp"
  python scripts/exporter_depuis_erp.py
"""

# L'ERP est mono-depot a ce jour : le referentiel des sites reste local.
ENTREPOTS = [
    ("E01", "Depot central Ankorondrano", "Antananarivo", 1200, "central"),
    ("E02", "Boutique Analakely", "Antananarivo", 150, "boutique"),
    ("E03", "Boutique Behoririka", "Antananarivo", 120, "boutique"),
    ("E04", "Depot Tamatave", "Toamasina", 400, "depot_regional"),
]

# Delai de fret promis par mode (jours), a defaut de contrat par fournisseur dans l'ERP.
DELAI_PAR_MODE = {"AIR": 12, "SEA": 50}


def ecrire_csv(nom: str, entetes: list[str], lignes: list[tuple]) -> None:
    chemin = DOSSIER_SEEDS / nom
    with chemin.open("w", newline="", encoding="utf-8") as flux:
        ecrivain = csv.writer(flux)
        ecrivain.writerow(entetes)
        ecrivain.writerows(lignes)
    print(f"  {chemin.name} : {len(lignes)} lignes")


def exporter(url: str) -> int:
    try:
        import psycopg
    except ImportError:
        print(
            "Erreur : le driver PostgreSQL est absent.\n"
            'Installez-le avec : pip install "psycopg[binary]"',
            file=sys.stderr,
        )
        return 1

    DOSSIER_SEEDS.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(url) as cnx, cnx.cursor() as cur:
        print("Connexion ERP etablie, export vers", DOSSIER_SEEDS)

        # fournisseurs : fournisseurs distincts references sur les lots.
        cur.execute(
            """
            select distinct on (supplier)
                   supplier, "freightMode"::text
            from "ShipmentBatch"
            where supplier is not null and supplier <> ''
            order by supplier, "orderedAt" desc
            """
        )
        fournisseurs = []
        code_fournisseur: dict[str, str] = {}
        for i, (nom, mode) in enumerate(cur.fetchall(), start=1):
            code = f"F{i:03d}"
            code_fournisseur[nom] = code
            fournisseurs.append(
                (code, nom, "Chine", mode, DELAI_PAR_MODE.get(mode, 30), "B")
            )
        ecrire_csv(
            "fournisseurs.csv",
            ["id_fournisseur", "nom_fournisseur", "pays", "mode_fret",
             "delai_contractuel_jours", "note_rse"],
            fournisseurs,
        )

        # produits : catalogue actif, cout de revient moyen debarque par produit.
        cur.execute(
            """
            select p.sku, p.name, coalesce(p.category, 'Divers'),
                   coalesce((select b.supplier
                             from "BatchItem" bi
                             join "ShipmentBatch" b on b.id = bi."batchId"
                             where bi."productId" = p.id and b.supplier is not null
                             order by b."orderedAt" desc limit 1), ''),
                   coalesce((select round(avg(bi."landedCostMga"))
                             from "BatchItem" bi
                             where bi."productId" = p.id and bi."landedCostMga" > 0), 0),
                   p."sellingPriceMga"
            from "Product" p
            where p."isActive"
            order by p.sku
            """
        )
        produits = []
        code_produit: dict[str, str] = {}
        for i, (sku, nom, famille, fournisseur, prix_achat, prix_vente) in enumerate(
            cur.fetchall(), start=1
        ):
            code = f"P{i:04d}"
            code_produit[sku] = code
            produits.append(
                (code, nom, famille, code_fournisseur.get(fournisseur, "F001"),
                 int(prix_achat), int(prix_vente))
            )
        ecrire_csv(
            "produits.csv",
            ["id_produit", "nom_produit", "famille", "id_fournisseur",
             "prix_achat", "prix_vente"],
            produits,
        )

        ecrire_csv(
            "entrepots.csv",
            ["id_entrepot", "nom_entrepot", "ville", "capacite_m3", "type_entrepot"],
            ENTREPOTS,
        )

        # commandes_achats : une ligne par produit de lot (ShipmentBatch x BatchItem).
        cur.execute(
            """
            select b.reference, p.sku, coalesce(b.supplier, ''),
                   b."orderedAt"::date, bi.quantity,
                   b."transitStatus"::text, b."receivedAt"::date
            from "BatchItem" bi
            join "ShipmentBatch" b on b.id = bi."batchId"
            join "Product" p on p.id = bi."productId"
            order by b."orderedAt", b.reference, p.sku
            """
        )
        commandes, receptions = [], []
        numero_reception = 1
        for i, (ref, sku, fournisseur, date_commande, quantite, statut_erp, date_recue) in enumerate(
            cur.fetchall(), start=1
        ):
            id_commande = f"CA{i:04d}"
            statut = "recue" if statut_erp == "RECEIVED_TANA" else "en_cours"
            commandes.append(
                (id_commande, code_produit.get(sku, sku),
                 code_fournisseur.get(fournisseur, "F001"), "E01",
                 date_commande.isoformat(), quantite, statut)
            )
            if statut == "recue" and date_recue is not None:
                receptions.append(
                    (f"R{numero_reception:04d}", id_commande,
                     date_recue.isoformat(), quantite)
                )
                numero_reception += 1
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

        # stocks : photo a la date d'export (ledger StockMovement pour les
        # produits classiques, SerialItem IN_STOCK pour les serialises).
        cur.execute(
            """
            select p.sku,
                   case when p."isSerialized"
                        then (select count(*) from "SerialItem" s
                              where s."productId" = p.id and s.status = 'IN_STOCK')
                        else p."stockLevel"
                   end
            from "Product" p
            where p."isActive"
            order by p.sku
            """
        )
        aujourd_hui = date.today().isoformat()
        stocks = [
            (code_produit.get(sku, sku), "E01", aujourd_hui, max(0, int(quantite)))
            for sku, quantite in cur.fetchall()
        ]
        ecrire_csv(
            "stocks.csv",
            ["id_produit", "id_entrepot", "date_inventaire", "quantite_disponible"],
            stocks,
        )

        # ventes : lignes de commandes clients payees ou livrees.
        cur.execute(
            """
            select o.id, o."createdAt"::date, p.sku,
                   case when o."deliveryZone"::text = 'TANA_INTRA'
                        then 'magasin' else 'web' end,
                   oi.quantity, oi."sellingPriceMga"
            from "OrderItem" oi
            join "Order" o on o.id = oi."orderId"
            join "Product" p on p.id = oi."productId"
            order by o."createdAt", o.id
            """
        )
        ventes = [
            (f"V{i:05d}", date_vente.isoformat(), code_produit.get(sku, sku),
             "E01", canal, quantite, int(prix))
            for i, (_, date_vente, sku, canal, quantite, prix) in enumerate(
                cur.fetchall(), start=1
            )
        ]
        ecrire_csv(
            "ventes.csv",
            ["id_vente", "date_vente", "id_produit", "id_entrepot", "canal",
             "quantite", "prix_unitaire"],
            ventes,
        )

    print("Export termine. Relancez ensuite : dbt seed --full-refresh && dbt build")
    return 0


def principal() -> int:
    url = os.environ.get("ERP_DATABASE_URL", "").strip()
    if not url:
        print(AIDE)
        return 0
    return exporter(url)


if __name__ == "__main__":
    sys.exit(principal())
