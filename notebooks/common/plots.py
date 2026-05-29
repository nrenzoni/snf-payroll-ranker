from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import lets_plot as lp

_RENDER_ERROR_PATTERNS = (
    re.compile(r'"__error_message"\s*:\s*"(?P<message>[^"]+)"'),
    re.compile(r"Can't convert to number: (?P<message>[^<\n]+)"),
    re.compile(r"Error loading Lets-Plot JS"),
)
_raw_ggplot: Any = getattr(lp, "ggplot")


class LetsPlotRenderError(RuntimeError):
    """Raised when Lets-Plot embeds a render error in generated HTML."""


def _raise_for_render_errors(html: str) -> None:
    for pattern in _RENDER_ERROR_PATTERNS:
        match = pattern.search(html)
        if match is None:
            continue
        message = match.groupdict().get("message") or match.group(0)
        raise LetsPlotRenderError(f"Lets-Plot render error: {message}")


@dataclass(frozen=True)
class CheckedPlot:
    _plot: Any

    def __add__(self, other: Any) -> CheckedPlot:
        return CheckedPlot(self._plot + other)

    def __radd__(self, other: Any) -> CheckedPlot:
        return CheckedPlot(other + self._plot)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._plot, name)

    def as_dict(self) -> dict[str, Any]:
        return self._plot.as_dict()

    def to_html(self, *args: Any, **kwargs: Any) -> str:
        html = self._plot.to_html(*args, **kwargs)
        _raise_for_render_errors(html)
        return html

    def _repr_html_(self) -> str:
        html = self._plot._repr_html_()
        _raise_for_render_errors(html)
        return html

    def __repr__(self) -> str:
        plot_dict = self.as_dict()

        mapping = plot_dict.get("mapping", {})
        active_cols = [val for key, val in mapping.items() if isinstance(val, str)]

        # Extract columns from all layers
        layers = plot_dict.get("layers", [])
        for layer in layers:
            layer_mapping = layer.get("mapping", {})
            layer_cols = [
                val for key, val in layer_mapping.items() if isinstance(val, str)
            ]
            active_cols.extend(layer_cols)

        # Deduplicate columns, preserve ordering
        active_cols = list(dict.fromkeys(active_cols))

        raw_data = plot_dict.get("data")
        df_str: str | None = None

        if raw_data is None:
            raise Exception("no data to render")

        if hasattr(raw_data, "select") and callable(
            getattr(raw_data, "select"),
        ):  # Polars DataFrame
            filtered_df = raw_data.select(active_cols)
            df_str = str(filtered_df)
        elif hasattr(raw_data, "filter") and hasattr(
            raw_data,
            "to_string",
        ):  # Pandas DataFrame
            filtered_df = raw_data[active_cols]
            df_str = filtered_df.to_string(index=False)
        else:
            raise Exception("raw_data must be polars or pandas DataFrame")

        title = plot_dict.get("ggtitle", {}).get("text", "ggplot Output")

        return f"=== DataFrame for: {title} ===\n{df_str}"

    def _repr_mimebundle_(self, include=None, exclude=None) -> dict[str, Any]:
        html_content = self._plot._repr_html_()
        _raise_for_render_errors(html_content)

        return {
            "text/plain": repr(self),
            "text/html": html_content,
        }

    def show(self, *args: Any, **kwargs: Any) -> Any:
        self.to_html()
        return self._plot.show(*args, **kwargs)


def ggplot(*args: Any, **kwargs: Any) -> CheckedPlot:
    return CheckedPlot(_raw_ggplot(*args, **kwargs))


LetsPlot: Any = getattr(lp, "LetsPlot")
aes: Any = getattr(lp, "aes")
coord_flip: Any = getattr(lp, "coord_flip")
geom_density: Any = getattr(lp, "geom_density")
geom_bar: Any = getattr(lp, "geom_bar")
geom_errorbar: Any = getattr(lp, "geom_errorbar")
geom_histogram: Any = getattr(lp, "geom_histogram")
geom_line: Any = getattr(lp, "geom_line")
geom_point: Any = getattr(lp, "geom_point")
geom_vline: Any = getattr(lp, "geom_vline")
geom_segment: Any = getattr(lp, "geom_segment")
geom_tile: Any = getattr(lp, "geom_tile")
gggrid: Any = getattr(lp, "gggrid")
ggtitle: Any = getattr(lp, "ggtitle")
labs: Any = getattr(lp, "labs")
scale_color_gradient: Any = getattr(lp, "scale_color_gradient")
scale_fill_gradient: Any = getattr(lp, "scale_fill_gradient")
element_text: Any = getattr(lp, "element_text")
theme: Any = getattr(lp, "theme")
theme_minimal: Any = getattr(lp, "theme_minimal")


def rotated_x_labels() -> Any:
    return theme(axis_text_x=element_text(angle=45, hjust=1))
