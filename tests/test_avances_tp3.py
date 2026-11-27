"""TP3 : fixtures, paramétrage, erreurs, cas limites et régressions."""

import json
import pytest

from simulateur_trafic.models.route import Route
from simulateur_trafic.models.vehicule import Voiture
from simulateur_trafic.models.exceptions import RouteIndisponibleError, ConfigurationInvalideError
from simulateur_trafic.models.reseau import ReseauRoutier
from simulateur_trafic.core.simulateur import Simulateur
from simulateur_trafic.core.analyseur import Analyseur


def test_fixture_route_valide(route_valide):
    assert route_valide.longueur == 100.0
    assert route_valide.vehicules == ()


def test_fixture_vehicule_valide(vehicule_valide):
    assert vehicule_valide.identifiant == "V-TEST"
    assert vehicule_valide.position == 0.0


def test_injection_avec_deux_fixtures(route_valide, vehicule_valide):
    route_valide.ajouter_vehicule(vehicule_valide)
    assert route_valide.vehicules == (vehicule_valide,)
    assert vehicule_valide.route_actuelle is route_valide


@pytest.mark.parametrize("longueur,limite,attendu", [
    (100.0, 50.0, True),     # normal 1
    (2500.0, 90.0, True),   # normal 2
    (0.001, 1.0, True),     # limite strictement positive
    (0.0, 50.0, False),    # invalide : longueur nulle
    (-2.0, 50.0, False),   # invalide : longueur négative
    (100.0, -5.0, False),  # invalide : vitesse négative
])
def test_creation_route_parametree(longueur, limite, attendu):
    if attendu:
        route = Route("R", longueur, limite, "A", "B")
        assert route.longueur == longueur
        assert route.limite_vitesse == limite
    else:
        with pytest.raises(ValueError):
            Route("R", longueur, limite, "A", "B")


def test_ajout_route_inexistante(reseau):
    with pytest.raises(RouteIndisponibleError, match="Route inconnue"):
        reseau.ajouter_vehicule(Voiture("V", itineraire=["INCONNUE"]))


def test_route_entree_bloquee(route_valide):
    route_valide.ajouter_vehicule(Voiture("V1"))
    with pytest.raises(RouteIndisponibleError, match="occupée"):
        route_valide.ajouter_vehicule(Voiture("V2"))


def test_fichier_configuration_manquant(tmp_path):
    with pytest.raises(FileNotFoundError, match="Configuration introuvable"):
        Simulateur(fichier_config=tmp_path / "introuvable.json")


def test_configuration_json_malforme(tmp_path):
    fichier = tmp_path / "incorrect.json"
    fichier.write_text('{"routes": [', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        Simulateur(fichier_config=fichier)


def test_simulation_iterations_negatives(reseau):
    with pytest.raises(ValueError, match="n_tours"):
        Simulateur(reseau=reseau).lancer_simulation(-1, afficher=False)


def test_avancer_temps_invalide(route_valide, vehicule_valide):
    route_valide.ajouter_vehicule(vehicule_valide)
    with pytest.raises(ValueError, match="delta_t"):
        vehicule_valide.avancer(0)


def test_vitesse_moyenne_route_vide(reseau):
    """Cas limite : pas de division par zéro ; résultat conventionnel 0 km/h."""
    assert Analyseur(reseau).vitesses_moyennes() == {"AB": 0.0, "BC": 0.0}


def test_simulation_zero_tour(reseau):
    simu = Simulateur(reseau=reseau)
    bilan = simu.lancer_simulation(0, afficher=False)
    assert isinstance(bilan, dict)
    assert len(simu.historique) == 1
