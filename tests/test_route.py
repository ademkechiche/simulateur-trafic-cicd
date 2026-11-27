"""Validation des routes, gestion des véhicules et espacement minimal."""

import pytest

from simulateur_trafic.models import Route, Vehicule


@pytest.mark.parametrize("longueur", [0, -10, float("nan"), float("inf")])
def test_longueur_invalide(longueur):
    with pytest.raises(ValueError):
        Route("AB", longueur, 50, "A", "B")


@pytest.mark.parametrize("vitesse", [0, -10, float("nan"), float("inf")])
def test_limite_invalide(vitesse):
    with pytest.raises(ValueError):
        Route("AB", 100, vitesse, "A", "B")


@pytest.mark.parametrize("espacement", [-1, float("nan"), float("inf")])
def test_espacement_invalide(espacement):
    with pytest.raises(ValueError):
        Route("AB", 100, 50, "A", "B", espacement)


def test_route_vide(reseau):
    route = reseau.routes["AB"]
    route.mettre_a_jour_vehicules(1)
    assert route.vehicules == ()
    assert route.taux_occupation == 0


def test_entree_occupee(reseau):
    route = reseau.routes["AB"]
    a, b = Vehicule("A"), Vehicule("B")
    route.ajouter_vehicule(a)
    with pytest.raises(ValueError):
        route.ajouter_vehicule(b)
    assert b.route_actuelle is None
    assert route.vehicules == (a,)


def test_seuil_entree_exact(reseau):
    route = reseau.routes["AB"]
    a, b = Vehicule("A"), Vehicule("B")
    route.ajouter_vehicule(a)
    a.position = a.longueur + route.distance_securite
    assert route.peut_accueillir(b)
    route.ajouter_vehicule(b)
    assert len(route.vehicules) == 2


def test_pas_de_depassement(reseau):
    route = reseau.routes["AB"]
    a, b = Vehicule("A", 10), Vehicule("B", 100)
    route.ajouter_vehicule(a)
    a.position = 30
    route.ajouter_vehicule(b)
    route.mettre_a_jour_vehicules(10)
    assert b.position <= a.position - a.longueur - route.distance_securite


def test_pas_de_double_appartenance(reseau):
    v = Vehicule("V")
    reseau.routes["AB"].ajouter_vehicule(v)
    with pytest.raises(ValueError):
        reseau.routes["BC"].ajouter_vehicule(v)
