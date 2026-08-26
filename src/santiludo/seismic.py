"""Seismic forward modelling on top of a :class:`~santiludo.model.RockPhysicsResult`.

Computes P- and S-wave first-arrival times for a linear acquisition geometry,
and Rayleigh/Love-wave phase-velocity dispersion curves via a selectable
backend: the pure-Python ``disba`` library (default, installed automatically
as a dependency) or the external ``gpdc`` program (Geopsy,
https://www.geopsy.org, opt-in via ``DispersionConfig(backend="gpdc")``;
must be installed separately and available on ``PATH``).
"""

import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from subprocess import CalledProcessError, run
from typing import Literal

import numpy as np
from disba import DispersionError, PhaseDispersion

from .model import RockPhysicsResult
from .TTDSPfunctions import firstArrival, readDispersion, writeVelocityModel

_DISBA_WAVE = {"R": "rayleigh", "L": "love"}


class GpdcNotFoundError(RuntimeError):
    """Raised when the ``gpdc`` executable cannot be found on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "The 'gpdc' executable was not found on PATH. It is required to compute "
            "surface-wave dispersion curves and ships with Geopsy "
            "(https://www.geopsy.org). Install it and ensure it is on PATH, or skip "
            "dispersion-curve computation."
        )


@dataclass(frozen=True)
class UnderLayer:
    """A homogeneous layer placed below the modelled soil column, GPDC format.

    The last under-layer represents the half-space and must have ``thickness == 0``.
    """

    thickness: float  # [m], 0 for the terminating half-space
    vp: float  # [m/s]
    vs: float  # [m/s]
    rho: float  # [kg/m3]


@dataclass(frozen=True)
class AcquisitionGeometry:
    """Linear receiver-array geometry."""

    x0: float = 0.5  # First geophone offset [m]
    nx: int = 400  # Number of geophones
    dx: float = 0.5  # Geophone spacing [m]
    trig: float = 0.0  # Acquisition pretrig [s]

    @property
    def xs(self) -> np.ndarray:
        return np.arange(self.x0, self.nx * self.dx + 1, self.dx)


@dataclass(frozen=True)
class DispersionConfig:
    """Frequency sampling, mode selection, and backend for the dispersion computation."""

    nf: int = 36  # Number of frequency samples
    df: float = 1.0  # Frequency sample interval [Hz]
    min_f: float = 15.0  # Minimum frequency [Hz]
    n_modes: int = 1  # Number of modes to compute
    wave: str = "R"  # 'R' Rayleigh (PSV) or 'L' Love (SH)
    mode: str = "frequency"  # GPDC-only sampling mode ('frequency' or 'wavelength')
    backend: Literal["gpdc", "disba"] = "disba"  # Dispersion-curve computation backend

    def __post_init__(self) -> None:
        if self.backend not in ("gpdc", "disba"):
            raise ValueError(f"backend must be 'gpdc' or 'disba', got {self.backend!r}")
        if self.wave not in ("R", "L"):
            raise ValueError(f"wave must be 'R' or 'L', got {self.wave!r}")
        if self.backend == "disba" and self.mode != "frequency":
            raise ValueError(
                f"mode={self.mode!r} ('wavelength' sampling) is only supported by the "
                "'gpdc' backend; disba only supports frequency-based sampling. "
                "Use backend='gpdc' or mode='frequency'."
            )

    @property
    def max_f(self) -> float:
        return self.min_f + (self.nf - 1) * self.df

    @property
    def freqs(self) -> np.ndarray:
        """Ascending frequency samples [Hz]."""
        return self.min_f + self.df * np.arange(self.nf)


@dataclass(frozen=True)
class SeismicResult:
    """Outputs of :func:`compute_seismic_forward`."""

    xs: np.ndarray
    ThodPs: np.ndarray
    ThodSs: np.ndarray
    dispersion_data: list[np.ndarray]
    n_modes: int
    zs_seismic: np.ndarray  # Depths including under-layers [m]
    VPs: np.ndarray  # VP profile including under-layers [m/s]
    VSs: np.ndarray  # VS profile including under-layers [m/s]
    rhobs: np.ndarray  # Density profile including under-layers [kg/m3]


def _validate_under_layers(under_layers: Sequence[UnderLayer]) -> None:
    for i, layer in enumerate(under_layers):
        is_last = i == len(under_layers) - 1
        if is_last and layer.thickness != 0:
            raise ValueError(f"Last under-layer thickness must be 0, got layer {i + 1}: {layer}")
        if not is_last and layer.thickness <= 0:
            raise ValueError(
                f"Under-layer thickness must be > 0 (except the last), got layer {i + 1}: {layer}"
            )


def _extend_with_under_layers(
    rp: RockPhysicsResult,
    under_layers: Sequence[UnderLayer],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Append under-layers below the soil column, for both plotting and first-arrival modelling."""
    dz = rp.dz
    zs_seismic = np.copy(rp.zs)
    VPs = np.copy(rp.VPs)
    VSs = np.copy(rp.VSs)
    rhobs = np.copy(rp.rhobs)

    for layer in under_layers:
        thickness_number = int(max(dz, layer.thickness) // dz)
        VPs = np.concatenate((VPs, [layer.vp] * thickness_number))
        VSs = np.concatenate((VSs, [layer.vs] * thickness_number))
        rhobs = np.concatenate((rhobs, [layer.rho] * thickness_number))
        zs_to_add = np.linspace(
            zs_seismic[-1] - dz,
            zs_seismic[-1] - dz * thickness_number,
            thickness_number,
        )
        zs_seismic = np.concatenate((zs_seismic, zs_to_add))

    return zs_seismic, VPs, VSs, rhobs


def _compute_dispersion_gpdc(
    rock_physics: RockPhysicsResult,
    under_layers: Sequence[UnderLayer],
    dispersion: DispersionConfig,
) -> tuple[list[np.ndarray], int]:
    """Dispersion curve(s) via the external gpdc binary (Geopsy).

    Raises:
        GpdcNotFoundError: If the ``gpdc`` executable is not available on PATH.
        RuntimeError: If the gpdc subprocess fails.
    """
    if shutil.which("gpdc") is None:
        raise GpdcNotFoundError()

    under_layers_str = "".join(
        " ".join(map(str, (layer.thickness, layer.vp, layer.vs, layer.rho))) + "\n"
        for layer in under_layers
    )
    velocity_model_string = writeVelocityModel(
        rock_physics.thks,
        rock_physics.VPs,
        rock_physics.VSs,
        rock_physics.rhobs,
        under_layers_str,
        len(under_layers),
    )
    gpdc_command = [
        f"gpdc -{dispersion.wave} {dispersion.n_modes} -n {dispersion.nf} "
        f"-min {dispersion.min_f} -max {dispersion.max_f} -s {dispersion.mode}"
    ]

    try:
        process = run(
            gpdc_command,
            input=velocity_model_string,
            text=True,
            shell=True,
            capture_output=True,
            check=True,
        )
    except CalledProcessError as e:
        raise RuntimeError(f"gpdc computation failed:\n{e.stdout}\n{e.stderr}") from e

    return readDispersion(process.stdout)


def _build_disba_model(
    rock_physics: RockPhysicsResult,
    under_layers: Sequence[UnderLayer],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Flat thickness/vp/vs/rho arrays for disba.PhaseDispersion (km, km/s, km/s, g/cm3)."""
    thks = np.concatenate((rock_physics.thks, [layer.thickness for layer in under_layers]))
    vps = np.concatenate((rock_physics.VPs, [layer.vp for layer in under_layers]))
    vss = np.concatenate((rock_physics.VSs, [layer.vs for layer in under_layers]))
    rhobs = np.concatenate((rock_physics.rhobs, [layer.rho for layer in under_layers]))
    return thks / 1000.0, vps / 1000.0, vss / 1000.0, rhobs / 1000.0


def _compute_dispersion_disba(
    rock_physics: RockPhysicsResult,
    under_layers: Sequence[UnderLayer],
    dispersion: DispersionConfig,
) -> tuple[list[np.ndarray], int]:
    """Dispersion curve(s) via the disba pure-Python backend.

    Modes are computed one at a time (0 = fundamental) and truncated at the first
    mode that isn't resolvable over the requested frequency range, mirroring gpdc's
    own positional mode truncation in :func:`readDispersion`. This can't represent a
    "gap" (e.g. mode 2 resolvable but mode 1 not) any better than gpdc's output can.
    """
    thks, vps, vss, rhobs = _build_disba_model(rock_physics, under_layers)
    phase_dispersion = PhaseDispersion(thks, vps, vss, rhobs)

    periods = 1.0 / dispersion.freqs[::-1]  # ascending period, as disba requires
    wave = _DISBA_WAVE[dispersion.wave]

    dispersion_data: list[np.ndarray] = []
    for mode in range(dispersion.n_modes):
        try:
            curve = phase_dispersion(periods, mode=mode, wave=wave)
        except DispersionError:
            break
        if curve.period.size == 0:
            break
        freqs_mode = 1.0 / curve.period[::-1]  # back to ascending frequency
        vels_mode = curve.velocity[::-1] * 1000.0  # km/s -> m/s
        dispersion_data.append(np.column_stack((freqs_mode, vels_mode)))

    return dispersion_data, len(dispersion_data)


def compute_seismic_forward(
    rock_physics: RockPhysicsResult,
    under_layers: Sequence[UnderLayer] = (),
    geometry: AcquisitionGeometry | None = None,
    dispersion: DispersionConfig | None = None,
) -> SeismicResult:
    """Compute P-/S-wave first arrivals and Rayleigh/Love-wave dispersion for a soil column.

    Parameters:
        rock_physics: Output of :func:`santiludo.model.compute_rock_physics`.
        under_layers: Optional homogeneous layers below the soil column (GPDC format),
            ordered from shallowest to the terminating half-space (thickness 0).
        geometry: Linear receiver-array geometry for first-arrival computation.
            Defaults to :class:`AcquisitionGeometry` defaults.
        dispersion: Frequency sampling, mode selection, and backend for the dispersion
            computation. Defaults to :class:`DispersionConfig` defaults.

    Returns:
        A :class:`SeismicResult`.

    Raises:
        GpdcNotFoundError: If ``dispersion.backend == "gpdc"`` and the ``gpdc``
            executable is not available on PATH.
    """
    if geometry is None:
        geometry = AcquisitionGeometry()
    if dispersion is None:
        dispersion = DispersionConfig()
    _validate_under_layers(under_layers)

    dz = rock_physics.dz
    xs = geometry.xs

    # First arrival times, including under-layers in the velocity model.
    thks_tmp = np.copy(rock_physics.thks)
    VPs_tmp = np.copy(rock_physics.VPs)
    VSs_tmp = np.copy(rock_physics.VSs)
    for layer in under_layers:
        thickness = layer.thickness if layer.thickness != 0 else 2 * dz
        n = int(thickness / dz)
        thks_tmp = np.concatenate((thks_tmp, [dz] * n))
        VPs_tmp = np.concatenate((VPs_tmp, [layer.vp] * n))
        VSs_tmp = np.concatenate((VSs_tmp, [layer.vs] * n))
    ThodPs = firstArrival(thks_tmp, VPs_tmp, xs, geometry.trig)
    ThodSs = firstArrival(thks_tmp, VSs_tmp, xs, geometry.trig)

    if dispersion.backend == "gpdc":
        dispersion_data, n_modes = _compute_dispersion_gpdc(rock_physics, under_layers, dispersion)
    else:
        dispersion_data, n_modes = _compute_dispersion_disba(rock_physics, under_layers, dispersion)

    zs_seismic, VPs_full, VSs_full, rhobs_full = _extend_with_under_layers(
        rock_physics, under_layers
    )

    return SeismicResult(
        xs=xs,
        ThodPs=ThodPs,
        ThodSs=ThodSs,
        dispersion_data=dispersion_data,
        n_modes=n_modes,
        zs_seismic=zs_seismic,
        VPs=VPs_full,
        VSs=VSs_full,
        rhobs=rhobs_full,
    )
