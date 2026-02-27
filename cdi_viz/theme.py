# ===========================================
# cdi_viz/theme.py
# CDI Visualization Utilities (Internal)
# ===========================================

"""
CDI Visualization Helpers
Publishing standard:
- All plots saved to /figures
- show=False by default for book rendering
- No *_files directories generated
"""

import os
from IPython.display import display, Markdown
import plotly.io as pio
import matplotlib.pyplot as plt


# -------------------------------------------
# CDI Palette
# -------------------------------------------
CDI_PALETTE = {
    "ink": "#374151",
    "title": "#036281",
    "axis": "#9CA3AF",
    "grid": "#E5E7EB",
}


# ===========================================
# 1) Plotly Theme helpers
# ===========================================
def cdi_theme(
    fig,
    *,
    title_x=0.5,
    template="simple_white",
    font_family="Inter, Arial, sans-serif",
    font_size=14,
    showgrid_y=True,
    gridcolor=None,
    margin=None,
    legend_orientation="h",
    legend_y=-0.2,
    legend_x=0,
):
    """Apply CDI styling defaults to a Plotly figure (per-figure)."""
    if gridcolor is None:
        gridcolor = CDI_PALETTE.get("grid", "#E9ECEF")

    if margin is None:
        margin = dict(l=40, r=20, t=70, b=40)

    fig.update_layout(
        template=template,
        title_x=title_x,
        title_font=dict(
            size=18,
            color=CDI_PALETTE.get("title", "#111827"),
            family=font_family,
        ),
        font=dict(
            family=font_family,
            size=font_size,
            color=CDI_PALETTE.get("ink", "#111827"),
        ),
        margin=margin,
        legend=dict(orientation=legend_orientation, y=legend_y, x=legend_x),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=showgrid_y, gridcolor=gridcolor, zeroline=False)
    return fig


def apply_cdi_plotly_theme(*, title_x=0.5, template_name="cdi", base="plotly_white"):
    """Register and set CDI as the default Plotly template globally."""
    pio.templates[template_name] = pio.templates[base]

    pio.templates[template_name].layout.update(
        title_x=title_x,
        title_font=dict(
            size=18,
            color=CDI_PALETTE.get("title", "#036281"),
            family="Inter, Arial, sans-serif",
        ),
        font=dict(
            size=14,
            color=CDI_PALETTE.get("ink", "#374151"),
            family="Inter, Arial, sans-serif",
        ),
        xaxis=dict(
            showline=True,
            linewidth=1,
            linecolor=CDI_PALETTE.get("axis", "#9ca3af"),
            gridcolor=CDI_PALETTE.get("grid", "#e5e7eb"),
            zeroline=False,
        ),
        yaxis=dict(
            showline=True,
            linewidth=1,
            linecolor=CDI_PALETTE.get("axis", "#9ca3af"),
            gridcolor=CDI_PALETTE.get("grid", "#e5e7eb"),
            zeroline=False,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    pio.templates.default = template_name
    return template_name


# ===========================================
# 2) Shared static export system (Plotly + MPL)
# ===========================================
_CDI_STATIC_COUNTER = 0
_CDI_STATIC_PREFIX = ""  # set by cdi_set_chapter("01")


def cdi_set_chapter(prefix: str):
    """Set chapter prefix and reset shared counter (e.g., '01')."""
    global _CDI_STATIC_COUNTER, _CDI_STATIC_PREFIX
    _CDI_STATIC_PREFIX = str(prefix)
    _CDI_STATIC_COUNTER = 0
    return _CDI_STATIC_PREFIX


def _cdi_next_static_path(folder="figures", ext="png"):
    """Generate next figure path: figures/01_001.png, 01_002.png, ..."""
    global _CDI_STATIC_COUNTER, _CDI_STATIC_PREFIX
    _CDI_STATIC_COUNTER += 1
    os.makedirs(folder, exist_ok=True)

    if _CDI_STATIC_PREFIX:
        filename = f"{_CDI_STATIC_PREFIX}_{_CDI_STATIC_COUNTER:03d}.{ext}"
    else:
        filename = f"{_CDI_STATIC_COUNTER:03d}.{ext}"

    return os.path.join(folder, filename)


# ===========================================
# 3) Notebook init (one-liner)
# ===========================================
def cdi_notebook_init(*, chapter: str, title_x=0.5, template_name="cdi"):
    """
    One-liner init for every chapter notebook.

    Example:
        cdi_notebook_init(chapter="12", title_x=0.5)
    """
    apply_cdi_plotly_theme(title_x=title_x, template_name=template_name)
    cdi_set_chapter(str(chapter))


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


# ===========================================
# 4) Export helpers (Plotly + Matplotlib)
# ===========================================
def save_plot_auto_static(fig, folder="figures", scale=2, emit_markdown=True):
    """
    Internal: Save Plotly figure to PNG using the shared chapter counter.
    (Authors should call show_and_save_plotly instead.)
    """
    path = _cdi_next_static_path(folder=folder, ext="png")

    try:
        fig.write_image(path, scale=scale)
        print(f"Saved PNG → {path}")
        if emit_markdown:
            display(Markdown(f"![]({path})"))
    except Exception as e:
        print("PNG export failed. Use Plotly toolbar to download manually.")
        print("Reason:", e)

    return None


def show_and_save_plotly(fig, *, folder="figures", scale=2, show=False, emit_markdown=True):
    """
    Author-facing Plotly helper.

    Default show=False to avoid duplicate outputs in notebooks.
    - show=False => only the saved PNG is displayed (best for Bookdown/GitBook)
    - show=True  => interactive HTML + saved PNG (use during development)
    """
    if show:
        fig.show()
    save_plot_auto_static(fig, folder=folder, scale=scale, emit_markdown=emit_markdown)
    return None


def show_and_save_mpl(
    fig=None,
    *,
    folder="figures",
    dpi=300,
    emit_markdown=True,
    close=True,
):
    """
    Author-facing Matplotlib helper.

    Default emit_markdown=True + close=True:
    - shows the saved PNG (Bookdown-safe)
    - prevents duplicate/empty inline renders in Jupyter
    """
    if fig is None:
        fig = plt.gcf()

    path = _cdi_next_static_path(folder=folder, ext="png")
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    print(f"Saved PNG → {path}")

    if emit_markdown:
        display(Markdown(f"![]({path})"))

    if close:
        plt.close(fig)

    return None


def save_gif_auto(filename, folder="figures", emit_markdown=True):
    """Embed an existing GIF from the figures folder."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    if emit_markdown:
        display(Markdown(f"![]({path})"))
    return None

# ===========================================
# 5) Plotnine CDI theme
# ===========================================

# Optional Plotnine support
try:
    import plotnine as p9
    from plotnine import element_text
    _PLOTNINE_AVAILABLE = True
except Exception:  # pragma: no cover
    p9 = None
    element_text = None
    _PLOTNINE_AVAILABLE = False


def cdi_theme_plotnine(*, base_size=14, legend_position="top"):
    """
    CDI defaults for Plotnine:
    - Centered title
    - Centered subtitle
    - Bold title
    - Legend on top
    """

    if not _PLOTNINE_AVAILABLE:
        raise ImportError("Plotnine is not available. Install plotnine to use this feature.")

    return p9.theme(
        plot_title=element_text(ha="center", weight="bold"),
        plot_subtitle=element_text(ha="center"),
        legend_position=legend_position,
        text=element_text(size=base_size),
    )
def show_and_save_plotnine(
    fig,
    *,
    folder="figures",
    dpi=300,
    apply_cdi_theme=True,
    theme_kwargs=None,
    emit_markdown=True,
    return_fig=False,
    **kwargs
):
    """
    Author-facing Plotnine helper.

    IMPORTANT:
    - Default return_fig=False prevents Plotnine auto-render duplicates in notebooks.
    - We embed the saved PNG via Markdown (book-safe).
    """
    path = _cdi_next_static_path(folder=folder, ext="png")

    out = fig
    if apply_cdi_theme:
        theme_kwargs = theme_kwargs or {}
        out = fig + cdi_theme_plotnine(**theme_kwargs)

    out.save(path, dpi=dpi, verbose=False, **kwargs)
    print(f"Saved PNG → {path}")

    if emit_markdown:
        display(Markdown(f"![]({path})"))

    return out if return_fig else None


# Backward/typo-friendly alias (what you called "plotline")
def show_and_save_plotline(*args, **kwargs):
    return show_and_save_plotnine(*args, **kwargs)

# ===========================================
# 5) Plotly utilities (optional but useful)
# ===========================================
def format_time_axis(fig, *, tickformat="%b %Y", dtick=None, rangeslider=False, showgrid=False):
    fig.update_xaxes(
        tickformat=tickformat,
        dtick=dtick,
        showgrid=showgrid,
        rangeslider=dict(visible=True) if rangeslider else None,
    )
    return fig


def add_event_marker(fig, *, x, y, text="Event", ay=-40, ax=0, arrowhead=2):
    fig.add_annotation(
        x=x,
        y=y,
        text=text,
        showarrow=True,
        arrowhead=arrowhead,
        ax=ax,
        ay=ay,
    )
    return fig


def add_time_window(fig, *, x0, x1, label=None, opacity=0.15):
    fig.add_vrect(x0=x0, x1=x1, opacity=opacity, line_width=0)
    if label:
        fig.add_annotation(
            x=x0,
            y=1.03,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            align="left",
        )
    return fig

