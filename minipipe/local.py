"""Local backend: runs each shard in its own worker process."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from pathlib import Path

from minipipe.runner import Result, Runner, Shard


class LocalRunner(Runner):
    """Run shards in a process pool. ``task`` must be a module-level callable (it is pickled)."""

    def __init__(self, task: Callable[[Shard], Path | None]) -> None:
        self.task = task

    def run(self, shards: list[Shard]) -> list[Result]:
        """Run every shard; a raising shard gives ``ok=False`` and the other shards still finish."""
        if not shards:
            return []
        with ProcessPoolExecutor() as pool:
            futures = [pool.submit(self.task, shard) for shard in shards]
            return [self._collect(shard, future) for shard, future in zip(shards, futures, strict=True)]

    @staticmethod
    def _collect(shard: Shard, future: Future[Path | None]) -> Result:
        try:
            return Result(id=shard.id, ok=True, output=future.result())
        except Exception as exc:  # noqa: BLE001 - any shard failure is reported as ok=False
            return Result(id=shard.id, ok=False, error=str(exc) or type(exc).__name__)
