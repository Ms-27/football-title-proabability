# Football Title Probability - Ligue 1

Analyseur de probabilités de titre en Ligue 1 avec simulation Monte Carlo et analyse des calendriers restants.

## 🎯 Fonctionnalités

- **Analyse des probabilités de titre** entre deux équipes de Ligue 1
- **Simulation Monte Carlo** (jusqu'à 100 000 simulations)
- **Prise en compte des facteurs** :
  - Points actuels et matchs restants
  - Statistiques domicile/extérieur
  - Forme récente (8 derniers matchs)
  - Buts marqués/encaissés
  - Calendrier des adversaires restants
- **Interface flexible** pour comparer n'importe quelles équipes

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Comparaison avec données réelles (recommandé)

```bash
python3 compare_api.py "Paris SG" "Lens" 50000
python3 compare_api.py "Marseille" "Monaco" 50000
python3 compare_api.py "Lyon" "Nice" 30000
```

## 📁 Structure du projet

```
football-title-proabability/
├── compare_api.py          # Module principal avec API football-data.org
├── title_probability.py   # Simulation Monte Carlo
├── config.py              # Configuration
├── requirements.txt       # Dépendances
├── README.md              # Documentation
└── results/              # Résultats JSON
```

## 📊 Résultats

Les scripts génèrent :
- **Analyse détaillée** avec probabilités de titre
- **Visualisation graphique** avec barres de progression
- **Fichiers JSON** dans le dossier `results/`
- **Statistiques détaillées** (forme, buts, calendrier)

## 🏆 Exemple de sortie

```
=========================================================
COMPARAISON ÉQUIPES LIGUE 1 (API/DONNÉES RÉELLES)
=========================================================
Analyse: Paris SG vs Lens
Simulations: 50,000
=========================================================

Situation actuelle:
  Paris SG: 51 points (9 matchs restants)
  Lens: 52 points (9 matchs restants)

Probabilités de titre:
  Paris SG: 22.5%
  Lens: 76.9%
  Égalité: 0.5%

🏆 VAINQUEUR PRÉDIT: Lens
📊 Favori clair pour le titre
```

## 🎮 Équipes disponibles

- Paris SG
- Lens
- Marseille
- Monaco
- Lyon
- Lille
- Nice
- Rennes
- Bordeaux
- Strasbourg
- Montpellier
- Nantes
- Toulouse
- Clermont
- Reims
- Angers
- Brest
- Metz

## 🔧 Personnalisation

### Ajouter de nouvelles équipes

Dans `compare.py`, modifiez la fonction `get_sample_data()` :

```python
'Nouvelle_Equipe': {
    'name': 'Nouvelle Équipe',
    'matches_played': 20,
    'wins': 10,
    'draws': 5,
    'losses': 5,
    'goals_scored': 30,
    'goals_conceded': 25,
    'points': 35,
    # ... autres statistiques
}
```

### Ajuster les paramètres de simulation

- **Nombre de simulations** : `python3 compare.py "Equipe1" "Equipe2" 100000`
- **Facteurs de probabilité** : Modifier les poids dans `calculate_match_probability()`

## 📈 Méthodologie

1. **Collecte des données** : Statistiques actuelles des équipes
2. **Calcul de force** : Basé sur les performances domicile/extérieur
3. **Simulation Monte Carlo** : 10 000 à 100 000 scénarios possibles
4. **Analyse des calendriers** : Difficulté des matchs restants
5. **Calcul des probabilités** : Pourcentage de victoire au titre

## 📝 Notes

- Les données sont simulées pour la démonstration
- Le parsing web nécessite une connexion internet
- Les probabilités sont des estimations basées sur les statistiques
- Pour des données réelles, utilisez les URLs soccerstats.com

## 🔬 Détails techniques

- **Langage** : Python 3.12+
- **Bibliothèques** : numpy, requests, beautifulsoup4
- **Méthode** : Simulation Monte Carlo avec pondération des facteurs
- **Performance** : ~50 000 simulations en < 2 secondes