"""Herramientas comunes de los cuadernos del TFG.

Contiene:
  * el cargador de los datos de ``data/``,
  * las funciones del "método de la caja" (fracción de muestras que caen en una
    región alrededor del punto de interés),
  * el bootstrap del cociente posterior/prior en función del tamaño de caja,
  * el estilo de las gráficas.

El cociente posterior/prior evaluado en un punto es el ratio de Savage-Dickey;
como trabajamos con muestras (no con densidades), la densidad en el punto se
sustituye por la probabilidad contenida en una caja pequeña centrada en él.
"""
import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Contrapartida electromagnética candidata ZTF19abanrhr (Tabla 2 de la memoria)
RA_ZTF = np.radians(192.426239)    # ascensión recta [rad]
DEC_ZTF = np.radians(34.824715)    # declinación [rad]
DL_ZTF = 2443.1                    # distancia de luminosidad [Mpc]
Z_ZTF = 0.438                      # desplazamiento al rojo de la galaxia anfitriona (AGN)


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
def load_gw190521():
    """Muestras de ra, dec y distancia de luminosidad de GW190521 (modelo NRSur7dq4).

    Devuelve un diccionario con los arrays ``post_*`` (posterior, 65 723 muestras)
    y ``prior_*`` (prior publicado por LIGO-Virgo, 6 001 muestras).
    """
    with np.load(DATA_DIR / "gw190521_ra_dec_dl.npz") as f:
        return {k: f[k] for k in f.files}


def load_kick_spin():
    """Muestras de los ángulos del kick y del espín del remanente.

    Devuelve ``(post, prior)``. ``post`` contiene ``theta_an`` y ``theta_kn``
    (radianes); ``prior`` contiene ``theta_kn``, ``iota``, ``phase`` y las
    componentes del espín final ``spin_x, spin_y, spin_z``.
    """
    with np.load(DATA_DIR / "kick_spin_posterior.npz") as f:
        post = {k: f[k] for k in f.files}
    with np.load(DATA_DIR / "kick_spin_prior.npz") as f:
        prior = {k: f[k] for k in f.files}
    return post, prior


# --------------------------------------------------------------------------
# Método de la caja
# --------------------------------------------------------------------------
def frac_in_box_1d_where(x, x0, L):
    """Fracción de muestras con |x - x0| <= L/2 (caja de lado L centrada en x0)."""
    x = np.array(x)
    cond = (x >= x0 - L / 2.0) & (x <= x0 + L / 2.0)
    return np.where(cond)[0].size / len(x)


def frac_in_box_2d_where(x, y, x0, y0, L):
    """Fracción de muestras dentro de una caja cuadrada de lado L centrada en (x0, y0)."""
    x, y = np.array(x), np.array(y)
    hw = L / 2
    cond = (np.abs(x - x0) <= hw) & (np.abs(y - y0) <= hw)
    return np.where(cond)[0].size / len(x)


def frac_in_box_3d_where(x, y, z, x0, y0, z0, L_ra, L_dec, L_dl):
    """Fracción de muestras dentro de una caja 3D de lados (L_ra, L_dec, L_dl)."""
    x, y, z = np.array(x), np.array(y), np.array(z)
    cond = (
        (np.abs(x - x0) <= L_ra / 2.0)
        & (np.abs(y - y0) <= L_dec / 2.0)
        & (np.abs(z - z0) <= L_dl / 2.0)
    )
    return np.where(cond)[0].size / len(x)


def frac_cumulative(x, x0, L):
    """Fracción de muestras a una distancia MENOR que L de x0 (|x - x0| < L).

    Con x0 = 0 y x >= 0 equivale a la hipótesis de rango "x < L".
    """
    x = np.array(x)
    return np.where(np.abs(x - x0) < L)[0].size / len(x)


def frac_cumulative_2d(an_array, kn_array, L_an, L_kn_fixed=90.0):
    """Fracción de muestras con (theta_an < L_an) y (theta_kn < L_kn_fixed)."""
    condicion = (np.abs(an_array) < L_an) & (np.abs(kn_array) < L_kn_fixed)
    return np.sum(condicion) / len(an_array)


def ratio(f_post, f_prior):
    """Cociente posterior/prior (ratio de Savage-Dickey); NaN si el prior no tiene muestras."""
    return f_post / f_prior if f_prior > 0 else np.nan


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------
def bootstrap_ratio(post, prior, fraction, sizes, n_boot=100, seed=0):
    """Bootstrap del cociente posterior/prior en función del tamaño de caja.

    Parameters
    ----------
    post, prior : tupla de arrays
        Columnas de las muestras (por ejemplo ``(ra, dec)``). Todas las columnas
        de una misma muestra se remuestrean con los MISMOS índices, para no
        romper las correlaciones entre parámetros.
    fraction : callable ``fraction(columnas, L) -> float``
        Fracción de muestras que cae en la caja de tamaño ``L``.
    sizes : array
        Tamaños de caja a barrer.
    n_boot : int
        Número de réplicas bootstrap.

    Returns
    -------
    array de forma (n_boot, len(sizes)) con el cociente posterior/prior.
    """
    rng = np.random.default_rng(seed)
    n_post, n_prior = len(post[0]), len(prior[0])
    out = np.empty((n_boot, len(sizes)))
    for b in range(n_boot):
        ip = rng.integers(0, n_post, n_post)
        iq = rng.integers(0, n_prior, n_prior)
        post_b = tuple(c[ip] for c in post)
        prior_b = tuple(c[iq] for c in prior)
        for j, L in enumerate(sizes):
            out[b, j] = ratio(fraction(post_b, L), fraction(prior_b, L))
    return out


def bootstrap_ratio_exact_prior(post, prior_fraction, fraction, sizes, n_boot=100, seed=0):
    """Igual que ``bootstrap_ratio`` pero con la probabilidad a priori conocida de forma exacta.

    ``prior_fraction(L)`` devuelve la probabilidad a priori de la caja de tamaño ``L``,
    de modo que solo el posterior se remuestrea.
    """
    rng = np.random.default_rng(seed)
    n_post = len(post[0])
    f_prior = np.array([prior_fraction(L) for L in sizes])
    out = np.empty((n_boot, len(sizes)))
    for b in range(n_boot):
        ip = rng.integers(0, n_post, n_post)
        post_b = tuple(c[ip] for c in post)
        for j, L in enumerate(sizes):
            out[b, j] = ratio(fraction(post_b, L), f_prior[j])
    return out


def summarize(P):
    """Mediana y percentiles 5 y 95 (intervalo del 90 %) por columna."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # columnas todo NaN (prior sin muestras)
        return (np.nanpercentile(P, 50, axis=0),
                np.nanpercentile(P, 5, axis=0),
                np.nanpercentile(P, 95, axis=0))


# --------------------------------------------------------------------------
# Priors
# --------------------------------------------------------------------------
def sample_sky_distance_prior(n, seed=0, d_max=10000.0):
    """Prior usado en el análisis de LIGO-Virgo para (ra, dec, distancia).

    * ra uniforme en [0, 2*pi)
    * dec con densidad proporcional a cos(dec): prior isótropo en el cielo
    * distancia con densidad proporcional a d^2 en (0, d_max): fuentes
      distribuidas de forma homogénea en el volumen
    """
    rng = np.random.default_rng(seed)
    ra = rng.uniform(0, 2 * np.pi, n)
    dec = np.arcsin(2 * rng.random(n) - 1)
    dl = rng.random(n) ** (1 / 3) * d_max
    return ra, dec, dl


def prior_prob_box_3d(L_ang, L_dl, d_max=10000.0, dec0=DEC_ZTF, dl0=DL_ZTF):
    """Probabilidad a priori exacta de la caja 3D (fórmula analítica de los tres priors)."""
    p_ra = L_ang / (2 * np.pi)
    p_dec = (np.sin(dec0 + L_ang / 2) - np.sin(dec0 - L_ang / 2)) / 2
    p_dl = ((dl0 + L_dl / 2) ** 3 - (dl0 - L_dl / 2) ** 3) / d_max ** 3
    return p_ra * p_dec * p_dl


def prior_prob_box_2d(L, dec0=DEC_ZTF):
    """Probabilidad a priori exacta de la caja 2D (ra, dec)."""
    return (L / (2 * np.pi)) * (np.sin(dec0 + L / 2) - np.sin(dec0 - L / 2)) / 2


# --------------------------------------------------------------------------
# Gráficas
# --------------------------------------------------------------------------
def set_paper_style(font_size=13):
    """Estilo de gráficas tipo artículo (el usado en la memoria)."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": font_size,
        "axes.linewidth": 1.5,
        "xtick.major.size": 6,
        "xtick.major.width": 1.5,
        "ytick.major.size": 6,
        "ytick.major.width": 1.5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
    })


def plot_bootstrap(sizes, P, xlabel, ax=None, color="crimson", label=None, log=True):
    """Mediana e intervalo del 90 % del bootstrap del cociente posterior/prior frente al tamaño de caja."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))
    P50, P5, P95 = summarize(P)
    ax.fill_between(sizes, P5, P95, color=color, alpha=0.2)
    ax.plot(sizes, P50, ".-", color=color, label=label)
    if log:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Ratio P = posterior/prior")
    ax.grid(True, which="both", ls="--", alpha=0.4)
    return ax
