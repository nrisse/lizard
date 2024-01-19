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
