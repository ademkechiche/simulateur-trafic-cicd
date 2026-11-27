"""Fixtures de petits réseaux indépendants, recréées pour chaque test pytest."""

import pytest

from simulateur_trafic.models import Intersection, ReseauRoutier, Route


@pytest.fixture
def reseau():
    """Renvoie un réseau A -> B -> C avec deux routes de 100 m limitées à 36 km/h."""
    resultat = ReseauRoutier()
    for nom in ("A", "B", "C"):
        resultat.ajouter_intersection(Intersection(nom))
    resultat.ajouter_route(Route("AB", 100, 36, "A", "B"))
    resultat.ajouter_route(Route("BC", 100, 36, "B", "C"))
    return resultat


@pytest.fixture
def route_valide():
    """Une route indépendante et valide, réinitialisée entre tests."""
    return Route("TEST", 100.0, 50.0, "A", "B")


@pytest.fixture
def vehicule_valide():
    """Une voiture valide et indépendante, réinitialisée entre tests."""
    from simulateur_trafic.models.vehicule import Voiture
    return Voiture("V-TEST", vitesse=36.0, itineraire=["TEST"])
