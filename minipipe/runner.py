"""Runner interface and the data types shared by all execution backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Shard:
    """One unit of work: an identifier and the input file it reads."""

    id: str
    input_path: Path


@dataclass(frozen=True)
class Result:
    """Outcome of one shard. ``error`` holds the failure text when ``ok`` is False."""

    id: str
    ok: bool
    output: Path | None = None
    error: str | None = None


class Runner(ABC):
    """Execute shards and return one Result per shard, in input order."""

    @abstractmethod
    def run(self, shards: list[Shard]) -> list[Result]:
        """Run every shard and return its Result."""
