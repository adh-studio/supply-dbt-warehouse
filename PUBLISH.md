# Publication sur GitHub

Commandes a executer depuis la racine du projet.

## 1. Creer le depot et pousser

```bash
gh repo create supply-dbt-warehouse --public \
  --description "Entrepot analytique dbt + DuckDB du domaine Offre et Supply d'une enseigne de decoration : data products testes, documentes, CI GitHub Actions" \
  --source . --push
```

## 2. Activer GitHub Pages (source : branche main, dossier /docs)

```bash
gh api repos/adh-studio/supply-dbt-warehouse/pages \
  --method POST \
  -f "source[branch]=main" -f "source[path]=/docs"
```

## 3. Verifier

- CI : https://github.com/adh-studio/supply-dbt-warehouse/actions
- Documentation (quelques minutes apres l'activation) : https://adh-studio.github.io/supply-dbt-warehouse/
