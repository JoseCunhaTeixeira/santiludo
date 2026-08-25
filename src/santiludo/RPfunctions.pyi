"""Type stub for the compiled santiludo.RPfunctions Cython extension."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import numpy.typing as npt

_FloatArray = Sequence[float] | npt.NDArray[np.floating[Any]]

def effFluid(
    Sw: _FloatArray,
    kw: float,
    ka: float,
    rhow: float,
    rhoa: float,
    rhos: _FloatArray,
    soiltypes: Sequence[str],
    thicknesses: _FloatArray,
    dz: float,
) -> tuple[list[float], list[float], list[float]]:
    """Returns (kf, rhof, rhob)."""

def fish(vp: float, vs: float) -> float:
    """Poisson's ratio from Vp and Vs."""

def biotGassmann(
    KHM: _FloatArray,
    muHM: _FloatArray,
    ks: _FloatArray,
    kf: _FloatArray,
    rhob: _FloatArray,
    soiltypes: Sequence[str],
    thicknesses: _FloatArray,
    dz: float,
) -> tuple[list[float], list[float]]:
    """Returns (Vp, Vs)."""

def hertzMindlin(
    Swe: _FloatArray,
    z: _FloatArray,
    h: _FloatArray,
    rhob: _FloatArray,
    g: float,
    rhoa: float,
    rhow: float,
    Ns: _FloatArray,
    mus: _FloatArray,
    nus: _FloatArray,
    fracs: _FloatArray,
    kk: int,
    soiltypes: Sequence[str],
    thicknesses: _FloatArray,
) -> tuple[list[float], list[float]]:
    """Returns (KHM, muHM)."""

def hillsAverage(
    mu_clay: float,
    mu_silt: float,
    mu_sand: float,
    rho_clay: float,
    rho_silt: float,
    rho_sand: float,
    k_clay: float,
    k_silt: float,
    k_sand: float,
    soiltypes: Sequence[str],
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Returns (mus, ks, rhos, nus)."""
