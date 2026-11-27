"""Modélise les intersections et les phases déterministes des feux de circulation."""

from dataclasses import dataclass, field
from math import isfinite
from .validation import nombre_fini


@dataclass
class Intersection:
    """Carrefour dont les phases autorisent successivement une route entrante.

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
    """

    identifiant: str
    x: float = 0.0
    y: float = 0.0
    phases: list[str] = field(default_factory=list)
    duree_vert: float = 20.0
    decalage: float = 0.0

    def __post_init__(self) -> None:
        """Valide les paramètres du feu et les coordonnées après création de la dataclass.

        Returns:
            None: Les valeurs validées sont conservées.

        Raises:
            ValueError: Si l’identifiant est vide ou un nombre non fini ou hors borne.
            TypeError: Si un paramètre numérique n’est pas un réel.
        """
        if not self.identifiant:
            raise ValueError("Identifiant requis.")
        self.duree_vert = nombre_fini(self.duree_vert, "duree_vert", strict=True)
        for nom in ("x", "y", "decalage"):
            valeur = getattr(self, nom)
            if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
                raise TypeError(f"{nom} doit être un réel.")
            if not isfinite(valeur):
                raise ValueError(f"{nom} doit être fini.")

    def autorise(self, route_entrante: str, temps: float) -> bool:
        """Exécute une opération du simulateur.

        Args:
            route_entrante (str): Nom de la route dont le feu est interrogé.
            temps (float): Instant de simulation exprimé en secondes.

        Returns:
            bool: Résultat de l’opération.
        """
        if not self.phases:
            return True
        indice = int((temps + self.decalage) // self.duree_vert) % len(self.phases)
        return route_entrante == self.phases[indice]
