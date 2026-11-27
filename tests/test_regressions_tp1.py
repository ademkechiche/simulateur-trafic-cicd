import csv
import json
import tempfile
import unittest
from pathlib import Path

from simulateur_trafic.core.simulateur import Simulateur
from simulateur_trafic.models import Intersection, Route, ReseauRoutier, Vehicule, Camion


def petit_reseau(longueur=10):
    reseau = ReseauRoutier()
    for nom in ("A", "B", "C"):
        reseau.ajouter_intersection(Intersection(nom))
    reseau.ajouter_route(Route("AB", longueur, 36, "A", "B"))
    reseau.ajouter_route(Route("BC", longueur, 36, "B", "C"))
    return reseau


class TestSimulateur(unittest.TestCase):
    def test_avancer_et_limite_vitesse(self):
        reseau = petit_reseau(100)
        v = Vehicule("V1", 72, ["AB"])
        reseau.ajouter_vehicule(v)
        reseau.avancer(2)
        self.assertAlmostEqual(v.position, 20)
        self.assertAlmostEqual(v.vitesse, 36)

    def test_camion_limite_par_son_type(self):
        self.assertEqual(Camion("C1", 120).vitesse_souhaitee, 80)

    def test_transfert_sans_double_deplacement(self):
        reseau = petit_reseau()
        v = Vehicule("V1", 36, ["AB", "BC"])
        reseau.ajouter_vehicule(v)
        reseau.avancer(1)
        self.assertEqual(v.route_actuelle.nom, "BC")
        self.assertEqual(v.position, 0)
        reseau.avancer(1)
        self.assertTrue(v.termine)
        self.assertEqual(v.distance_parcourue, 20)
        self.assertEqual(v.temps_parcours, 2)

    def test_sous_pas_fractionnaire(self):
        reseau = petit_reseau(100)
        v = Vehicule("V1", 36, ["AB"])
        reseau.ajouter_vehicule(v)
        reseau.avancer(0.25)
        self.assertAlmostEqual(v.position, 2.5)
        self.assertAlmostEqual(reseau.temps, 0.25)

    def test_entree_occupee_et_distance_securite(self):
        reseau = petit_reseau(100)
        for nom in ("V1", "V2"):
            reseau.ajouter_vehicule(Vehicule(nom, 36, ["AB"]))
        reseau.injecter_vehicules()
        self.assertIsNone(reseau.vehicules["V2"].heure_depart)
        reseau.avancer(2)
        a, b = reseau.vehicules["V1"], reseau.vehicules["V2"]
        self.assertIsNotNone(b.heure_depart)
        self.assertGreaterEqual(a.position - b.position, a.longueur + 2)

    def test_transfert_bloque_ne_perd_pas_le_vehicule(self):
        reseau = petit_reseau(100)
        a, b = Vehicule("A", 36, ["AB", "BC"]), Vehicule("B", 36, ["BC"])
        reseau.ajouter_vehicule(a)
        reseau.ajouter_vehicule(b)
        reseau.injecter_vehicules()
        a.position = reseau.routes["AB"].longueur
        self.assertFalse(a.changer_de_route(reseau.routes["BC"]))
        self.assertIs(a.route_actuelle, reseau.routes["AB"])
        self.assertIn(a, reseau.routes["AB"].vehicules)

    def test_feu_rouge_puis_vert(self):
        reseau = petit_reseau()
        reseau.intersections["B"].phases = ["autre", "AB"]
        reseau.intersections["B"].duree_vert = 2
        v = Vehicule("V1", 36, ["AB", "BC"])
        reseau.ajouter_vehicule(v)
        reseau.avancer(2)
        self.assertEqual(v.route_actuelle.nom, "AB")
        self.assertEqual(v.vitesse, 0)
        reseau.avancer(1)
        self.assertEqual(v.route_actuelle.nom, "BC")
        reseau.avancer(1)
        self.assertEqual(v.temps_parcours, 4)

    def test_depart_differe(self):
        reseau = petit_reseau()
        v = Vehicule("V1", 36, ["AB"], depart=3)
        reseau.ajouter_vehicule(v)
        reseau.avancer(3)
        self.assertIsNone(v.heure_depart)
        reseau.avancer(1)
        self.assertEqual(v.heure_depart, 3)
        self.assertTrue(v.termine)

    def test_dijkstra_minimise_le_temps(self):
        reseau = petit_reseau(100)
        reseau.ajouter_route(Route("AC", 300, 120, "A", "C"))
        self.assertEqual(reseau.plus_court_chemin("A", "C"), ["AC"])
        with self.assertRaises(ValueError):
            reseau.plus_court_chemin("C", "A")

    def test_validation(self):
        reseau = petit_reseau()
        with self.assertRaises(ValueError):
            reseau.ajouter_vehicule(Vehicule("V1", 36, ["BC", "AB"]))
        reseau.ajouter_vehicule(Vehicule("V1", 36, ["AB"]))
        with self.assertRaises(ValueError):
            reseau.ajouter_vehicule(Vehicule("V1", 36, ["AB"]))
        with self.assertRaises(ValueError):
            reseau.avancer(0)
        with self.assertRaises(ValueError):
            Simulateur(reseau=reseau).lancer_simulation(-1, afficher=False)

    def test_exports_et_statistiques(self):
        reseau = petit_reseau()
        reseau.ajouter_vehicule(Vehicule("V1", 36, ["AB", "BC"]))
        simulateur = Simulateur(reseau=reseau)
        bilan = simulateur.lancer_simulation(3, 1, afficher=False)
        self.assertEqual(bilan["vehicules_termines"], 1)
        self.assertEqual(bilan["vitesse_moyenne_trajets_kmh"], 36)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as dossier:
            fichiers = simulateur.exporter(dossier, graphiques=False)
            self.assertEqual(len(fichiers), 4)
            resultat = json.loads((Path(dossier) / "resultats.json").read_text(encoding="utf-8"))
            self.assertEqual(len(resultat["historique"]), 4)
            with (Path(dossier) / "trajets.csv").open(encoding="utf-8-sig", newline="") as flux:
                ligne = list(csv.DictReader(flux))[0]
            self.assertEqual(ligne["statut"], "termine")
            self.assertEqual(float(ligne["distance_m"]), 20)

    def test_simulation_complete_conservation_et_espacement(self):
        simulateur = Simulateur()
        for _ in range(360):
            simulateur.reseau.avancer(10)
            reseau = simulateur.reseau
            etat = reseau.etat()
            self.assertEqual(etat["vehicules_actifs"] + etat["vehicules_termines"]
                             + etat["vehicules_en_attente"], len(reseau.vehicules))
            presents = []
            for route in reseau.routes.values():
                vehicules = sorted(route.vehicules, key=lambda v: v.position, reverse=True)
                presents.extend(v.identifiant for v in vehicules)
                for v in vehicules:
                    self.assertGreaterEqual(v.position, 0)
                    self.assertLessEqual(v.position, route.longueur)
                for a, b in zip(vehicules, vehicules[1:]):
                    self.assertGreaterEqual(a.position - b.position + 1e-8,
                                            a.longueur + route.distance_securite)
            self.assertEqual(len(presents), len(set(presents)))
        bilan = simulateur.analyseur.bilan()
        self.assertEqual(bilan["nombre_vehicules_total"], 402)
        self.assertEqual(bilan["vehicules_termines"], 402)
        self.assertEqual(bilan["vehicules_actifs"], 0)


if __name__ == "__main__":
    unittest.main()
