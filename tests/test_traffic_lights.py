"""Tests des feux et de leur intégration au simulateur existant."""

import json

import pytest

from simulateur_trafic.core.simulateur import Simulateur
from simulateur_trafic.models import Intersection, ReseauRoutier, Route, Voiture
from simulateur_trafic.traffic_lights import TrafficLight


@pytest.fixture
def feu():
    return TrafficLight("F1", red_duration=3, green_duration=2, orange_duration=1)


@pytest.fixture
def scenario_feu(feu):
    reseau = ReseauRoutier()
    reseau.ajouter_intersection(Intersection("A"))
    reseau.ajouter_intersection(Intersection("B", traffic_light=feu))
    reseau.ajouter_intersection(Intersection("C"))
    reseau.ajouter_route(Route("AB", 10, 36, "A", "B"))
    reseau.ajouter_route(Route("BC", 100, 36, "B", "C"))
    voiture = Voiture("V1", vitesse=36, itineraire=["AB", "BC"])
    reseau.ajouter_vehicule(voiture)
    return reseau, voiture, feu


@pytest.mark.parametrize("rouge,vert,orange", [(3, 2, 1), (0.5, 1.25, 0.25), (30, 30, 5)])
def test_creation_valide(rouge, vert, orange):
    f = TrafficLight("F1", rouge, vert, orange)
    assert f.light_id == "F1"
    assert (f.red_duration, f.green_duration, f.orange_duration) == (rouge, vert, orange)
    assert f.get_state() == "RED"
    assert f.timer == 0


@pytest.mark.parametrize("nom", ["red_duration", "green_duration", "orange_duration"])
@pytest.mark.parametrize("valeur", [0, -1, float("nan"), float("inf"), -float("inf"), True, "5", None])
def test_duree_invalide(nom, valeur):
    with pytest.raises(ValueError, match=nom):
        TrafficLight("F1", **{nom: valeur})


@pytest.mark.parametrize("identifiant", ["", "   ", None, 17])
def test_identifiant_invalide(identifiant):
    with pytest.raises(ValueError, match="light_id"):
        TrafficLight(identifiant)


@pytest.mark.parametrize("etat,autorise", [("RED", False), ("GREEN", True), ("ORANGE", False)])
def test_can_pass(feu, etat, autorise):
    feu.state = etat
    assert feu.get_state() == etat
    assert feu.can_pass() is autorise


@pytest.mark.parametrize("etat", ["BLUE", "green", None, []])
def test_etat_invalide(feu, etat):
    with pytest.raises(ValueError, match="state"):
        feu.state = etat
    assert feu.state == "RED"


@pytest.mark.parametrize("initial,suivant", [("RED", "GREEN"), ("GREEN", "ORANGE"), ("ORANGE", "RED")])
def test_change_state(feu, initial, suivant):
    feu.state = initial
    feu.update(0.5)
    feu.change_state()
    assert feu.state == suivant
    assert feu.timer == 0


@pytest.mark.parametrize("initial,temps,etat,compteur", [
    ("RED", 0, "RED", 0),
    ("RED", 1, "RED", 1),
    ("RED", 3, "GREEN", 0),
    ("GREEN", 2, "ORANGE", 0),
    ("ORANGE", 1, "RED", 0),
    ("RED", 4, "GREEN", 1),
    ("RED", 6, "RED", 0),
    ("RED", 13, "RED", 1),
    ("GREEN", 4, "RED", 1),
    ("ORANGE", 5, "GREEN", 1),
])
def test_update(feu, initial, temps, etat, compteur):
    feu.state = initial
    feu.update(temps)
    assert feu.state == etat
    assert feu.timer == pytest.approx(compteur)


@pytest.mark.parametrize("temps", [-1, float("nan"), float("inf"), -float("inf"), True, "1", None])
def test_update_invalide(feu, temps):
    with pytest.raises(ValueError, match="elapsed_time"):
        feu.update(temps)
    assert (feu.state, feu.timer) == ("RED", 0)


@pytest.mark.parametrize("etat", ["RED", "GREEN", "ORANGE"])
def test_reset(feu, etat):
    feu.state = etat
    feu.update(0.5)
    feu.reset()
    assert feu.get_state() == "RED"
    assert feu.timer == 0
    assert feu.can_pass() is False


@pytest.mark.parametrize("etat,route_attendue", [("RED", "AB"), ("ORANGE", "AB"), ("GREEN", "BC")])
def test_vehicule_face_au_feu(scenario_feu, etat, route_attendue):
    reseau, voiture, f = scenario_feu
    f.state = etat
    reseau.avancer(1)
    assert voiture.route_actuelle.nom == route_attendue
    assert voiture.distance_parcourue == pytest.approx(10)
    if etat != "GREEN":
        assert voiture.position == 10
        assert voiture.vitesse == 0
    else:
        # Aucun deuxième déplacement après le transfert dans un même sous-pas.
        assert voiture.position == 0


def test_reprise_apres_rouge(scenario_feu):
    reseau, voiture, f = scenario_feu
    reseau.avancer(3)
    assert f.state == "GREEN"
    assert voiture.route_actuelle.nom == "AB"
    assert voiture.vitesse == 0
    reseau.avancer(1)
    assert voiture.route_actuelle.nom == "BC"
    assert voiture.position == 0
    reseau.avancer(1)
    assert voiture.position == pytest.approx(10)


@pytest.mark.parametrize("etat,termine", [("RED", False), ("ORANGE", False), ("GREEN", True)])
def test_feu_sur_derniere_route(scenario_feu, etat, termine):
    reseau, voiture, f = scenario_feu
    voiture.itineraire = ["AB"]
    f.state = etat
    reseau.avancer(1)
    assert voiture.termine is termine
    if not termine:
        assert voiture.route_actuelle.nom == "AB"
        assert voiture.vitesse == 0


def test_horloge_sans_vehicule(feu):
    reseau = ReseauRoutier()
    reseau.ajouter_intersection(Intersection("A", traffic_light=feu))
    reseau.avancer(2.5)
    assert feu.state == "RED"
    assert feu.timer == pytest.approx(2.5)
    reseau.avancer(0.5)
    assert feu.state == "GREEN"
    assert feu.timer == 0


def test_feu_partage_avance_une_fois(scenario_feu):
    reseau, _, f = scenario_feu
    reseau.intersections["C"].traffic_light = f
    reseau.avancer(1)
    assert f.state == "RED"
    assert f.timer == 1


def test_phases_courtes_non_ignorees(scenario_feu):
    reseau, voiture, _ = scenario_feu
    f = TrafficLight("COURT", 0.2, 0.1, 0.1)
    reseau.intersections["B"].traffic_light = f
    reseau.injecter_vehicules()
    voiture.position = 10
    reseau.avancer(1)
    assert voiture.route_actuelle.nom == "BC"


@pytest.mark.parametrize("etat,temps,autorise", [
    ("RED", 0, False), ("ORANGE", 0, False),
    ("GREEN", 0, True), ("GREEN", 10, False),
])
def test_compatibilite_avec_phases_existantes(feu, etat, temps, autorise):
    intersection = Intersection("B", phases=["AB", "XB"], duree_vert=10, traffic_light=feu)
    feu.state = etat
    assert intersection.autorise("AB", temps) is autorise


def test_intersection_refuse_feu_invalide():
    with pytest.raises(ValueError, match="traffic_light"):
        Intersection("B", traffic_light="RED")


def test_chargement_feu_depuis_json(tmp_path):
    config = {
        "intersections": [
            {"identifiant": "A"},
            {"identifiant": "B", "traffic_light": {
                "light_id": "JSON", "red_duration": 2,
                "green_duration": 2, "orange_duration": 1,
            }},
        ],
        "routes": [{"nom": "AB", "longueur": 10, "limite_vitesse": 36, "depart": "A", "arrivee": "B"}],
        "vehicules": [{"identifiant": "V1", "vitesse": 36, "itineraire": ["AB"]}],
    }
    fichier = tmp_path / "reseau_feu.json"
    fichier.write_text(json.dumps(config), encoding="utf-8")
    simulation = Simulateur(fichier_config=fichier)
    bilan = simulation.lancer_simulation(2, 1, afficher=False)
    assert bilan["vehicules_termines"] == 0
    assert simulation.reseau.intersections["B"].traffic_light.state == "GREEN"
    bilan = simulation.lancer_simulation(1, 1, afficher=False)
    assert bilan["vehicules_termines"] == 1


def test_vehicule_approche_le_feu_rouge(scenario_feu):
    reseau, voiture, _ = scenario_feu
    reseau.routes["AB"].longueur = 100
    reseau.avancer(1)
    assert voiture.position == pytest.approx(10)
    assert voiture.route_actuelle.nom == "AB"
