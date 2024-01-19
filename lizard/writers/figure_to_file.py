"""
This function is a wrapper around the matplotlib.pyplot.savefig function, which
combines the output directory of all figures with the actual figure filename.

Usage:
write_figure(fig, 'test.png', dpi=300, ...)
"""


import os

from dotenv import load_dotenv

load_dotenv()


def write_figure(fig, filename, verbose=True, **kwargs):
    """
    Saves figure at the pre-defined location

    Parameters
    ----------
    fig: figure object
    filename: output location and filename
    verbose: prints the output location
    kwargs: plt.savefig parameters

    Returns
    -------
    None
    """

    outfile = os.path.join(os.environ["PATH_PLT"], filename)
    fig.savefig(outfile, **kwargs)

    if verbose:
        print(f"Created figure file: {outfile}")
