# Simulateur de trafic routier

Projet continu des TP1, TP2 et TP3 : conception orientée objet, simulation de circulation,
documentation, tests automatisés, couverture du code et optimisation. Python **3.10 ou supérieur** est requis.

## Structure du projet

Toutes les commandes s'exécutent depuis le dossier racine extrait `tp_python`.
Le code source existe dans un seul dossier `simulateur_trafic`.

```text
tp_python/
├── simulateur_trafic/              # Package Python
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── models/                     # Véhicules, routes, intersections, réseau
│   ├── core/                       # Simulation et statistiques
│   ├── out/                        # Affichage et exports
│   └── data/config_reseau.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_vehicule.py
│   ├── test_route.py
│   ├── test_simulation.py
│   ├── test_regressions_tp1.py
│   └── test_avances_tp3.py
├── docs/
│   ├── API.md
│   ├── anomalies_avant.txt
├── resultats/                     # Exports et rapports de tests
├── scripts/profilage_tp3.py      # Mesures cProfile, Cython et Numba
├── resultats_tp3/                 # Couverture, profil et benchmark
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
```

Les anciennes archives, copies d'installation et fichiers temporaires ne font
pas partie du projet livré. Les PNG et SVG sont deux formats graphiques ;
les CSV et JSON présentent des données complémentaires.

## Lancer la simulation

Sans installation de dépendances externes :

```powershell
python -m simulateur_trafic
```

Cette commande lance 60 tours de 60 secondes. Les graphiques SVG et les données
CSV/JSON sont écrits dans `resultats/` du dossier courant. Matplotlib, s'il est
disponible, ajoute les graphiques PNG.

```powershell
python -m simulateur_trafic --tours 120 --delta-t 30
python -m simulateur_trafic --sortie resultats_autre_scenario
python -m simulateur_trafic --afficher-chaque 1
python -m simulateur_trafic --sans-graphiques --silencieux
python -m simulateur_trafic --help
```

La configuration par défaut est localisée dans le package et ne dépend pas du
dossier du terminal. Une autre configuration se choisit avec `--config CHEMIN`.
Les chemins fournis sont relatifs au terminal ou absolus. Une relance remplace
les fichiers du dossier de sortie choisi.

## Installation et tests du TP2

```powershell
python -m pip install -e ".[test,graphiques]"
python -m pytest -v
python -m pytest tests/test_vehicule.py -v
python -m pytest -v --junitxml=resultats/rapport_tests.xml
```

L'option `test` installe pytest ; `graphiques` installe Matplotlib. Pour les tests
sans PNG, utiliser `python -m pip install -e ".[test]"`. Après installation,
la commande console `simulateur-trafic` est également disponible.

La suite du **TP2** comptait **70 cas** : véhicules (19), routes (16), simulation (23) et
régressions du TP1 (12). Avec les **17 cas supplémentaires du TP3**, la suite finale compte **87 tests**. Chaque cas paramétré compte séparément. Les fixtures
recréent les réseaux et isolent les fichiers temporaires.

Les tests initiaux restent exécutables sans pytest :

```powershell
python -m unittest discover -s tests -p test_regressions_tp1.py -v
```

Le bilan historique du TP2 et ses corrections figurent dans `resultats/rapport_tests.md` ; le bilan final du TP3 est dans `LIVRAISON.md`.
Le XML JUnit contient le détail de l'exécution. Le TP2 ne mesurait pas la couverture ; le TP3 mesure **78 %** au total.

## Scénario et modèle

`simulateur_trafic/data/config_reseau.json` décrit six intersections, six routes
orientées et 402 véhicules planifiés. Au carrefour C, les entrées nord et ouest
alternent toutes les 25 secondes. Une pointe de trafic commence à 900 secondes.

- `intersections` : identifiant, coordonnées et éventuellement phases, durée du
  feu vert et décalage du cycle. Une phase autorise une route entrante.
- `routes` : nom, longueur en mètres, vitesse limite en km/h, départ et arrivée.
- `vehicules` : identifiant, type, vitesse souhaitée, départ en secondes et
  itinéraire. `origine` et `destination` peuvent remplacer l'itinéraire pour
  utiliser Dijkstra, qui minimise le temps théorique à vitesse limite.
- `generations` : préfixe, nombre, début, intervalle et caractéristiques communes.
  Les départs sont planifiés au chargement, sans création infinie.

```json
{"identifiant": "V001", "type": "voiture", "vitesse": 50,
 "depart": 0, "itineraire": ["N_C", "C_E", "E_D"]}
```

Une route comporte une voie sans dépassement. La position représente l'avant du
véhicule. Les véhicules conservent un espacement minimal de 2 m et attendent si
le feu est rouge ou si la route suivante est occupée. Les départs futurs et les
véhicules bloqués avant entrée sont comptés « en attente ».

Chaque tour utilise des sous-pas d'au plus une seconde. Toutes les routes
avancent avant les transferts : aucun véhicule n'avance deux fois dans le même
sous-pas. Le temps restant au bout d'une route n'est pas reporté ; l'erreur peut
atteindre un sous-pas par franchissement. Le modèle ne représente pas les
accélérations, les voies multiples ou les conflits géométriques aux carrefours.

Les nombres doivent être réels et finis. Les longueurs, vitesses et durées sont
strictement positives ; les départs et espacements sont positifs ou nuls.
Les booléens, NaN et infinis sont refusés. Un transfert prématuré lève ValueError.

## Résultats et documentation

| Fichier dans resultats | Contenu |
| --- | --- |
| `resultats.json` | Bilan et historique détaillé par route |
| `historique.csv` | État global initial et à chaque fin de tour |
| `routes.csv` | Occupation et vitesses par route et par instant |
| `trajets.csv` | Départs, arrivées, distances et statuts individuels |
| `statistiques.svg` et `.png` | Effectifs, vitesses et congestions |
| `carte_reseau.svg` et `.png` | Réseau et sens de circulation |
| `rapport_tests.md` | Résultats des tests et anomalies corrigées |
| `rapport_tests.xml` | Rapport technique au format JUnit |

La vitesse instantanée concerne les véhicules actifs en fin de tour et vaut zéro
sur un réseau vide. La vitesse moyenne des trajets terminés utilise leur distance
cumulée divisée par leur durée cumulée. L'attente avant entrée est mesurée à part.
La congestion est signalée à 35 % d'occupation ou si au moins trois véhicules
roulent en moyenne sous 30 % de la limite. Ces seuils sont pédagogiques.

Les CSV utilisent la virgule et l'encodage UTF-8 avec BOM. La référence des classes et fonctions est dans `docs/API.md` ; les résultats TP3 et les consignes de remise sont dans `LIVRAISON.md`.

```python
from simulateur_trafic.core.simulateur import Simulateur

simulation = Simulateur()
bilan = simulation.lancer_simulation(n_tours=60, delta_t=60)
simulation.exporter("resultats")
```

## TP3 — Tests avancés, couverture et optimisation

- Fixtures supplémentaires dans `tests/conftest.py` : `route_valide`, `vehicule_valide`.
- Tests paramétrés et tests d'erreur dans `tests/test_avances_tp3.py`.
- Exceptions métier dans `simulateur_trafic/models/exceptions.py`.
- Optimisation des statistiques : une seule évaluation des vitesses moyennes par instantané.
- Profil cProfile et benchmarks Python/Numba/Cython : `python -m scripts.profilage_tp3`.

Installation des dépendances optionnelles :

```sh
python -m pip install pytest pytest-cov numpy numba Cython
python -m pytest --cov=simulateur_trafic --cov-report=term-missing --cov-report=html:resultats_tp3/htmlcov
python -m scripts.profilage_tp3
```

Les accélérations Numba et Cython sont démontrées dans un noyau numérique isolé ; elles ne remplacent pas la logique de déplacement du simulateur. La compilation initiale et les formats d'entrée impactent le temps observé.


Pour les commandes exactes sous Windows PowerShell, la compilation Cython et les fichiers à remettre, consulter [`LIVRAISON.md`](LIVRAISON.md).

## Distribution du package

- Nom de distribution : `adem_kechiche_traffic_simulator`
- Package importable : `simulateur_trafic`
- Version : `1.0.0`
- Auteur : Adem Kechiche
- Python minimum : 3.10
- Licence : MIT

### Installation depuis le wheel

```powershell
python -m pip install dist/adem_kechiche_traffic_simulator-1.0.0-py3-none-any.whl
```

### Exemple d’utilisation

```python
from simulateur_trafic.core.simulateur import Simulateur

simulation = Simulateur()
bilan = simulation.lancer_simulation(
    n_tours=60,
    delta_t=60,
    afficher=False
)

print("Véhicules terminés :", bilan["vehicules_termines"])
simulation.exporter("resultats_client", graphiques=False)
```

Cet exemple charge le réseau fourni, exécute une simulation,
affiche un résultat et exporte les données en CSV et JSON.