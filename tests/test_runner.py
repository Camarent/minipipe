"""Tests for the Runner interface and the shared data types."""

from pathlib import Path

import pytest

from minipipe import Result, Runner, Shard


class EchoRunner(Runner):
    """Minimal in-memory backend: every shard succeeds and reports its input path as output."""

    def run(self, shards: list[Shard]) -> list[Result]:
        return [Result(id=shard.id, ok=True, output=shard.input_path) for shard in shards]


def test_runner_is_abstract() -> None:
    with pytest.raises(TypeError):
        Runner()  # type: ignore[abstract]


def test_subclass_must_implement_run() -> None:
    class Incomplete(Runner):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_subclass_run_returns_one_result_per_shard_in_order(tmp_path: Path) -> None:
    shards = [Shard(id=f"s{i}", input_path=tmp_path / f"in{i}.txt") for i in range(3)]

    results = EchoRunner().run(shards)

    assert [r.id for r in results] == ["s0", "s1", "s2"]
    assert all(r.ok for r in results)
    assert results[0].output == tmp_path / "in0.txt"


def test_empty_shard_list_gives_empty_results() -> None:
    assert EchoRunner().run([]) == []


def test_result_defaults() -> None:
    result = Result(id="x", ok=False)

    assert result.output is None
    assert result.error is None


def test_shard_and_result_are_frozen(tmp_path: Path) -> None:
    shard = Shard(id="s", input_path=tmp_path / "in.txt")
    result = Result(id="s", ok=True)

    with pytest.raises(AttributeError):
        shard.id = "other"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.ok = False  # type: ignore[misc]
