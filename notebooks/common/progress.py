from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TypeVar

from tqdm.auto import tqdm

T = TypeVar("T")


@dataclass(frozen=True)
class TqdmProgress:
    disable: bool = False

    def iter(
        self,
        iterable: Iterable[T],
        *,
        desc: str,
        total: int | None = None,
        unit: str = "it",
    ) -> Iterator[T]:
        bar = tqdm(
            iterable,
            desc=desc,
            total=total,
            unit=unit,
            disable=self.disable,
            mininterval=0.25,
            miniters=1,
        )
        if not self.disable:
            bar.refresh()
        try:
            yield from bar
        finally:
            bar.close()
