"""Optional plotting helpers for :class:`~santiludo.model.RockPhysicsResult` and
:class:`~santiludo.seismic.SeismicResult`.

Nothing in this module is required to run the forward models; it only turns
their outputs into matplotlib figures, mirroring the diagnostic plots from the
original SANTILUDO script.
"""

import os
from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from .model import RockPhysicsResult
from .seismic import SeismicResult


def plot_van_genuchten(rp: RockPhysicsResult) -> Figure:
    """Pressure head and saturation profiles with depth."""
    fig, axs = plt.subplots(1, 2, figsize=(8, 4), gridspec_kw={"wspace": 0.5})

    axs[0].plot(rp.hs, rp.zs)
    axs[0].axhline(-rp.WT, color="gray", linestyle="--")
    axs[0].set_xlabel("Pressure head h")
    axs[0].set_ylabel("Depth [m]")
    axs[0].set_ylim((rp.zs[-1], 0))
    axs[0].grid()

    axs[1].plot(rp.Sws, rp.zs, label="$S_w$")
    axs[1].plot(rp.Swes, rp.zs, label="$S_{we}$")
    axs[1].axhline(-rp.WT, color="gray", linestyle="--", label="WT")
    axs[1].set_xlabel("Saturation")
    axs[1].set_xlim([-0.05, 1.05])
    axs[1].set_ylim((rp.zs[-1], 0))
    axs[1].grid()
    axs[1].legend()

    fig.tight_layout()
    return fig


def plot_effective_fluid(rp: RockPhysicsResult) -> Figure:
    """Effective fluid compressibility and bulk/fluid density profiles with depth."""
    fig, axs = plt.subplots(1, 2, figsize=(8, 4), gridspec_kw={"wspace": 0.5})

    axs[0].plot(rp.kfs, rp.zs)
    axs[0].axhline(-rp.WT, color="gray", linestyle="--")
    axs[0].set_xlabel("Effective compressibility $k_f$ [Pa$^{-1}$]")
    axs[0].set_ylabel("Depth [m]")
    axs[0].set_ylim((rp.zs[-1], 0))
    axs[0].grid()

    axs[1].plot(rp.rhofs, rp.zs, label="Fluid density $\\rho_f$")
    axs[1].plot(rp.rhobs, rp.zs, label="Bulk density $\\rho_b$")
    axs[1].axhline(-rp.WT, color="gray", linestyle="--")
    axs[1].set_xlabel("Density [kg/m$^3$]")
    axs[1].set_ylim((rp.zs[-1], 0))
    axs[1].grid()
    axs[1].legend(fontsize=8)

    fig.tight_layout()
    return fig


def plot_hertz_mindlin(rp: RockPhysicsResult) -> Figure:
    """Hertz-Mindlin frame bulk and shear moduli with depth."""
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(rp.KHMs, rp.zs, label="Effective bulk $K_{HM}$")
    ax.plot(rp.muHMs, rp.zs, label="Shear moduli $\\mu_{HM}$")
    ax.axhline(-rp.WT, color="gray", linestyle="--")
    ax.set_xlabel("Pressure [Pa]")
    ax.set_ylabel("Depth $z$ [m]")
    ax.set_ylim((rp.zs[-1], 0))
    ax.grid()
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_saturated_velocities(rp: RockPhysicsResult) -> Figure:
    """Saturated P- and S-wave velocity profiles with depth."""
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(rp.VPs, rp.zs, label="$V_p$")
    ax.plot(rp.VSs, rp.zs, label="$V_s$")
    ax.axhline(-rp.WT, color="gray", linestyle="--")
    ax.set_xlabel("Velocity [m/s]")
    ax.set_ylabel("Depth $z$ [m]")
    ax.set_ylim((rp.zs[-1], 0))
    ax.grid()
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_summary_pages(
    scenarios: Sequence[tuple[RockPhysicsResult, SeismicResult | None, str, str]],
) -> tuple[Figure, Figure]:
    """Build the two-page dashboard (rock physics, then seismic) for one or more scenarios.

    Parameters:
        scenarios: Sequence of ``(rock_physics, seismic, color, label)`` tuples.
            ``seismic`` may be ``None`` to skip the first-arrival/dispersion row.

    Returns:
        ``(page1, page2)`` matplotlib figures.
    """
    page1, axs1 = plt.subplots(
        2, 3, figsize=(11.69, 8.27), gridspec_kw={"hspace": 0.3, "wspace": 0.4}
    )
    page2, axs2 = plt.subplots(
        2, 3, figsize=(11.69, 8.27), gridspec_kw={"hspace": 0.3, "wspace": 0.4}
    )
    axs1[1, 2].axis("off")

    for rp, seismic, color, label in scenarios:
        zs_seismic = seismic.zs_seismic if seismic is not None else rp.zs
        VPs = seismic.VPs if seismic is not None else rp.VPs
        VSs = seismic.VSs if seismic is not None else rp.VSs
        rhobs = seismic.rhobs if seismic is not None else rp.rhobs

        for axs in (axs1, axs2):
            axs[0, 0].plot(VPs, zs_seismic, linewidth=1.5, color=color, label=label)
            axs[0, 0].axhline(-rp.WT, color=color, linestyle="--", linewidth=0.5)
            axs[0, 0].set_xlabel("$V_p$ [m/s]")
            axs[0, 0].set_ylabel("$z$ [m]")

            axs[0, 1].plot(VSs, zs_seismic, linewidth=1.5, color=color)
            axs[0, 1].axhline(-rp.WT, color=color, linestyle="--", linewidth=0.5)
            axs[0, 1].set_xlabel("$V_s$ [m/s]")
            axs[0, 1].set_ylabel("$z$ [m]")

            axs[0, 2].plot(rhobs, zs_seismic, linewidth=1.5, color=color)
            axs[0, 2].axhline(-rp.WT, color=color, linestyle="--", linewidth=0.5)
            axs[0, 2].set_xlabel("$\\rho_b$ [kg/$m^3$]")
            axs[0, 2].set_ylabel("$z$ [m]")

        axs1[1, 0].plot(rp.Sws, rp.zs, linewidth=1.5, color=color)
        axs1[1, 0].axhline(-rp.WT, color=color, linestyle="--", linewidth=0.5)
        axs1[1, 0].set_xlim(0, 1.1)
        axs1[1, 0].set_xlabel("$S_w$")
        axs1[1, 0].set_ylabel("$z$ [m]")

        axs1[1, 1].plot(
            rp.poisson_ratios, zs_seismic if seismic is None else rp.zs, linewidth=1.5, color=color
        )
        axs1[1, 1].axhline(-rp.WT, color=color, linestyle="--", linewidth=0.5)
        axs1[1, 1].set_xlabel("Poisson ratio")
        axs1[1, 1].set_ylabel("$z$ [m]")

        if seismic is not None:
            axs2[1, 0].plot(seismic.xs, seismic.ThodPs, linewidth=1.5, color=color)
            axs2[1, 0].set_xlabel("Offset [m]")
            axs2[1, 0].set_ylabel("P- first arrival time [s]")

            axs2[1, 1].plot(seismic.xs, seismic.ThodSs, linewidth=1.5, color=color)
            axs2[1, 1].set_xlabel("Offset [m]")
            axs2[1, 1].set_ylabel("S- first arrival time [s]")

            for mode in range(seismic.n_modes):
                axs2[1, 2].plot(
                    seismic.dispersion_data[mode][:, 0],
                    seismic.dispersion_data[mode][:, 1],
                    linewidth=1.5,
                    color=color,
                )
            axs2[1, 2].set_xlabel("Frequency [Hz]")
            axs2[1, 2].set_ylabel("P-SV phase vel. [m/s]")
        else:
            axs2[1, 0].axis("off")
            axs2[1, 1].axis("off")
            axs2[1, 2].axis("off")

    for axs in (axs1, axs2):
        for ax in axs.flat:
            if ax.has_data():
                ax.grid()

    return page1, page2


def save_report_pdf(
    scenarios: Sequence[tuple[RockPhysicsResult, SeismicResult | None, str, str]],
    path: str | os.PathLike[str],
) -> None:
    """Render :func:`plot_summary_pages` for the given scenarios into a two-page PDF."""
    page1, page2 = plot_summary_pages(scenarios)
    with PdfPages(path) as pdf:
        pdf.savefig(page1, bbox_inches="tight")
        pdf.savefig(page2, bbox_inches="tight")
    plt.close(page1)
    plt.close(page2)
