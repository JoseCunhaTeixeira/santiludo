"""Example: reproduce the original SANTILUDO script's output using the santiludo package.

Run from the repo root after installing the package (`pip install -e .`):

    python examples/basic_usage.py
"""

from pathlib import Path
from time import perf_counter

import numpy as np
from matplotlib.cm import copper

from santiludo import AcquisitionGeometry, DispersionConfig, Layer, UnderLayer
from santiludo.model import compute_rock_physics
from santiludo.plotting import save_report_pdf
from santiludo.seismic import GpdcNotFoundError, compute_seismic_forward

OUTPUT_DIR = Path(__file__).parent / "output"


def main() -> None:
    start = perf_counter()
    OUTPUT_DIR.mkdir(exist_ok=True)

    layers = [Layer(soiltype="clay", thickness=5, N=9, frac=0.3)]
    WTs = [2]  # Water table depths to compare [m]
    colors = copper(np.linspace(0, 1, len(WTs)))

    under_layers = [
        UnderLayer(thickness=10, vp=4000, vs=2000, rho=2500),
        UnderLayer(thickness=0, vp=8000, vs=4000, rho=2500),
    ]
    geometry = AcquisitionGeometry(x0=0.5, nx=400, dx=0.5)
    # backend defaults to "disba"; pass backend="gpdc" to use Geopsy's gpdc instead
    dispersion = DispersionConfig(nf=36, df=1, min_f=15, n_modes=1)

    scenarios = []
    for wt, color in zip(WTs, colors, strict=True):
        rp = compute_rock_physics(layers, WT=wt)
        try:
            seismic = compute_seismic_forward(rp, under_layers, geometry, dispersion)
        except GpdcNotFoundError as e:
            print(f"Skipping seismic forward modelling: {e}")
            seismic = None
        scenarios.append((rp, seismic, color, f"WT={wt}m"))

    name = "_".join(f"{layer.soiltype}{layer.thickness}" for layer in layers)
    if under_layers:
        name += "_substratum"
    save_report_pdf(scenarios, OUTPUT_DIR / f"{name}.SANTILUDO.pdf")

    print(f"\nElapsed time: {perf_counter() - start:.2f} s")


if __name__ == "__main__":
    main()
