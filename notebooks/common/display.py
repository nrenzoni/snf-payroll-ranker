from __future__ import annotations

import polars as pl
from common.plots import LetsPlot
from itables import init_notebook_mode


def setup_notebook_html() -> None:
    """Configure notebook HTML rendering for plots and tabular outputs."""
    LetsPlot.setup_html()
    init_notebook_mode(all_interactive=True, connected=True)


def setup_polars_display() -> None:
    """Configure Polars DataFrame plain-text output for AI-friendly review."""
    pl.Config(
        tbl_formatting="MARKDOWN",
        tbl_hide_column_data_types=False,
        tbl_cols=30,
        tbl_width_chars=300,
        fmt_str_lengths=300,
    )
