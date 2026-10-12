# Datos

Los cuadernos leen tres archivos reducidos en formato NumPy (`.npz` comprimido). Contienen **las mismas muestras que los archivos originales, sin modificar**; solo se han seleccionado las columnas que usa el análisis para que el repositorio pese pocos MB. El script [`../scripts/prepare_data.py`](../scripts/prepare_data.py) documenta (y permite repetir) esa selección.

| Archivo | Contenido | Tamaño | Lo usan |
|---|---|---|---|
| `gw190521_ra_dec_dl.npz` | Posterior (65 723 muestras) y prior (6 001 muestras) de la ascensión recta `ra` (rad), la declinación `dec` (rad) y la distancia de luminosidad `luminosity_distance` (Mpc) de GW190521, modelo de forma de onda `NRSur7dq4` | 1,6 MB | 01, 03 |
| `kick_spin_posterior.npz` | Posterior del remanente (50 000 muestras): ángulos `theta_an` (entre el espín final y la línea de visión) y `theta_kn` (entre el kick y la línea de visión), en radianes. Ya restringido a la posición en el cielo y la distancia de ZTF19abanrhr | 0,7 MB | 02 |
| `kick_spin_prior.npz` | Prior del remanente (50 000 muestras): `theta_kn` (rad), inclinación `iota` y fase `phase` (para la línea de visión) y componentes `spin_x`, `spin_y`, `spin_z` del espín final | 2,2 MB | 02 |

## Procedencia

* **`gw190521_ra_dec_dl.npz`** — archivo público `GW190521_posterior_samples.h5` de la colaboración LIGO-Virgo (≈ 160 MB), publicado con los artículos del descubrimiento: <https://dcc.ligo.org/LIGO-P2000158/public>. Se extrae el grupo `NRSur7dq4` (`posterior_samples` y `priors/samples`).
* **`kick_spin_posterior.npz` y `kick_spin_prior.npz`** — muestras del remanente (kick y espín) facilitadas por el tutor del TFG a partir de las muestras de GW190521 (archivos originales `Remnant_50k.json` y `newpriors.csv`).

## Cómo regenerarlos

Con los archivos originales descargados:

```bash
python scripts/prepare_data.py \
    --gw190521 RUTA/GW190521_posterior_samples.h5 \
    --posterior-kick RUTA/Remnant_50k.json \
    --prior-kick RUTA/newpriors.csv
```

(Requiere además `h5py` y `pandas`; ver `requirements.txt`.)

## Coordenadas de la contrapartida (ZTF19abanrhr)

Fijadas en `src/tfg_bayes.py` (Tabla 2 de la memoria): ascensión recta 192,426239°, declinación 34,824715°, distancia de luminosidad 2443,1 Mpc; desplazamiento al rojo de la galaxia anfitriona z = 0,438.
