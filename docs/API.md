# Référence du package simulateur_trafic

Les distances sont exprimées en mètres, les temps en secondes et les vitesses en km/h. Les descriptions suivantes sont extraites des docstrings du code livré.

## __init__.py

TP Python : modélisation et simulation d'un réseau routier intelligent.

## __main__.py

Permet le lancement du package avec python -m simulateur_trafic.

## core/__init__.py

Moteur de simulation et calcul des statistiques.

## core/analyseur.py

Calcule les statistiques instantanées et les indicateurs cumulés des trajets.

### Analyseur

Statistiques instantanées et cumulées, sans modifier le réseau.

#### Analyseur.__init__

```python
__init__(self, reseau: ReseauRoutier)
```

Initialise les attributs et vérifie les paramètres de construction.

Args:
    reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

Returns:
    None: L’instance est initialisée.

#### Analyseur.vitesses_moyennes

```python
vitesses_moyennes(self)
```

Calcule la moyenne arithmétique des vitesses réelles sur chaque route.

Returns:
    dict[str, float]: Vitesse moyenne en km/h par nom de route ; zéro sur une route vide.

#### Analyseur.zones_congestion

```python
zones_congestion(self)
```

Congestion si occupation >= 35 % ou >= 3 véhicules à moins de 30 % de la limite.

Returns:
    list[str]: Noms des routes satisfaisant les seuils de congestion.

#### Analyseur.temps_parcours

```python
temps_parcours(self)
```

Renvoie la durée entre entrée effective et arrivée, ou None pour un trajet inachevé.

Returns:
    dict[str, float]: Durées en secondes des seuls trajets achevés.

#### Analyseur.instantane

```python
instantane(self)
```

Rassemble l’état courant du réseau et les statistiques de chaque route.

Returns:
    dict: État global, statistiques par route et zones de congestion.

#### Analyseur.bilan

```python
bilan(self)
```

Rassemble le bilan final, les distances, les temps de parcours et l’attente à l’entrée.

Returns:
    dict: Indicateurs instantanés et cumulés ; None pour les moyennes de trajets non disponibles.

## core/simulateur.py

Exécute les tours de simulation et coordonne analyse, affichage et exports.

### Simulateur

Coordonne la configuration, la boucle temporelle, l’historique et les exports.

#### Simulateur.__init__

```python
__init__(self, fichier_config: str | Path | None=None, reseau: ReseauRoutier | None=None)
```

Initialise les attributs et vérifie les paramètres de construction.

Args:
    fichier_config (str | Path | None): Chemin JSON ; None sélectionne la configuration fournie avec le package.
    reseau (ReseauRoutier | None): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

Returns:
    None: L’instance est initialisée.

Raises:
    ValueError: Si une valeur métier ne respecte pas les bornes ou les contraintes.
    TypeError: Si un paramètre numérique n’est pas un réel.

#### Simulateur.lancer_simulation

```python
lancer_simulation(self, n_tours: int=60, delta_t: float=60, afficher: bool=True, afficher_chaque: int=10)
```

Exécute les tours demandés, mémorise chaque état et renvoie le bilan.

Args:
    n_tours (int): Nombre entier positif ou nul de tours supplémentaires à exécuter.
    delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.
    afficher (bool): Active l’affichage console des états et du bilan.
    afficher_chaque (int): Fréquence entière strictement positive d’affichage, exprimée en tours.

Returns:
    dict: Bilan du réseau après les tours demandés.

Raises:
    ValueError: Si les tours, la durée ou la fréquence sont invalides.
    TypeError: Si la durée n’est pas un réel.

#### Simulateur.exporter

```python
exporter(self, dossier: str | Path, graphiques: bool=True)
```

Crée le dossier de sortie et exporte le bilan, les historiques et les graphiques demandés.

Args:
    dossier (str | Path): Dossier de destination ; créé si nécessaire.
    graphiques (bool): Active les graphiques SVG et les PNG si Matplotlib est disponible.

Returns:
    list[Path]: Chemins des fichiers effectivement écrits.

Raises:
    OSError: Si le dossier ou un fichier de sortie ne peut pas être écrit.

## main.py

Point d'entrée : python -m simulateur_trafic ou python simulateur_trafic/main.py.

### main

Analyse les arguments CLI, exécute la simulation et produit les fichiers de résultats.

Returns:
    int: Zéro en cas de succès ; argparse provoque SystemExit en cas d’erreur.

## models/__init__.py

Expose les classes métier du réseau routier et des véhicules.

## models/intersection.py

Modélise les intersections et les phases déterministes des feux de circulation.

### Intersection

Carrefour dont les phases autorisent successivement une route entrante.

Args:
    identifiant (str): Identifiant unique et non vide du carrefour.
    x (float): Abscisse finie sur la carte schématique.
    y (float): Ordonnée finie sur la carte schématique.
    phases (list[str]): Routes entrantes autorisées successivement ; vide pour un passage libre.
    duree_vert (float): Durée finie strictement positive de chaque phase, en secondes.
    decalage (float): Décalage fini du cycle en secondes, éventuellement négatif.

Raises:
    ValueError: Si l'identifiant est vide ou une valeur numérique non finie ou hors borne.
    TypeError: Si un paramètre numérique n'est pas un réel.

#### Intersection.__post_init__

```python
__post_init__(self)
```

Valide les paramètres du feu et les coordonnées après création de la dataclass.

Returns:
    None: Les valeurs validées sont conservées.

Raises:
    ValueError: Si l’identifiant est vide ou un nombre non fini ou hors borne.
    TypeError: Si un paramètre numérique n’est pas un réel.

#### Intersection.autorise

```python
autorise(self, route_entrante: str, temps: float)
```

Exécute une opération du simulateur.

Args:
    route_entrante (str): Nom de la route dont le feu est interrogé.
    temps (float): Instant de simulation exprimé en secondes.

Returns:
    bool: Résultat de l’opération.

## models/reseau.py

Construit le réseau routier et orchestre itinéraires, entrées, déplacements et sorties.

### ReseauRoutier

Graphe orienté, calcul d'itinéraires et gestion des entrées/sorties.

#### ReseauRoutier.__init__

```python
__init__(self)
```

Initialise les attributs et vérifie les paramètres de construction.

Returns:
    None: L’instance est initialisée.

#### ReseauRoutier.ajouter_intersection

```python
ajouter_intersection(self, intersection: Intersection)
```

Enregistre une intersection dont l’identifiant doit être unique.

Args:
    intersection (Intersection): Intersection à enregistrer dans le réseau.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si l’identifiant existe déjà.

#### ReseauRoutier.ajouter_route

```python
ajouter_route(self, route: Route)
```

Enregistre une route unique reliant deux intersections déjà connues.

Args:
    route (Route): Route à enregistrer dans le réseau.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si le nom est dupliqué ou une intersection inconnue.

#### ReseauRoutier.ajouter_vehicule

```python
ajouter_vehicule(self, vehicule: Vehicule)
```

Ajoute un véhicule après validation de son itinéraire ou de la disponibilité de la route.

Args:
    vehicule (Vehicule): Véhicule concerné par l’opération.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si le véhicule est déjà présent, l’entrée occupée ou l’itinéraire invalide.

#### ReseauRoutier.plus_court_chemin

```python
plus_court_chemin(self, depart: str, arrivee: str)
```

Dijkstra : minimise le temps théorique à vitesse limite, hors feux/congestion.

Args:
    depart (str): Instant prévu de départ en secondes pour un véhicule, ou intersection de départ pour une route.
    arrivee (str): Identifiant de l’intersection d’arrivée.

Returns:
    list[str]: Noms des routes du chemin le plus rapide ; liste vide si les deux nœuds sont identiques.

Raises:
    ValueError: Si un nœud est inconnu ou si aucun chemin n’existe.

#### ReseauRoutier.depuis_json

```python
depuis_json(cls, fichier: str | Path)
```

Charge, valide et construit le réseau et les départs planifiés depuis un fichier JSON.

Args:
    fichier (str | Path): Chemin du fichier JSON de configuration.

Returns:
    ReseauRoutier: Réseau construit, avec véhicules planifiés mais non encore injectés.

Raises:
    OSError: Si le fichier ne peut pas être lu.
    json.JSONDecodeError: Si le contenu n’est pas du JSON valide.
    ValueError: Si les contraintes du réseau ou des véhicules ne sont pas respectées.
    KeyError: Si une clé requise manque.
    TypeError: Si une donnée a un type incompatible.

#### ReseauRoutier.injecter_vehicules

```python
injecter_vehicules(self)
```

Insère les véhicules éligibles dans l’ordre des départs si l’entrée est libre.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

#### ReseauRoutier.avancer

```python
avancer(self, delta_t: float)
```

Sous-pas d'au plus une seconde, pour limiter l'erreur aux intersections.

Toutes les routes avancent avant les transferts : aucun véhicule ne se
déplace deux fois pendant un même sous-pas.

        Args:
            delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.

        Returns:
            None: Le réseau et son temps courant sont mis à jour sur place.

        Raises:
            ValueError: Si la durée ou une borne numérique est invalide.
            TypeError: Si un paramètre numérique n’est pas un réel.
        

#### ReseauRoutier.etat

```python
etat(self)
```

Compte les véhicules actifs, terminés et en attente à l’instant courant.

Returns:
    dict: Temps en secondes et nombres de véhicules par statut.

## models/route.py

Modélise les routes à sens unique, leur occupation et les contraintes de circulation.

### Route

Route à une voie et un sens ; position = avant du véhicule, espacement minimal 2 m.

#### Route.__init__

```python
__init__(self, nom: str, longueur: float, limite_vitesse: float, depart: str, arrivee: str, distance_securite: float=2.0)
```

Initialise les attributs et vérifie les paramètres de construction.

Args:
    nom (str): Nom unique de la route.
    longueur (float): Longueur finie strictement positive de la route, en mètres.
    limite_vitesse (float): Vitesse maximale autorisée sur la route, en km/h.
    depart (str): Instant prévu de départ en secondes pour un véhicule, ou intersection de départ pour une route.
    arrivee (str): Identifiant de l’intersection d’arrivée.
    distance_securite (float): Espacement minimal positif ou nul entre deux véhicules, en mètres.

Returns:
    None: L’instance est initialisée.

Raises:
    ValueError: Si une valeur métier ne respecte pas les bornes ou les contraintes.
    TypeError: Si un paramètre numérique n’est pas un réel.

#### Route.vehicules

```python
vehicules(self)
```

Expose les véhicules présents sous forme de tuple non modifiable.

Returns:
    tuple[Vehicule, ...]: Instantané de la collection de véhicules présents.

#### Route.taux_occupation

```python
taux_occupation(self)
```

Calcule la part de longueur occupée, espacement compris, plafonnée à un.

Returns:
    float: Résultat de l’opération.

#### Route.peut_accueillir

```python
peut_accueillir(self, vehicule: Vehicule)
```

Vérifie que le véhicule est absent et que l’entrée est suffisamment dégagée.

Args:
    vehicule (Vehicule): Véhicule concerné par l’opération.

Returns:
    bool: True si l’entrée peut accueillir le véhicule.

#### Route.ajouter_vehicule

```python
ajouter_vehicule(self, vehicule: Vehicule)
```

Ajoute un véhicule après validation de son itinéraire ou de la disponibilité de la route.

Args:
    vehicule (Vehicule): Véhicule concerné par l’opération.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si le véhicule est déjà présent, l’entrée occupée ou l’itinéraire invalide.

#### Route.retirer_vehicule

```python
retirer_vehicule(self, vehicule: Vehicule)
```

Retire le véhicule et efface sa référence vers la route actuelle.

Args:
    vehicule (Vehicule): Véhicule concerné par l’opération.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si le véhicule n’est pas présent sur cette route.

#### Route.mettre_a_jour_vehicules

```python
mettre_a_jour_vehicules(self, delta_t: float)
```

Fait avancer les véhicules de l’aval vers l’amont en maintenant l’espacement.

Args:
    delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

Raises:
    ValueError: Si la durée n’est pas finie ou strictement positive.
    TypeError: Si la durée n’est pas un réel.

## models/validation.py

Validation commune des nombres réels finis et des identifiants métier.

### nombre_fini

Convertit un réel fini respectant une borne en float.

Args:
    valeur (float): Nombre à valider ; les booléens sont refusés.
    nom (str): Nom du paramètre affiché dans l'erreur.
    minimum (float): Borne inférieure autorisée.
    strict (bool): Si vrai, exclut la borne inférieure.

Returns:
    float: Valeur finie validée.

Raises:
    TypeError: Si la valeur n'est pas un réel ou est un booléen.
    ValueError: Si la valeur est infinie, NaN ou hors de la borne.

## models/vehicule.py

Les distances sont en mètres, les durées en secondes, les vitesses en km/h.

### Vehicule

Véhicule générique suivant un itinéraire de routes à sens unique.

#### Vehicule.__init__

```python
__init__(self, identifiant: str, vitesse: float=50.0, itineraire: list[str] | None=None, depart: float=0.0)
```

Initialise les attributs et vérifie les paramètres de construction.

Args:
    identifiant (str): Identifiant texte non vide du véhicule ou de l’intersection.
    vitesse (float): Vitesse souhaitée strictement positive en km/h.
    itineraire (list[str] | None): Noms successifs des routes ; copie de la liste fournie.
    depart (float): Instant prévu de départ en secondes pour un véhicule, ou intersection de départ pour une route.

Returns:
    None: L’instance est initialisée.

Raises:
    ValueError: Si une valeur métier ne respecte pas les bornes ou les contraintes.
    TypeError: Si un paramètre numérique n’est pas un réel.

#### Vehicule.termine

```python
termine(self)
```

Indique si une heure de sortie a été enregistrée.

Returns:
    bool: Résultat de l’opération.

#### Vehicule.prochaine_route

```python
prochaine_route(self)
```

Renvoie le nom de la prochaine route de l’itinéraire ou None en fin de trajet.

Returns:
    str | None: Résultat de l’opération.

#### Vehicule.temps_parcours

```python
temps_parcours(self)
```

Renvoie la durée entre entrée effective et arrivée, ou None pour un trajet inachevé.

Returns:
    float | None: Durée en secondes, ou None tant que le trajet n’est pas terminé.

#### Vehicule.avancer

```python
avancer(self, delta_t: float, position_max: float | None=None)
```

Avance sans dépasser la route ni le véhicule précédent ; renvoie les mètres parcourus.

Args:
    delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.
    position_max (float | None): Position maximale autorisée de l’avant du véhicule, en mètres ; None utilise le bout de route.

Returns:
    float: Distance réellement parcourue pendant le pas, en mètres.

Raises:
    ValueError: Si la durée ou une borne numérique est invalide.
    TypeError: Si un paramètre numérique n’est pas un réel.

#### Vehicule.changer_de_route

```python
changer_de_route(self, nouvelle_route: Route)
```

Transfert atomique : si l'entrée est occupée, le véhicule reste sur sa route.

Args:
    nouvelle_route (Route): Route suivante, connectée et conforme à l’itinéraire.

Returns:
    bool: True si le transfert a eu lieu, False si la même route ou une entrée occupée le bloque.

Raises:
    ValueError: Si le véhicule n’est pas au bout de la route ou si l’itinéraire est incohérent.

#### Vehicule.__repr__

```python
__repr__(self)
```

Construit une représentation courte du véhicule pour le débogage.

Returns:
    str: Représentation lisible du véhicule.

### Voiture

Véhicule léger de 4,5 m dont la vitesse souhaitée est plafonnée à 130 km/h.

### Camion

Poids lourd de 12 m dont la vitesse souhaitée est plafonnée à 80 km/h.

### Bus

Transport collectif de 12 m dont la vitesse souhaitée est plafonnée à 90 km/h.

## out/__init__.py

Affichage console, graphiques et exports de données.

## out/affichage.py

Affiche les états console et produit les graphiques SVG ou PNG et la carte.

### Affichage

Regroupe l’affichage console et la génération des représentations graphiques.

#### Affichage.afficher_etat

```python
afficher_etat(etat: dict)
```

Affiche une ligne résumant le trafic à un instant donné.

Args:
    etat (dict): Dictionnaire des statistiques instantanées.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

#### Affichage.afficher_bilan

```python
afficher_bilan(bilan: dict)
```

Affiche les indicateurs de durée, de distance, de parcours et d’attente.

Args:
    bilan (dict): Dictionnaire des indicateurs cumulés à exporter ou à afficher.

Returns:
    None: Les objets concernés sont mis à jour ou le résultat est affiché.

#### Affichage.generer_graphiques

```python
generer_graphiques(historique: list[dict], reseau: ReseauRoutier, dossier: Path)
```

SVG sans dépendance ; deux PNG supplémentaires si matplotlib est installé.

Args:
    historique (list[dict]): Liste chronologique des instantanés de statistiques.
    reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.
    dossier (Path): Dossier de destination ; créé si nécessaire.

Returns:
    list[Path]: Deux SVG et, si Matplotlib est disponible, deux PNG.

Raises:
    OSError: Si un fichier de sortie ne peut pas être écrit.

#### Affichage._courbes_svg

```python
_courbes_svg(historique: list[dict], fichier: Path)
```

Écrit trois courbes SVG à partir des états observés, sans dépendance externe.

Args:
    historique (list[dict]): Liste chronologique des instantanés de statistiques.
    fichier (Path): Chemin du fichier JSON de configuration.

Returns:
    Path: Chemin du graphique SVG créé.

Raises:
    OSError: Si le fichier ne peut pas être écrit.

#### Affichage._carte_svg

```python
_carte_svg(reseau: ReseauRoutier, fichier: Path)
```

Écrit une carte SVG schématique des routes et des intersections.

Args:
    reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.
    fichier (Path): Chemin du fichier JSON de configuration.

Returns:
    Path: Chemin de la carte SVG créée.

Raises:
    OSError: Si le fichier ne peut pas être écrit.

## out/export.py

Exporte les états, le bilan et les trajets aux formats JSON et CSV.

### Export

Regroupe les écritures de données JSON et CSV.

#### Export.sauvegarder

```python
sauvegarder(dossier: Path, historique: list[dict], bilan: dict, reseau: ReseauRoutier)
```

Écrit les quatre fichiers resultats.json, historique.csv, routes.csv et trajets.csv.

Args:
    dossier (Path): Dossier de destination ; créé si nécessaire.
    historique (list[dict]): Liste chronologique des instantanés de statistiques.
    bilan (dict): Dictionnaire des indicateurs cumulés à exporter ou à afficher.
    reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

Returns:
    list[Path]: Chemins des quatre fichiers de données créés.

Raises:
    OSError: Si un fichier ne peut pas être écrit.
