from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any


# =====================================================
# CDI figure state (shared naming across backends)
# =====================================================
@dataclass
class _CDIState:
    chapter: str = "01"
    fig_counter: int = 0


_STATE = _CDIState()


def cdi_notebook_init(chapter: str) -> None:
    """Initialize chapter-level state for consistent figure naming."""
    _STATE.chapter = str(chapter).zfill(2)
    _STATE.fig_counter = 0
    Path("figures").mkdir(exist_ok=True)
    Path("docs/assets").mkdir(parents=True, exist_ok=True)


# =====================================================
# Matplotlib (minimal)
# =====================================================
def cdi_plot_style() -> None:
    """Minimal, consistent Matplotlib defaults for CDI lessons."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.figsize": (7.2, 4.6),
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })


def show_and_save_mpl(fig: Optional[Any] = None, dpi: int = 160) -> str:
    """Save the current Matplotlib figure into figures/{chapter}_{counter}.png."""
    import matplotlib.pyplot as plt

    if fig is None:
        fig = plt.gcf()
    _STATE.fig_counter += 1
    out = Path("figures") / f"{_STATE.chapter}_{_STATE.fig_counter:03d}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.show()
    return str(out)


# =====================================================
# Plotnine (minimal helper, optional dependency)
# =====================================================
def cdi_plotnine_theme(
    *,
    title_size: int = 15,
    subtitle_size: int = 11,
    axis_title_size: int = 12,
    axis_text_size: int = 11,
    legend_title_size: int = 11,
    legend_text_size: int = 11,
):
    """Return a CDI-styled Plotnine theme."""
    try:
        from plotnine import theme_minimal, theme, element_text
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "Plotnine is required for cdi_plotnine_theme(). Install it with: pip install plotnine"
        ) from e

    return (
        theme_minimal()
        + theme(
            plot_title=element_text(weight="bold", size=title_size),
            plot_subtitle=element_text(size=subtitle_size),
            axis_title=element_text(weight="bold", size=axis_title_size),
            axis_text=element_text(size=axis_text_size),
            legend_title=element_text(weight="bold", size=legend_title_size),
            legend_text=element_text(size=legend_text_size),
        )
    )


def save_plotnine(p, *, filename: Optional[str] = None, dpi: int = 160) -> str:
    """Save a Plotnine plot to figures/ with CDI naming."""
    _STATE.fig_counter += 1
    out = Path(filename) if filename else Path("figures") / f"{_STATE.chapter}_{_STATE.fig_counter:03d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    p.save(str(out), dpi=dpi, verbose=False)
    return str(out)


# =====================================================
# Plotly (the reason we needed theme.py)
# =====================================================
def cdi_plotly_style(fig: Any, *, title: Optional[str] = None, subtitle: Optional[str] = None) -> Any:
    """Apply a minimal CDI Plotly layout.

    - Centers title
    - Uses a smaller subtitle (in HTML title)
    - Keeps a clean white background
    - Uses top legend by default (can be overridden in lesson code)

    Notes:
    - Plotly doesn't have a native subtitle field; we use HTML in the title.
    """
    if title is not None:
        if subtitle:
            full = f"{title}<br><span style='font-size:0.85em;color:#475569'>{subtitle}</span>"
        else:
            full = title
        fig.update_layout(title={"text": full, "x": 0.5})

    fig.update_layout(
        template="plotly_white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
        margin={"l": 60, "r": 30, "t": 80, "b": 60},
    )
    return fig


def save_plotly_html(fig: Any, *, filename: Optional[str] = None) -> str:
    """Save an interactive Plotly figure to docs/assets/ with CDI naming."""
    _STATE.fig_counter += 1
    out = Path(filename) if filename else Path("docs/assets") / f"{_STATE.chapter}_{_STATE.fig_counter:03d}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out))
    return str(out)
