"""Genera los archivos reducidos de ``data/`` a partir de los archivos originales.

Los cuadernos solo necesitan unas pocas columnas de cada archivo original, así que
se guardan en formato ``.npz`` comprimido (pocos MB en lugar de cientos). No se
modifica ninguna muestra: solo se seleccionan columnas.

Uso (desde la raíz del repositorio)::

    python scripts/prepare_data.py --gw190521 RUTA/GW190521_posterior_samples.h5 \
        --posterior-kick RUTA/Remnant_50k.json \
        --prior-kick RUTA/newpriors.csv

Cada opción es independiente: puede ejecutarse solo la parte de la que se
disponga del archivo original.
"""
import argparse
import ast
import json
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def gw190521(path):
    import h5py

    with h5py.File(path, "r") as f:
        g = f["NRSur7dq4"]
        post, prior = g["posterior_samples"], g["priors"]["samples"]
        out = {
            "post_ra": np.array(post["ra"]),
            "post_dec": np.array(post["dec"]),
            "post_dl": np.array(post["luminosity_distance"]),
            "prior_ra": np.array(prior["ra"]),
            "prior_dec": np.array(prior["dec"]),
            "prior_dl": np.array(prior["luminosity_distance"]),
        }
    np.savez_compressed(DATA_DIR / "gw190521_ra_dec_dl.npz", **out)
    print("gw190521_ra_dec_dl.npz:", {k: v.shape for k, v in out.items()})


def posterior_kick(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    out = {
        "theta_an": np.array(d["theta_an"]),
        "theta_kn": np.array(d["theta_kn"]),
    }
    np.savez_compressed(DATA_DIR / "kick_spin_posterior.npz", **out)
    print("kick_spin_posterior.npz:", {k: v.shape for k, v in out.items()})


def prior_kick(path):
    import pandas as pd

    df = pd.read_csv(path, converters={"final_spin_components": ast.literal_eval})
    spin = np.vstack(df["final_spin_components"].values)
    out = {
        "theta_kn": df["theta_kn"].to_numpy(),
        "iota": df["iota"].to_numpy(),
        "phase": df["phase"].to_numpy(),
        "spin_x": spin[:, 0],
        "spin_y": spin[:, 1],
        "spin_z": spin[:, 2],
    }
    np.savez_compressed(DATA_DIR / "kick_spin_prior.npz", **out)
    print("kick_spin_prior.npz:", {k: v.shape for k, v in out.items()})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gw190521", help="GW190521_posterior_samples.h5 (LIGO DCC P2000158)")
    p.add_argument("--posterior-kick", help="JSON con el posterior del remanente (theta_an, theta_kn)")
    p.add_argument("--prior-kick", help="CSV con el prior del remanente")
    a = p.parse_args()
    DATA_DIR.mkdir(exist_ok=True)
    if a.gw190521:
        gw190521(a.gw190521)
    if a.posterior_kick:
        posterior_kick(a.posterior_kick)
    if a.prior_kick:
        prior_kick(a.prior_kick)
