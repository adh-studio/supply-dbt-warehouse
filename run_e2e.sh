#!/usr/bin/env bash
# Test de bout en bout : installation, dependances dbt, seeds, build complet.
# Echoue (code de sortie non nul) si un modele ou un test dbt echoue.
set -euo pipefail
cd "$(dirname "$0")"

# 1. Interpreteur Python (dbt supporte 3.11 a 3.13)
PYTHON_BIN=""
for candidat in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidat" >/dev/null 2>&1; then
        PYTHON_BIN="$candidat"
        break
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "Erreur : aucun interpreteur Python 3 trouve." >&2
    exit 1
fi
echo "==> Python utilise : $PYTHON_BIN ($($PYTHON_BIN --version))"

# 2. Environnement virtuel et dependances
if [ ! -x ".venv/bin/dbt" ]; then
    echo "==> Creation de l'environnement virtuel"
    "$PYTHON_BIN" -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -r requirements.txt
fi
export DBT_PROFILES_DIR="$PWD"

# 3. Seeds : generes uniquement si un CSV manque ou si REGENERER_SEEDS=1.
# Protection des saisies : les seeds sont desormais alimentes par la
# plateforme SupplyOps, les ecraser detruirait les saisies operationnelles.
SEEDS_ATTENDUS="produits fournisseurs entrepots commandes_achats receptions stocks ventes"
SEED_MANQUANT=0
for seed in $SEEDS_ATTENDUS; do
    if [ ! -f "seeds/${seed}.csv" ]; then
        SEED_MANQUANT=1
    fi
done
if [ "${REGENERER_SEEDS:-0}" = "1" ] || [ "$SEED_MANQUANT" = "1" ]; then
    echo "==> Generation des seeds (deterministe, graine fixe)"
    .venv/bin/python scripts/generer_seeds.py
else
    echo "==> Seeds existants conserves (REGENERER_SEEDS=1 pour forcer la regeneration)"
fi

# 4. Pipeline dbt complet (dbt deps seulement si le paquet n'est pas deja la,
# pour que les relances fonctionnent hors ligne)
if [ ! -d "dbt_packages/dbt_utils" ]; then
    echo "==> dbt deps"
    .venv/bin/dbt deps
fi
echo "==> dbt seed"
.venv/bin/dbt seed --full-refresh
echo "==> dbt build"
.venv/bin/dbt build

echo "==> Test e2e termine avec succes."
