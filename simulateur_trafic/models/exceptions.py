"""Exceptions métier spécialisées du simulateur de trafic."""


class ErreurSimulation(ValueError):
    """Erreur de cohérence ou de validation de la simulation."""


class RouteIndisponibleError(ErreurSimulation):
    """Une route est saturée, inconnue ou indisponible pour le véhicule."""


class ConfigurationInvalideError(ErreurSimulation):
    """Un fichier de configuration est illisible ou contient des données invalides."""
