"""Rock-physics forward modelling for a layered, partially saturated 1D soil column.

Computes the saturation profile (Van Genuchten), effective grain and fluid
properties, the Hertz-Mindlin contact-stiffness frame, and the saturated
P- and S-wave velocities (Biot-Gassmann) for a stack of soil layers above a
given water table depth.

Reference:
Solazzi, S. G., Bodet, L., Holliger, K., & Jougnot, D. (2021). Surface-wave
dispersion in partially saturated soils: The role of capillary forces.
Journal of Geophysical Research: Solid Earth, 126, e2021JB022074.
https://doi.org/10.1029/2021JB022074
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .RPfunctions import biotGassmann, effFluid, fish, hertzMindlin, hillsAverage
from .VGfunctions import vanGen

# Soil types recognized by the underlying Van Genuchten / mixture model
# (see selectSoilType_src in _cpp/VGfunctions_src.cpp).
SOIL_TYPES = (
    "clay",
    "silt",
    "clayloam",
    "loam",
    "loamysand",
    "cleansand",
    "sand",
    "sandyclay",
    "sandyclayloam",
    "sandyloam",
)


@dataclass(frozen=True)
class Layer:
    """One soil layer in the column, ordered from the surface downward."""

    soiltype: str
    thickness: float  # [m]
    N: float = 9.0  # Coordination number (contacts per grain)
    frac: float = 0.3  # Fraction of non-slipping grains

    def __post_init__(self) -> None:
        if self.soiltype not in SOIL_TYPES:
            raise ValueError(f"Unknown soiltype {self.soiltype!r}, must be one of {SOIL_TYPES}")
        if self.thickness <= 0:
            raise ValueError(f"Layer thickness must be > 0, got {self.thickness}")


@dataclass(frozen=True)
class GrainProperties:
    """Elastic moduli and density of the clay/silt/sand end-members making up the grains."""

    mu_clay: float = 6.8  # [GPa]
    mu_silt: float = 45.0
    mu_sand: float = 45.0
    k_clay: float = 25.0  # [GPa]
    k_silt: float = 37.0
    k_sand: float = 37.0
    rho_clay: float = 2580.0  # [kg/m3]
    rho_silt: float = 2600.0
    rho_sand: float = 2600.0


DEFAULT_GRAIN_PROPERTIES = GrainProperties()


@dataclass(frozen=True)
class FluidProperties:
    """Water and air physical properties."""

    rhow: float = 1000.0  # Water density [kg/m3]
    rhoa: float = 1.0  # Air density [kg/m3]
    kw: float = 2.3e9  # Water bulk modulus [Pa]
    ka: float = 1.01e5  # Air bulk modulus [Pa]


DEFAULT_FLUID_PROPERTIES = FluidProperties()


@dataclass(frozen=True)
class RockPhysicsResult:
    """Depth-profile outputs of :func:`compute_rock_physics`.

    All depth-indexed arrays (``zs``, ``hs``, ``Sws``, ... ``VPs``, ``VSs``)
    share the same length and are ordered from the surface (index 0) downward;
    ``zs`` is negative-downward [m].
    """

    zs: np.ndarray
    dz: float
    thks: np.ndarray
    WT: float
    hs: np.ndarray
    Sws: np.ndarray
    Swes: np.ndarray
    mus: np.ndarray
    ks: np.ndarray
    rhos: np.ndarray
    nus: np.ndarray
    kfs: np.ndarray
    rhofs: np.ndarray
    rhobs: np.ndarray
    KHMs: np.ndarray
    muHMs: np.ndarray
    VPs: np.ndarray
    VSs: np.ndarray

    @property
    def poisson_ratios(self) -> np.ndarray:
        """Poisson's ratio computed from VPs and VSs at each depth."""
        return np.array([fish(vp, vs) for vp, vs in zip(self.VPs, self.VSs, strict=True)])


def compute_rock_physics(
    layers: Sequence[Layer],
    WT: float,
    *,
    dz: float = 0.01,
    kk: int = 3,
    grain_properties: GrainProperties = DEFAULT_GRAIN_PROPERTIES,
    fluid_properties: FluidProperties = DEFAULT_FLUID_PROPERTIES,
    g: float = 9.82,
) -> RockPhysicsResult:
    """Compute the saturation and elastic-velocity depth profile of a soil column.

    Parameters:
        layers: Soil layers, ordered from the surface downward.
        WT: Water table depth below the surface [m].
        dz: Depth sample interval [m].
        kk: Effective pressure model: 1 = constant Pe (Zyserman et al., 2017),
            2 = Pe without suction, 3 = Pe with suction (Solazzi et al., 2021).
        grain_properties: Elastic moduli/density of the clay/silt/sand end-members.
        fluid_properties: Water/air physical properties.
        g: Gravitational acceleration [m/s2].

    Returns:
        A :class:`RockPhysicsResult` with the full depth profile.
    """
    if not layers:
        raise ValueError("At least one layer is required")
    if kk not in (1, 2, 3):
        raise ValueError(f"kk must be 1, 2 or 3, got {kk}")

    soiltypes = [layer.soiltype for layer in layers]
    thicknesses = [layer.thickness for layer in layers]
    Ns = [layer.N for layer in layers]
    fracs = [layer.frac for layer in layers]

    depth = float(np.sum(thicknesses))
    top_surface_level = dz
    zs = -np.arange(top_surface_level, depth + dz, dz)
    thks = np.diff(np.abs(zs))

    hs, Sws, Swes = vanGen(zs, WT, soiltypes, thicknesses)

    mus, ks, rhos, nus = hillsAverage(
        grain_properties.mu_clay,
        grain_properties.mu_silt,
        grain_properties.mu_sand,
        grain_properties.rho_clay,
        grain_properties.rho_silt,
        grain_properties.rho_sand,
        grain_properties.k_clay,
        grain_properties.k_silt,
        grain_properties.k_sand,
        soiltypes,
    )

    kfs, rhofs, rhobs = effFluid(
        Sws,
        fluid_properties.kw,
        fluid_properties.ka,
        fluid_properties.rhow,
        fluid_properties.rhoa,
        rhos,
        soiltypes,
        thicknesses,
        dz,
    )

    KHMs, muHMs = hertzMindlin(
        Swes,
        zs,
        hs,
        rhobs,
        g,
        fluid_properties.rhoa,
        fluid_properties.rhow,
        Ns,
        mus,
        nus,
        fracs,
        kk,
        soiltypes,
        thicknesses,
    )

    VPs, VSs = biotGassmann(KHMs, muHMs, ks, kfs, rhobs, soiltypes, thicknesses, dz)

    return RockPhysicsResult(
        zs=np.asarray(zs),
        dz=dz,
        thks=np.asarray(thks),
        WT=WT,
        hs=np.asarray(hs),
        Sws=np.asarray(Sws),
        Swes=np.asarray(Swes),
        mus=np.asarray(mus),
        ks=np.asarray(ks),
        rhos=np.asarray(rhos),
        nus=np.asarray(nus),
        kfs=np.asarray(kfs),
        rhofs=np.asarray(rhofs),
        rhobs=np.asarray(rhobs),
        KHMs=np.asarray(KHMs),
        muHMs=np.asarray(muHMs),
        VPs=np.asarray(VPs),
        VSs=np.asarray(VSs),
    )
