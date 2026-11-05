"""Tests for LocalRunner: process-pool execution of shards."""

from pathlib import Path

from minipipe import Result, Runner, Shard
from minipipe.local import LocalRunner


def write_output(shard: Shard) -> Path:
    """Module-level task (must be picklable): writes the shard id to a file next to its input."""
    out = shard.input_path.with_suffix(".out")
    out.write_text(shard.id, encoding="utf-8")
    return out


def fail_on_bad(shard: Shard) -> Path | None:
    """Module-level task: raises for the shard id 'bad', succeeds for every other shard."""
    if shard.id == "bad":
        raise ValueError("bad shard input")
    return write_output(shard)


def fail_without_message(_shard: Shard) -> Path | None:
    """Module-level task: raises an exception with an empty message."""
    raise KeyError()


def test_local_runner_is_a_runner() -> None:
    assert isinstance(LocalRunner(write_output), Runner)


def test_all_ok_run_returns_outputs_in_input_order(tmp_path: Path) -> None:
    shards = [Shard(id=f"s{i}", input_path=tmp_path / f"in{i}.txt") for i in range(4)]

    results = LocalRunner(write_output).run(shards)

    assert [r.id for r in results] == ["s0", "s1", "s2", "s3"]
    assert all(r.ok for r in results)
    assert all(r.error is None for r in results)
    for shard, result in zip(shards, results, strict=True):
        assert result.output == shard.input_path.with_suffix(".out")
        assert result.output is not None
        assert result.output.read_text(encoding="utf-8") == shard.id


def test_one_failing_shard_does_not_stop_the_others(tmp_path: Path) -> None:
    shards = [
        Shard(id="a", input_path=tmp_path / "a.txt"),
        Shard(id="bad", input_path=tmp_path / "bad.txt"),
        Shard(id="c", input_path=tmp_path / "c.txt"),
    ]

    results = LocalRunner(fail_on_bad).run(shards)

    assert [r.id for r in results] == ["a", "bad", "c"]
    assert [r.ok for r in results] == [True, False, True]
    assert results[1] == Result(id="bad", ok=False, error="bad shard input")
    assert results[0].output == tmp_path / "a.out"
    assert results[2].output == tmp_path / "c.out"
    assert (tmp_path / "c.out").read_text(encoding="utf-8") == "c"


def test_failure_without_message_reports_exception_type(tmp_path: Path) -> None:
    results = LocalRunner(fail_without_message).run([Shard(id="s", input_path=tmp_path / "s.txt")])

    assert results == [Result(id="s", ok=False, error="KeyError")]


def test_empty_shard_list_returns_empty_list_without_pool() -> None:
    assert LocalRunner(write_output).run([]) == []
