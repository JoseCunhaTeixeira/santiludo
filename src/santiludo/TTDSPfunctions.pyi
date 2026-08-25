"""Type stub for the compiled santiludo.TTDSPfunctions Cython extension."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import numpy.typing as npt

_FloatArray = Sequence[float] | npt.NDArray[np.floating[Any]]

def writeVelocityModel(
    thk: _FloatArray,
    vp: _FloatArray,
    vs: _FloatArray,
    rho: _FloatArray,
    substratum: str,
    n_layers_substratum: int,
) -> str: ...
def firstArrival(
    thk: _FloatArray,
    vv: _FloatArray,
    Xdata: _FloatArray,
    trig: float,
) -> npt.NDArray[np.float64]: ...
def readDispersion(
    gpdc_output_string: str,
) -> tuple[list[npt.NDArray[np.float64]], int]:
    """Returns (dispersion_data, n_modes)."""
