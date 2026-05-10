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
ggtitle: Any = getattr(lp, "ggtitle")
labs: Any = getattr(lp, "labs")
scale_color_gradient: Any = getattr(lp, "scale_color_gradient")
scale_fill_gradient: Any = getattr(lp, "scale_fill_gradient")
theme_minimal: Any = getattr(lp, "theme_minimal")
