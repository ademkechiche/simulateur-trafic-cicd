"""Calcule les statistiques instantanées et les indicateurs cumulés des trajets."""

from statistics import mean

from ..models.reseau import ReseauRoutier


class Analyseur:
    """Statistiques instantanées et cumulées, sans modifier le réseau."""

    def __init__(self, reseau: ReseauRoutier):
        """Initialise les attributs et vérifie les paramètres de construction.

        Args:
            reseau (ReseauRoutier): Réseau à analyser ou à simuler ; remplace le chargement depuis un fichier.

        Returns:
            None: L’instance est initialisée.
        """
        self.reseau = reseau

    def vitesses_moyennes(self) -> dict[str, float]:
        """Calcule la moyenne arithmétique des vitesses réelles sur chaque route.

        Returns:
            dict[str, float]: Vitesse moyenne en km/h par nom de route ; zéro sur une route vide.
        """
        return {nom: mean(v.vitesse for v in route.vehicules) if route.vehicules else 0.0
                for nom, route in self.reseau.routes.items()}

    def zones_congestion(self) -> list[str]:
        """Congestion si occupation >= 35 % ou >= 3 véhicules à moins de 30 % de la limite.

        Returns:
            list[str]: Noms des routes satisfaisant les seuils de congestion.
        """
        moyennes = self.vitesses_moyennes()
        return [nom for nom, route in self.reseau.routes.items()
                if route.taux_occupation >= 0.35
                or (len(route.vehicules) >= 3 and moyennes[nom] < route.limite_vitesse * 0.3)]

    def temps_parcours(self) -> dict[str, float]:
        """Renvoie la durée entre entrée effective et arrivée, ou None pour un trajet inachevé.

        Returns:
            dict[str, float]: Durées en secondes des seuls trajets achevés.
        """
        return {v.identifiant: v.temps_parcours for v in self.reseau.vehicules.values()
                if v.temps_parcours is not None}

    def instantane(self) -> dict:
        """Rassemble l’état courant du réseau et les statistiques de chaque route.

        Returns:
            dict: État global, statistiques par route et zones de congestion.
        """
        actifs = [v for v in self.reseau.vehicules.values() if v.route_actuelle is not None]
        temps = list(self.temps_parcours().values())
        moyennes_routes = self.vitesses_moyennes()  # Calcul unique par instantané.
        return {**self.reseau.etat(),
                "vitesse_moyenne_kmh": mean(v.vitesse for v in actifs) if actifs else 0.0,
                "temps_parcours_moyen_s": mean(temps) if temps else None,
                "zones_congestion": self.zones_congestion(),
                "routes": {nom: {"nombre_vehicules": len(route.vehicules),
                                 "vitesse_moyenne_kmh": moyennes_routes[nom],
                                 "taux_occupation": route.taux_occupation}
                           for nom, route in self.reseau.routes.items()}}

    def bilan(self) -> dict:
        """Rassemble le bilan final, les distances, les temps de parcours et l’attente à l’entrée.

        Returns:
            dict: Indicateurs instantanés et cumulés ; None pour les moyennes de trajets non disponibles.
        """
        termines = [v for v in self.reseau.vehicules.values() if v.termine]
        distance = sum(v.distance_parcourue for v in termines)
        duree = sum(v.temps_parcours for v in termines)
        attente = [v.heure_depart - v.depart_prevu for v in self.reseau.vehicules.values()
                   if v.heure_depart is not None]
        return {**self.instantane(), "nombre_vehicules_total": len(self.reseau.vehicules),
                "distance_totale_m": sum(v.distance_parcourue for v in self.reseau.vehicules.values()),
                "vitesse_moyenne_trajets_kmh": distance / duree * 3.6 if duree else None,
                "attente_entree_moyenne_s": mean(attente) if attente else None,
                "temps_parcours_s": self.temps_parcours()}
