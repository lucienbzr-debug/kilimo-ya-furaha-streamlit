# Ménages KYF : tableau de bord d'identification des bénéficiaires

Application Streamlit qui présente les résultats de l'identification des ménages bénéficiaires du projet **Kilimo ya Furaha** (Rikolto RDC), dans les territoires de Beni et Lubero (Nord-Kivu). La collecte a eu lieu du 15 juin au 14 septembre 2026 ; 1 963 ménages sont analysés.

## Contenu de l'application

| Page | Ce qu'elle montre |
| --- | --- |
| Vue d'ensemble | 10 indicateurs clés, ménages par groupement, statut, âge, durée depuis le retour, organisations |
| Vulnérabilité | Score de vulnérabilité (0 à 8), fréquence des critères, groupements et villages les plus exposés, synthèse par groupement |
| Production | Cultures, petit élevage, maraîchage, surfaces exploitées, 4 profils de production |
| Besoins | Freins selon le sexe du chef de ménage, activités pratiquées et jugées rentables, souhaits et motivations |
| Qualité des données | Alertes, collecte par jour, performance des enquêteurs (codés) |
| Méthode et données | Règles de traitement, protection des données, téléchargement de la sélection en CSV |

La barre latérale filtre toutes les pages par territoire, groupement, sexe, âge, statut, niveau de vulnérabilité et profil de production.

## Protection des données

Le fichier `data/menages_kyf.csv` est **anonymisé** : il ne contient ni nom, ni téléphone, ni coordonnée GPS, ni réponse libre, ni identifiant KoBo. Les enquêteurs sont codés (E01 à E21) et les villages de moins de 10 ménages sont regroupés sous « Autres villages ».

L'export KoBo brut et les fichiers intermédiaires restent en local : `data/raw/` et `data/interim/` sont exclus du dépôt par `.gitignore`. **Ne versionnez jamais la base nominative.**

## Lancer l'application en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows ; sous macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Mettre à jour les données

1. Placez le nouvel export KoBo (format Excel, avec libellés) dans `data/raw/`.
2. Nettoyez la base (produit `data/interim/`, non versionné) :
   ```bash
   pip install scikit-learn scipy openpyxl
   python scripts/nettoyage.py
   ```
3. Produisez l'export anonymisé utilisé par l'application :
   ```bash
   python scripts/preparer_donnees.py
   ```
4. Vérifiez que tout s'affiche, puis publiez :
   ```bash
   pip install pytest
   python -m pytest tests
   git add data/menages_kyf.csv && git commit -m "Mise à jour des données" && git push
   ```

## Déployer sur Streamlit Community Cloud

1. Poussez ce dépôt sur GitHub.
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io) avec votre compte GitHub.
3. Cliquez sur **Create app**, choisissez ce dépôt, la branche `main` et le fichier `streamlit_app.py`.
4. Cliquez sur **Deploy**. L'application se met à jour à chaque `git push`.

Un dépôt privé peut aussi être déployé ; dans ce cas, limitez l'accès à l'application depuis ses paramètres de partage sur Streamlit Community Cloud.

## Structure

```
streamlit_app.py        Point d'entrée : filtres et navigation
app_pages/              Une page par thème
lib/data.py             Chargement, libellés, calculs partagés
lib/charts.py           Graphiques Altair à la charte du projet
data/menages_kyf.csv    Données anonymisées (seul fichier de données versionné)
scripts/                Nettoyage de l'export KoBo et anonymisation
tests/                  Tests de fumée de toutes les pages
.streamlit/config.toml  Thème de l'application
```

## Méthode

- 4 fiches exclues faute de consentement ; 3 fiches d'une ancienne version du formulaire réintégrées.
- Groupements, villages et noms d'enquêteurs harmonisés.
- Taille du ménage = hommes + femmes + garçons + filles quand ce détail est rempli.
- Superficies supérieures à 5 ha considérées comme des erreurs de saisie.
- Score de vulnérabilité : 1 point par critère parmi 8 (femme cheffe de ménage, personne handicapée, pas de terre en propriété, retour depuis moins de 12 mois, 9 personnes ou plus, non membre d'une organisation, moins de 0,25 ha exploité, accueil de 2 ménages ou plus). Faible 0 à 2, modérée 3 à 4, élevée 5 et plus.
- Profils de production : classification k-means (4 classes) sur les cultures, l'élevage et l'accès à la terre.

Source : base KoBoToolbox « KILIMO YA FURAHA_RIKOLTO RDC », export du 30/09/2026.
