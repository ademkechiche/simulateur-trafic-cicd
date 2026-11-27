# Livraison finale — Simulateur de trafic (TP1 + TP2 + TP3)

## Contenu remis

- `simulateur_trafic/` : application exécutable et code source Python, y compris le fichier Cython `core/performance_cython.pyx`.
- `tests/` : suite de 87 tests unitaires, tests de régression, fixtures et tests paramétrés.
- `docs/` : documentation API et anomalies constatées avant correction.
- `resultats/` : graphiques (PNG/SVG), statistiques CSV/JSON, rapport historique des tests TP2.
- `resultats_tp3/` : rapport de couverture HTML et XML, liste des lignes non couvertes, profiling et mesures Python/Numba/Cython.
- `scripts/profilage_tp3.py` : script reproductible de benchmarking/profiling.
- `README.md`, `pyproject.toml`, `requirements.txt` : documentation et configuration du projet.

Les caches Python/pytest, données internes de couverture, compilations temporaires et doublons ont été retirés. Les résultats historiques TP2 sont conservés pour montrer la continuité du travail.

## Vérification du projet final

Depuis **PowerShell**, après extraction du dossier `tp_python` :

```powershell
cd tp_python
python -m pip install -e ".[test,graphiques]"
python -m pip install pytest-cov
python -m pytest -v
python -m pytest --cov=simulateur_trafic --cov-report=term-missing --cov-report=html:resultats_tp3/htmlcov --cov-report=xml:resultats_tp3/coverage.xml
start .\resultats_tp3\htmlcov\index.html
```

**Dernière vérification du dossier livré : 87 tests réussis, 0 échec, couverture globale de 78 %.** Ces pourcentages correspondent à la suite exécutée et incluent les modules CLI et affichage, qui restent partiellement non couverts.

## Lancer la simulation

```powershell
python -m simulateur_trafic
```

Les exports se trouvent dans `resultats/`.

## Exécuter Cython, Numba et cProfile

```powershell
python -m pip install numpy numba Cython setuptools
python -m scripts.profilage_tp3
```

Le script lance le simulateur sous **cProfile**, mesure le noyau Python, puis utilise **Numba** et compile le fichier `.pyx` **Cython** à l'importation via `pyximport`. Les résultats sont sauvegardés dans `resultats_tp3/profilage.txt` et `resultats_tp3/benchmark.json`. Il n'est pas nécessaire d'exécuter le fichier `.pyx` directement.

**Sur Windows**, la compilation Cython peut exiger Microsoft C++ Build Tools. Si Cython n'est pas compilable sur le poste, le script poursuit les autres mesures et signale `cython_indisponible` dans le JSON. Les mesures de vitesse varient selon le matériel et ne prouvent pas un gain global du simulateur : elles concernent un noyau numérique isolé.

## Remise

Remettre le dossier extrait ou l'archive `Simulateur_TP1_TP2_TP3_FINAL.zip` selon la demande de l'enseignant. Ne pas ajouter de dossiers `__pycache__`, `.pytest_cache`, `.venv` ou de fichiers `.coverage` au dossier final.
