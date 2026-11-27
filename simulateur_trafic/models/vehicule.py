"""Les distances sont en mètres, les durées en secondes, les vitesses en km/h."""

from __future__ import annotations

from typing import TYPE_CHECKING
from .validation import nombre_fini

if TYPE_CHECKING:
    from .route import Route


class Vehicule:
    """Véhicule générique suivant un itinéraire de routes à sens unique."""

    longueur = 4.5
    vitesse_maximale = 130.0

    def __init__(self, identifiant: str, vitesse: float = 50.0,
                 itineraire: list[str] | None = None, depart: float = 0.0):
        """Initialise les attributs et vérifie les paramètres de construction.

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
        """
        if not isinstance(identifiant, str) or not identifiant.strip():
            raise ValueError("Un identifiant texte non vide est requis.")
        vitesse = nombre_fini(vitesse, "vitesse", strict=True)
        depart = nombre_fini(depart, "depart")
        self.identifiant = identifiant
        self.vitesse_souhaitee = min(float(vitesse), self.vitesse_maximale)
        self.vitesse = 0.0
        self.position = 0.0
        self.route_actuelle: Route | None = None
        self.itineraire = list(itineraire or [])
        self.indice_route = 0
        self.depart_prevu = float(depart)
        self.heure_depart: float | None = None
        self.heure_arrivee: float | None = None
        self.distance_parcourue = 0.0

    @property
    def termine(self) -> bool:
        """Indique si une heure de sortie a été enregistrée.

        Returns:
            bool: Résultat de l’opération.
        """
        return self.heure_arrivee is not None

    @property
    def prochaine_route(self) -> str | None:
        """Renvoie le nom de la prochaine route de l’itinéraire ou None en fin de trajet.

        Returns:
            str | None: Résultat de l’opération.
        """
        indice = self.indice_route + 1
        return self.itineraire[indice] if indice < len(self.itineraire) else None

    @property
    def temps_parcours(self) -> float | None:
        """Renvoie la durée entre entrée effective et arrivée, ou None pour un trajet inachevé.

        Returns:
            float | None: Durée en secondes, ou None tant que le trajet n’est pas terminé.
        """
        if self.heure_depart is None or self.heure_arrivee is None:
            return None
        return self.heure_arrivee - self.heure_depart

    def avancer(self, delta_t: float, position_max: float | None = None) -> float:
        """Avance sans dépasser la route ni le véhicule précédent ; renvoie les mètres parcourus.

        Args:
            delta_t (float): Durée finie strictement positive du déplacement ou du tour, en secondes.
            position_max (float | None): Position maximale autorisée de l’avant du véhicule, en mètres ; None utilise le bout de route.

        Returns:
            float: Distance réellement parcourue pendant le pas, en mètres.

        Raises:
            ValueError: Si la durée ou une borne numérique est invalide.
            TypeError: Si un paramètre numérique n’est pas un réel.
        """
        delta_t = nombre_fini(delta_t, "delta_t", strict=True)
        if position_max is not None:
            position_max = nombre_fini(position_max, "position_max")
        if self.route_actuelle is None or self.termine:
            self.vitesse = 0.0
            return 0.0
        route = self.route_actuelle
        limite = min(route.longueur, position_max if position_max is not None else route.longueur)
        vitesse_libre = min(self.vitesse_souhaitee, route.limite_vitesse)
        distance = max(0.0, min(vitesse_libre / 3.6 * delta_t, limite - self.position))
        self.position += distance
        self.distance_parcourue += distance
        self.vitesse = distance / delta_t * 3.6
        return distance

    def changer_de_route(self, nouvelle_route: Route) -> bool:
        """Transfert atomique : si l'entrée est occupée, le véhicule reste sur sa route.

        Args:
            nouvelle_route (Route): Route suivante, connectée et conforme à l’itinéraire.

        Returns:
            bool: True si le transfert a eu lieu, False si la même route ou une entrée occupée le bloque.

        Raises:
            ValueError: Si le véhicule n’est pas au bout de la route ou si l’itinéraire est incohérent.
        """
        ancienne_route = self.route_actuelle
        if ancienne_route is nouvelle_route:
            return False
        if ancienne_route is None or self.position < ancienne_route.longueur - 1e-9:
            raise ValueError("Le véhicule doit atteindre le bout de sa route avant un transfert.")
        if self.prochaine_route != nouvelle_route.nom:
            raise ValueError("La nouvelle route ne correspond pas à l'itinéraire.")
        if ancienne_route is not None and ancienne_route.arrivee != nouvelle_route.depart:
            raise ValueError("Les deux routes ne sont pas connectées.")
        if not nouvelle_route.peut_accueillir(self):
            return False
        if ancienne_route is not None:
            ancienne_route.retirer_vehicule(self)
        nouvelle_route.ajouter_vehicule(self)
        self.indice_route += 1
        return True

    def __repr__(self) -> str:
        """Construit une représentation courte du véhicule pour le débogage.

        Returns:
            str: Représentation lisible du véhicule.
        """
        return f"{type(self).__name__}({self.identifiant!r}, position={self.position:.1f})"


class Voiture(Vehicule):
    """Véhicule léger de 4,5 m dont la vitesse souhaitée est plafonnée à 130 km/h."""
    longueur = 4.5
    vitesse_maximale = 130.0


class Camion(Vehicule):
    """Poids lourd de 12 m dont la vitesse souhaitée est plafonnée à 80 km/h."""
    longueur = 12.0
    vitesse_maximale = 80.0


class Bus(Vehicule):
    """Transport collectif de 12 m dont la vitesse souhaitée est plafonnée à 90 km/h."""
    longueur = 12.0
    vitesse_maximale = 90.0
