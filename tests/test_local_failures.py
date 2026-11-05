"""Failure modes of LocalRunner: a crashed worker process and an unpicklable task."""

import os
from pathlib import Path

from minipipe import Result, Shard
from minipipe.local import LocalRunner


def crash_on_bad(shard: Shard) -> Path | None:
    """Module-level task: kills the worker process for the shard id 'bad' (no exception, no cleanup)."""
    if shard.id == "bad":
        os._exit(1)
    return shard.input_path.with_suffix(".out")


def test_crashed_worker_gives_ok_false_without_raising(tmp_path: Path) -> None:
    shards = [Shard(id="bad", input_path=tmp_path / "bad.txt")]

    results = LocalRunner(crash_on_bad).run(shards)

    assert len(results) == 1
    assert results[0].id == "bad"
    assert results[0].ok is False
    assert results[0].output is None
    assert results[0].error


def test_crashed_worker_among_others_gives_ok_false_for_each_without_raising(tmp_path: Path) -> None:
    shards = [Shard(id="bad", input_path=tmp_path / "bad.txt")]
    shards += [Shard(id=f"s{i}", input_path=tmp_path / f"s{i}.txt") for i in range(4)]

    results = LocalRunner(crash_on_bad).run(shards)

    assert [r.id for r in results] == [s.id for s in shards]
    assert results[0].ok is False
    assert results[0].error
    for result in results:
        # Other shards may finish before the pool breaks; any that did not must carry an error text.
        assert result.ok or result.error


def test_unpicklable_task_gives_ok_false_without_hanging(tmp_path: Path) -> None:
    shards = [Shard(id="s", input_path=tmp_path / "s.txt")]

    results = LocalRunner(lambda shard: shard.input_path).run(shards)

    assert len(results) == 1
    assert results[0] == Result(id="s", ok=False, error=results[0].error)
    assert results[0].error
