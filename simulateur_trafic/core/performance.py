"""Noyau numérique isolé pour comparer Python, Cython et Numba."""


def calcul_distances_python(vitesses_kmh, duree_s):
    """Distances libres en mètres, sans bornes de route (benchmark calcul pur)."""
    return [v / 3.6 * duree_s for v in vitesses_kmh]


try:
    from numba import njit
except ImportError:
    njit = None

if njit is not None:
    @njit(cache=True)
    def calcul_distances_numba(vitesses_kmh, duree_s):
        """Noyau JIT Numba : calcul numérique répété."""
        resultat = []
        for v in vitesses_kmh:
            resultat.append(v / 3.6 * duree_s)
        return resultat
else:
    calcul_distances_numba = None
