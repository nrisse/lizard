"""
Tools for matplotlib legend
"""

import matplotlib.colors as mcolors
import numpy as np


def fancy_legend(ax, legend_params):
    """
    Removes markers and colors label in marker color

    Parameters
    ----------
    ax: axis on where to plot legend an from where to get legend content
    legend_params: parameters for legend such as fontsize
    """

    leg = ax.legend(
        frameon=False, handlelength=0, handletextpad=0, **legend_params
    )

    handles = leg.legendHandles
    texts = leg.get_texts()

    for i in range(len(handles)):
        # get color of handle
        try:
            color = handles[i].get_c()

        except AttributeError:
            color = handles[i].get_fc()

        if isinstance(color, np.ndarray):
            color = mcolors.to_hex(color)

        # make handle invisible
        handles[i].set_visible(False)

        # change color of text to color of handle
        texts[i].set_color(color)


def add_scale(ax, width, step, proj, annotation_params=dict()):
    """
    Adds km-scale on cartopy map in the lower left corner. The scale can be
    modified in many ways.

    The scale bar is shown on the very top of the figure.

    (x0, y0): lower left corner of scale bar
    (y1, y1): upper left corner of scale bar
    x=(), y=(y0, y1): discrete bins of scale bar

    Parameters
    ----------
    ax: axis to add the scale on.
    width: scale width in km (e.g. 100 km).
    step: step of color scale in km (e.g. 25 km).
    proj: map projection.
    """

    assert (
        width / step % 2 == 0
    ), "Scale with divided by step must be an even number"

    # coordinates to m
    width = width * 1e3
    step = step * 1e3

    # get point on map coordinates that is 10% from the lower left corner
    xl0, xl1 = ax.get_xlim()
    yl0, yl1 = ax.get_ylim()
    dx = 0.02 * (xl1 - xl0)
    dy = 0.02 * (yl1 - yl0)
    x0 = xl0 + dx
    y0 = yl0 + dy

    height = 0.1 * width
    y1 = y0 + height
    x1 = x0 + width
    x = np.arange(x0, x1, step) + step / 2
    y = np.array([y0, y1])
    c = np.array([[0, 1] * int(len(x) / 2), [0, 1] * int(len(x) / 2)])

    ax.annotate(
        f"{int(width*1e-3)} km",
        xy=(x0, y1),
        ha="left",
        va="bottom",
        transform=proj,
        zorder=98,
        **annotation_params,
    )
    ax.pcolormesh(
        x, y, c, cmap="Greys", transform=proj, shading="nearest", zorder=99
    )
