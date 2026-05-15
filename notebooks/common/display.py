from __future__ import annotations

from common.plots import LetsPlot
from itables import init_notebook_mode


def setup_notebook_html() -> None:
    """Configure notebook HTML rendering for plots and tabular outputs."""
    LetsPlot.setup_html()
    init_notebook_mode(all_interactive=True, connected=True)
