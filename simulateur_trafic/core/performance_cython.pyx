# cython: language_level=3
"""Noyau Cython : distances libres, pour évaluer le gain des boucles numériques."""

def calcul_distances_cython(list vitesses_kmh, double duree_s):
    cdef Py_ssize_t i, n = len(vitesses_kmh)
    cdef list resultat = [0.0] * n
    for i in range(n):
        resultat[i] = <double>vitesses_kmh[i] / 3.6 * duree_s
    return resultat
