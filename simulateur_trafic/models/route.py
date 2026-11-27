"""Modélise les routes à sens unique, leur occupation et les contraintes de circulation."""

from __future__ import annotations

from .vehicule import Vehicule
from .validation import nombre_fini
from .exceptions import RouteIndisponibleError


class Route:
    """Route à une voie et un sens ; position = avant du véhicule, espacement minimal 2 m."""

    def __init__(self, nom: str, longueur: float, limite_vitesse: float,
                 depart: str, arrivee: str, distance_securite: float = 2.0):
        """Initialise les attributs et vérifie les paramètres de construction.

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
        """
        if not isinstance(nom, str) or not nom.strip():
            raise ValueError("Un nom de route non vide est requis.")
        longueur = nombre_fini(longueur, "longueur", strict=True)
        limite_vitesse = nombre_fini(limite_vitesse, "limite_vitesse", strict=True)
        distance_securite = nombre_fini(distance_securite, "distance_securite")
        self.nom = nom
        self.longueur = float(longueur)
        self.limite_vitesse = float(limite_vitesse)
        self.depart = depart
        self.arrivee = arrivee
        self.distance_securite = float(distance_securite)
        self._vehicules: list[Vehicule] = []

    @property
    def vehicules(self) -> tuple[Vehicule, ...]:
        """Expose les véhicules présents sous forme de tuple non modifiable.

        Returns:
            tuple[Vehicule, ...]: Instantané de la collection de véhicules présents.
        """
        return tuple(self._vehicules)

    @property
    def taux_occupation(self) -> float:
        """Calcule la part de longueur occupée, espacement compris, plafonnée à un.

        Returns:
            float: Résultat de l’opération.
        """
        return min(1.0, sum(v.longueur + self.distance_securite for v in self._vehicules) / self.longueur)

    def peut_accueillir(self, vehicule: Vehicule) -> bool:
        """Vérifie que le véhicule est absent et que l’entrée est suffisamment dégagée.

        Args:
            vehicule (Vehicule): Véhicule concerné par l’opération.

        Returns:
            bool: True si l’entrée peut accueillir le véhicule.
        """
        if vehicule in self._vehicules:
            return False
        if not self._vehicules:
            return True
        premier = min(self._vehicules, key=lambda v: v.position)
        return premier.position >= premier.longueur + self.distance_securite

    def ajouter_vehicule(self, vehicule: Vehicule) -> None:
        """Ajoute un véhicule après validation de son itinéraire ou de la disponibilité de la route.

        Args:
            vehicule (Vehicule): Véhicule concerné par l’opération.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si le véhicule est déjà présent, l’entrée occupée ou l’itinéraire invalide.
        """
        if vehicule.route_actuelle is not None:
            raise ValueError("Retirer d'abord le véhicule de son ancienne route.")
        if not self.peut_accueillir(vehicule):
            raise RouteIndisponibleError(f"Entrée de {self.nom} occupée.")
        self._vehicules.append(vehicule)
        vehicule.route_actuelle = self
        vehicule.position = 0.0

    def retirer_vehicule(self, vehicule: Vehicule) -> None:
        """Retire le véhicule et efface sa référence vers la route actuelle.

        Args:
            vehicule (Vehicule): Véhicule concerné par l’opération.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si le véhicule n’est pas présent sur cette route.
        """
        self._vehicules.remove(vehicule)
        vehicule.route_actuelle = None

    def mettre_a_jour_vehicules(self, delta_t: float) -> None:
        """Fait avancer les véhicules de l’aval vers l’amont en maintenant l’espacement.

        Args:
            delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.

        Returns:
            None: Les objets concernés sont mis à jour ou le résultat est affiché.

        Raises:
            ValueError: Si la durée n’est pas finie ou strictement positive.
            TypeError: Si la durée n’est pas un réel.
        """
        delta_t = nombre_fini(delta_t, "delta_t", strict=True)
        precedent = None
        for vehicule in sorted(self._vehicules, key=lambda v: v.position, reverse=True):
            maximum = self.longueur
            if precedent is not None:
                maximum = precedent.position - precedent.longueur - self.distance_securite
            vehicule.avancer(delta_t, maximum)
            precedent = vehicule
