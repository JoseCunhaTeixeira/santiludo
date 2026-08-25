# santiludo

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.1029%2F2021JB022074-blue)](https://doi.org/10.1029/2021JB022074)

Rock-physics and surface-wave forward modelling for a layered, partially
saturated 1D soil column: saturation profile, saturated P-/S-wave velocities,
first-arrival times, and Rayleigh-wave dispersion curves.

- Programmers: *S.G. Solazzi & L. Bodet* (Van Genuchten model courtesy of D. Jougnot)
- First version: *2020/07/14*
- Converted to C++ and interfaced with Python (Cython) by J. Cunha Teixeira and B. Decker, 2024/03
- Adapted to multi-layers, 2024/04 by J. Cunha Teixeira
- Packaged as an installable, importable library, 2026/08 by J. Cunha Teixeira

## Reference

Solazzi, S. G., Bodet, L., Holliger, K., & Jougnot, D. (2021). Surface-wave
dispersion in partially saturated soils: The role of capillary forces.
*Journal of Geophysical Research: Solid Earth*, 126, e2021JB022074.
https://doi.org/10.1029/2021JB022074

See [CITATION.cff](CITATION.cff) for citation metadata (also usable via
GitHub's "Cite this repository" button).

## Installation

Requires a C++ compiler (MSVC on Windows, gcc/clang on Linux/macOS) since the
core physics is implemented in C++ and wrapped with Cython.

```bash
pip install .
# or, for local development:
pip install -e ".[dev]"
```

This builds three compiled extensions (`santiludo.VGfunctions`,
`santiludo.RPfunctions`, `santiludo.TTDSPfunctions`) from `src/santiludo/_cpp/`.

To install it into another repo's environment straight from source (e.g. a
git checkout or a private git URL), the same `pip install` commands work:

```bash
pip install git+https://github.com/JoseCunhaTeixeira/Santiludo_layered.git
```

### Optional: surface-wave dispersion (`gpdc`)

Dispersion-curve computation shells out to the `gpdc` program from
[Geopsy](https://www.geopsy.org), which must be installed separately and be
on `PATH`. It is **not** a Python dependency. If it's missing,
`santiludo.seismic.compute_seismic_forward` raises a `GpdcNotFoundError` with
installation pointers; the rock-physics API (`compute_rock_physics`) does not
need it at all.

## Usage

```python
from santiludo import Layer, compute_rock_physics

layers = [Layer(soiltype="clay", thickness=5)]
rp = compute_rock_physics(layers, WT=2)  # water table at 2 m depth

rp.zs  # depths [m], negative-downward
rp.Sws  # saturation profile [-]
rp.VPs  # P-wave velocity profile [m/s]
rp.VSs  # S-wave velocity profile [m/s]
```

Add seismic forward modelling (first arrivals + dispersion, requires `gpdc`):

```python
from santiludo import AcquisitionGeometry, DispersionConfig, UnderLayer
from santiludo.seismic import compute_seismic_forward

under_layers = [
    UnderLayer(thickness=10, vp=4000, vs=2000, rho=2500),
    UnderLayer(thickness=0, vp=8000, vs=4000, rho=2500),  # half-space, thickness=0
]
seismic = compute_seismic_forward(
    rp,
    under_layers,
    geometry=AcquisitionGeometry(x0=0.5, nx=400, dx=0.5),
    dispersion=DispersionConfig(nf=36, min_f=15),
)
seismic.ThodPs  # P-wave first arrival times [s]
seismic.dispersion_data  # list of (freq, phase velocity) arrays, one per mode
```

Plotting is optional and separate from the models (`santiludo.plotting`).
See [examples/basic_usage.py](examples/basic_usage.py) for a full run that
reproduces the original SANTILUDO script's PDF report.

## Package layout

```
src/santiludo/
  __init__.py          Public API
  model.py              Rock physics: Layer, compute_rock_physics, RockPhysicsResult
  seismic.py             Seismic forward modelling: UnderLayer, compute_seismic_forward, SeismicResult
  plotting.py             Optional matplotlib helpers
  _cpp/                    C++ sources (*_src.cpp) and Cython wrappers (*.pyx)
```

- C++ functions are named `nameFunction_src`; their Cython wrappers (called
  from Python) are named `nameFunction`.
- If you change a function's header in a `*_src.cpp`, update the matching
  `*.pyx` declaration too.
- `setup.py` builds the extensions (invoked automatically by `pip install`).

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format .
pyright
```

## Known limitations / ideas for future work

- Fewer discretization cells are needed when `soiltype="sand"`.
- Sensitivity to layer thickness, half-space depth/thickness, and
  discretization has not been systematically tested.
- Sensitivity to Hertz-Mindlin, mechanical, and geometric parameters has not
  been systematically tested.
- Only the Van Genuchten retention model is implemented; alternative
  rock-physics models could be added.
