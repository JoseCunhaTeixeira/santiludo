"""Type stub for the compiled santiludo.VGfunctions Cython extension."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import numpy.typing as npt

_FloatArray = Sequence[float] | npt.NDArray[np.floating[Any]]

def vanGen(
    z: _FloatArray,
    WT: float,
    soiltypes: Sequence[str],
    thicknesses: _FloatArray,
) -> tuple[list[float], list[float], list[float]]:
    """Returns (h, Sw, Swe)."""

def selectSoilType(
    soiltype: str,
) -> tuple[float, float, float, float, float, float, float, float]:
    """Returns (wsand, wclay, wsilt, phi, alpha, nvg, theta, Swr)."""
