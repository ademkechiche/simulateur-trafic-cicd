"""Profilage cProfile et mesure des noyaux; lancer depuis la racine du projet."""
import cProfile
import io
import pstats
import time
import json
from pathlib import Path
from simulateur_trafic.core.simulateur import Simulateur
from simulateur_trafic.core.performance import calcul_distances_python, calcul_distances_numba


def simuler():
    simulation = Simulateur()
    return simulation.lancer_simulation(n_tours=100, delta_t=10, afficher=False)


def mesure(f, repetitions=5):
    debut = time.perf_counter()
    for _ in range(repetitions):
        f()
    return (time.perf_counter() - debut) / repetitions


def main():
    profil = cProfile.Profile()
    profil.enable()
    simuler()
    profil.disable()
    dossier = Path("resultats_tp3")
    dossier.mkdir(exist_ok=True)
    profil.dump_stats(str(dossier / "profilage.prof"))
    out = io.StringIO()
    pstats.Stats(profil, stream=out).sort_stats("cumtime").print_stats(25)
    (dossier / "profilage.txt").write_text(out.getvalue(), encoding="utf-8")
    vitesses = [float(i % 130 + 1) for i in range(100_000)]
    resultats = {"python_s": mesure(lambda: calcul_distances_python(vitesses, 60))}
    if calcul_distances_numba is not None:
        import numpy as np
        vitesses_numpy = np.asarray(vitesses, dtype=np.float64)
        calcul_distances_numba(vitesses_numpy, 60.)  # échauffement JIT EXCLU du chronométrage
        assert list(calcul_distances_numba(vitesses_numpy[:100], 60.)) == calcul_distances_python(vitesses[:100], 60.)
        resultats["numba_s"] = mesure(lambda: calcul_distances_numba(vitesses_numpy, 60.))
    try:
        import pyximport
        pyximport.install(language_level=3)
        from simulateur_trafic.core.performance_cython import calcul_distances_cython
        assert calcul_distances_cython(vitesses[:100], 60.) == calcul_distances_python(vitesses[:100], 60.)
        resultats["cython_s"] = mesure(lambda: calcul_distances_cython(vitesses, 60.))
    except (ImportError, OSError) as exc:
        resultats["cython_indisponible"] = str(exc)
    (dossier / "benchmark.json").write_text(json.dumps(resultats, indent=2), encoding="utf-8")
    print(out.getvalue()[:2500]); print(resultats)


if __name__ == "__main__":
    main()
