"""Construit le réseau routier et orchestre itinéraires, entrées, déplacements et sorties."""

from __future__ import annotations

import heapq
import json
from pathlib import Path

from .intersection import Intersection
from .route import Route
from .vehicule import Vehicule, Voiture, Camion, Bus
from .validation import nombre_fini
from .exceptions import RouteIndisponibleError, ConfigurationInvalideError


class ReseauRoutier:
    """Graphe orienté, calcul d'itinéraires et gestion des entrées/sorties."""

    def __init__(self):
        """Initialise les attributs et vérifie les paramètres de construction.

        Returns:
            None: L’instance est initialisée.
        """
        self.routes: dict[str, Route] = {}
        self.intersections: dict[str, Intersection] = {}
        self.vehicules: dict[str, Vehicule] = {}
        self.temps = 0.0

    def ajouter_intersection(self, intersection: Intersection) -> None:
        """Enregistre une intersection dont l’identifiant doit être unique.

        Args:
            intersection (Intersection): Intersection à enregistrer dans le réseau.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si l’identifiant existe déjà.
        """
        if intersection.identifiant in self.intersections:
            raise ValueError(f"Intersection dupliquée : {intersection.identifiant}")
        self.intersections[intersection.identifiant] = intersection

    def ajouter_route(self, route: Route) -> None:
        """Enregistre une route unique reliant deux intersections déjà connues.

        Args:
            route (Route): Route à enregistrer dans le réseau.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si le nom est dupliqué ou une intersection inconnue.
        """
        if route.nom in self.routes:
            raise ValueError(f"Route dupliquée : {route.nom}")
        if route.depart not in self.intersections or route.arrivee not in self.intersections:
            raise ValueError(f"Intersection inconnue pour {route.nom}.")
        self.routes[route.nom] = route

    def ajouter_vehicule(self, vehicule: Vehicule) -> None:
        """Ajoute un véhicule après validation de son itinéraire ou de la disponibilité de la route.

        Args:
            vehicule (Vehicule): Véhicule concerné par l’opération.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si le véhicule est déjà présent, l’entrée occupée ou l’itinéraire invalide.
        """
        if vehicule.identifiant in self.vehicules:
            raise ValueError(f"Véhicule dupliqué : {vehicule.identifiant}")
        if not vehicule.itineraire:
            raise ValueError("Un itinéraire non vide est requis.")
        for nom in vehicule.itineraire:
            if nom not in self.routes:
                raise RouteIndisponibleError(f"Route inconnue : {nom}")
        for nom_a, nom_b in zip(vehicule.itineraire, vehicule.itineraire[1:]):
            if self.routes[nom_a].arrivee != self.routes[nom_b].depart:
                raise ValueError(f"Itinéraire discontinu : {nom_a} -> {nom_b}")
        self.vehicules[vehicule.identifiant] = vehicule

    def plus_court_chemin(self, depart: str, arrivee: str) -> list[str]:
        """Dijkstra : minimise le temps théorique à vitesse limite, hors feux/congestion.

        Args:
            depart (str): Instant prévu de départ en secondes pour un véhicule, ou intersection de départ pour une route.
            arrivee (str): Identifiant de l’intersection d’arrivée.

        Returns:
            list[str]: Noms des routes du chemin le plus rapide ; liste vide si les deux nœuds sont identiques.

        Raises:
            ValueError: Si un nœud est inconnu ou si aucun chemin n’existe.
        """
        if depart not in self.intersections or arrivee not in self.intersections:
            raise ValueError("Intersection de départ ou d'arrivée inconnue.")
        file = [(0.0, depart, [])]
        visites = set()
        while file:
            cout, noeud, chemin = heapq.heappop(file)
            if noeud == arrivee:
                return chemin
            if noeud in visites:
                continue
            visites.add(noeud)
            for route in self.routes.values():
                if route.depart == noeud and route.arrivee not in visites:
                    duree = route.longueur / (route.limite_vitesse / 3.6)
                    heapq.heappush(file, (cout + duree, route.arrivee, chemin + [route.nom]))
        raise ValueError(f"Aucun chemin de {depart} vers {arrivee}.")

    @classmethod
    def depuis_json(cls, fichier: str | Path) -> ReseauRoutier:
        """Charge, valide et construit le réseau et les départs planifiés depuis un fichier JSON.

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
        """
        try:
            with Path(fichier).open(encoding="utf-8") as flux:
                config = json.load(flux)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Configuration introuvable : {fichier}") from exc
        except json.JSONDecodeError:
            raise  # Compatibilité avec les tests du TP2.
        except UnicodeDecodeError as exc:
            raise ConfigurationInvalideError(f"Encodage de configuration invalide : {fichier}") from exc
        reseau = cls()
        for donnees in config.get("intersections", []):
            reseau.ajouter_intersection(Intersection(**donnees))
        for donnees in config.get("routes", []):
            reseau.ajouter_route(Route(**donnees))
        if not reseau.routes:
            raise ValueError("La configuration doit contenir au moins une route.")
        for intersection in reseau.intersections.values():
            for nom in intersection.phases:
                if nom not in reseau.routes or reseau.routes[nom].arrivee != intersection.identifiant:
                    raise ValueError(f"Phase de feu invalide : {nom}")
        types = {"voiture": Voiture, "camion": Camion, "bus": Bus, "vehicule": Vehicule}

        def creer(donnees: dict) -> None:
            """Construit et enregistre un véhicule depuis un dictionnaire de configuration.

            Args:
                donnees (dict): Dictionnaire des caractéristiques d’un véhicule.

            Returns:
                None: Les objets concernés sont mis à jour ou le résultat est affiché.

            Raises:
                ValueError: Si le type ou l’itinéraire du véhicule est invalide.
                KeyError: Si une caractéristique requise manque.
            """
            donnees = dict(donnees)
            type_vehicule = donnees.pop("type", "voiture")
            if type_vehicule not in types:
                raise ValueError(f"Type de véhicule inconnu : {type_vehicule}")
            if "itineraire" not in donnees:
                origine = donnees.pop("origine")
                destination = donnees.pop("destination")
                donnees["itineraire"] = reseau.plus_court_chemin(origine, destination)
            reseau.ajouter_vehicule(types[type_vehicule](**donnees))

        for donnees in config.get("vehicules", []):
            creer(donnees)
        for generation in config.get("generations", []):
            nombre = generation["nombre"]
            intervalle = nombre_fini(generation["intervalle"], "intervalle")
            debut = nombre_fini(generation.get("debut", 0), "debut")
            if isinstance(nombre, bool) or not isinstance(nombre, int) or nombre < 0:
                raise ValueError("Nombre entier positif ou nul et intervalle positif ou nul requis.")
            for i in range(nombre):
                creer({**generation["vehicule"],
                       "identifiant": f"{generation['prefixe']}_{i + 1:03d}",
                       "depart": debut + i * intervalle})
        return reseau

    def injecter_vehicules(self) -> None:
        """Insère les véhicules éligibles dans l’ordre des départs si l’entrée est libre.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.
        """
        candidats = sorted(self.vehicules.values(), key=lambda v: (v.depart_prevu, v.identifiant))
        for vehicule in candidats:
            if vehicule.heure_depart is None and vehicule.depart_prevu <= self.temps + 1e-9:
                route = self.routes[vehicule.itineraire[0]]
                if route.peut_accueillir(vehicule):
                    route.ajouter_vehicule(vehicule)
                    vehicule.heure_depart = self.temps

    def avancer(self, delta_t: float) -> None:
        """Sous-pas d'au plus une seconde, pour limiter l'erreur aux intersections.

Toutes les routes avancent avant les transferts : aucun véhicule ne se
déplace deux fois pendant un même sous-pas.

        Args:
            delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.

        Returns:
            None: Le réseau et son temps courant sont mis à jour sur place.

        Raises:
            ValueError: Si la durée ou une borne numérique est invalide.
            TypeError: Si un paramètre numérique n’est pas un réel.
        """
        delta_t = nombre_fini(delta_t, "delta_t", strict=True)
        cible = self.temps + delta_t
        # Un feu partagé par plusieurs intersections n'avance qu'une seule fois.
        feux = {
            id(intersection.traffic_light): intersection.traffic_light
            for intersection in self.intersections.values()
            if intersection.traffic_light is not None
        }
        while self.temps < cible - 1e-9:
            self.injecter_vehicules()
            pas = min(1.0, cible - self.temps)
            # Respecter aussi les transitions plus courtes qu'une seconde.
            for feu in feux.values():
                durees = {"RED": feu.red_duration, "GREEN": feu.green_duration,
                          "ORANGE": feu.orange_duration}
                pas = min(pas, durees[feu.state] - feu.timer)
            for route in self.routes.values():
                route.mettre_a_jour_vehicules(pas)
            fin_pas = self.temps + pas
            for vehicule in self.vehicules.values():
                route = vehicule.route_actuelle
                if route is None or vehicule.position < route.longueur - 1e-9:
                    continue
                intersection = self.intersections[route.arrivee]
                feu = intersection.traffic_light
                # Le feu contrôle aussi une sortie à la fin de l'itinéraire.
                if feu is not None and not feu.can_pass():
                    vehicule.vitesse = 0.0
                    continue
                if vehicule.prochaine_route is None:
                    route.retirer_vehicule(vehicule)
                    vehicule.heure_arrivee = fin_pas
                    vehicule.vitesse = 0.0
                elif intersection.autorise(route.nom, self.temps):
                    vehicule.changer_de_route(self.routes[vehicule.prochaine_route])
                else:
                    vehicule.vitesse = 0.0
            # Les véhicules ont été traités avec l'état du début du sous-pas.
            for feu in feux.values():
                feu.update(pas)
            self.temps = fin_pas

    def etat(self) -> dict:
        """Compte les véhicules actifs, terminés et en attente à l’instant courant.

        Returns:
            dict: Temps en secondes et nombres de véhicules par statut.
        """
        actifs = sum(v.route_actuelle is not None for v in self.vehicules.values())
        termines = sum(v.termine for v in self.vehicules.values())
        return {"temps_s": self.temps, "vehicules_actifs": actifs,
                "vehicules_termines": termines,
                "vehicules_en_attente": len(self.vehicules) - actifs - termines}
