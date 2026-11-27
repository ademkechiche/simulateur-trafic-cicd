"""Cas nominaux, limites et invalides des véhicules et des transferts."""

import pytest

from simulateur_trafic.models import Bus, Camion, Vehicule, Voiture


def test_initialisation():
    v = Voiture("V1", 50, ["AB"])
    assert (v.position, v.vitesse, v.route_actuelle) == (0, 0, None)
    assert not v.termine
    assert v.temps_parcours is None


@pytest.mark.parametrize("classe,maximum", [(Voiture, 130), (Camion, 80), (Bus, 90)])
def test_limite_du_type(classe, maximum):
    assert classe("V1", 200).vitesse_souhaitee == maximum


@pytest.mark.parametrize("vitesse", [0, -1, float("nan"), float("inf")])
def test_vitesse_invalide(vitesse):
    with pytest.raises(ValueError):
        Vehicule("V1", vitesse)


@pytest.mark.parametrize("vitesse", [True, "rapide", None])
def test_type_vitesse_invalide(vitesse):
    with pytest.raises(TypeError):
        Vehicule("V1", vitesse)


@pytest.mark.parametrize("depart", [-1, float("nan"), float("inf")])
def test_depart_invalide(depart):
    with pytest.raises(ValueError):
        Vehicule("V1", depart=depart)


def test_identifiant_vide():
    with pytest.raises(ValueError):
        Vehicule("")


def test_sans_route_ne_bouge_pas():
    v = Vehicule("V1")
    assert v.avancer(1) == 0
    assert v.position == 0


def test_deplacement_et_bout_de_route(reseau):
    v = Vehicule("V1", 72, ["AB"])
    reseau.ajouter_vehicule(v)
    reseau.injecter_vehicules()
    assert v.avancer(3) == pytest.approx(30)
    assert v.vitesse == pytest.approx(36)
    assert v.avancer(20) == pytest.approx(70)
    assert v.position == 100


def test_transfert_premature_interdit(reseau):
    v = Vehicule("V1", 36, ["AB", "BC"])
    reseau.ajouter_vehicule(v)
    reseau.injecter_vehicules()
    with pytest.raises(ValueError):
        v.changer_de_route(reseau.routes["BC"])
    assert v.route_actuelle.nom == "AB"


def test_transfert_valide(reseau):
    v = Vehicule("V1", 36, ["AB", "BC"])
    reseau.ajouter_vehicule(v)
    reseau.injecter_vehicules()
    v.avancer(10)
    assert v.changer_de_route(reseau.routes["BC"])
    assert v.position == 0
    assert v not in reseau.routes["AB"].vehicules
    assert v in reseau.routes["BC"].vehicules
