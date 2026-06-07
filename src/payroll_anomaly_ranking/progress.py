from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol, TypeVar

T = TypeVar("T")


class ProgressReporter(Protocol):
    def iter(
        self,
        iterable: Iterable[T],
        *,
        desc: str,
        total: int | None = None,
        unit: str = "it",
    ) -> Iterator[T]: ...


@dataclass(frozen=True)
class NoProgress:
    def iter(
        self,
        iterable: Iterable[T],
        *,
        desc: str,
        total: int | None = None,
        unit: str = "it",
    ) -> Iterator[T]:
        yield from iterable


@dataclass
class SharedStepProgress:
    steps: Iterator[object]

    def iter(
        self,
        iterable: Iterable[T],
        *,
        desc: str,
        total: int | None = None,
        unit: str = "it",
    ) -> Iterator[T]:
        del desc, total, unit
        for item in iterable:
            next(self.steps, None)
            yield item


def progress_or_none(progress: ProgressReporter | None) -> ProgressReporter:
    return progress if progress is not None else NoProgress()
