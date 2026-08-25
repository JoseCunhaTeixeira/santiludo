"""SANTILUDO: rock-physics and surface-wave forward modelling for layered,
partially saturated 1D soils.

Typical usage:

    from santiludo import Layer, compute_rock_physics

    layers = [Layer(soiltype="clay", thickness=5)]
    rp = compute_rock_physics(layers, WT=2)
    print(rp.VPs, rp.VSs)

Reference:
Solazzi, S. G., Bodet, L., Holliger, K., & Jougnot, D. (2021). Surface-wave
dispersion in partially saturated soils: The role of capillary forces.
Journal of Geophysical Research: Solid Earth, 126, e2021JB022074.
https://doi.org/10.1029/2021JB022074
"""

from .model import (
    DEFAULT_FLUID_PROPERTIES,
    DEFAULT_GRAIN_PROPERTIES,
    SOIL_TYPES,
    FluidProperties,
    GrainProperties,
    Layer,
    RockPhysicsResult,
    compute_rock_physics,
)
from .seismic import (
    AcquisitionGeometry,
    DispersionConfig,
    GpdcNotFoundError,
    SeismicResult,
    UnderLayer,
    compute_seismic_forward,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_FLUID_PROPERTIES",
    "DEFAULT_GRAIN_PROPERTIES",
    "SOIL_TYPES",
    "AcquisitionGeometry",
    "DispersionConfig",
    "FluidProperties",
    "GpdcNotFoundError",
    "GrainProperties",
    "Layer",
    "RockPhysicsResult",
    "SeismicResult",
    "UnderLayer",
    "__version__",
    "compute_rock_physics",
    "compute_seismic_forward",
]
