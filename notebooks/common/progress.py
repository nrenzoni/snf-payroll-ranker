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
        yield from tqdm(
            iterable,
            desc=desc,
            total=total,
            unit=unit,
            disable=self.disable,
        )
