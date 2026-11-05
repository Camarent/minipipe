# minipipe

[![CI](https://github.com/Camarent/minipipe/actions/workflows/ci.yml/badge.svg)](https://github.com/Camarent/minipipe/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Camarent/minipipe/graph/badge.svg)](https://codecov.io/gh/Camarent/minipipe)

minipipe is a minimal pipeline runner. It splits work into shards, runs each shard through a pluggable `Runner` backend, and reports one `Result` per shard. A shard that fails does not stop the others.

The `Runner` interface is `run(shards: list[Shard]) -> list[Result]`. `Shard` holds an `id` and an `input_path`. `Result` holds `id`, `ok`, `output` and `error`.

The only backend today is `LocalRunner`, which runs each shard in a separate process. Planned backends: Slurm and Kubernetes.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.11 or newer. Standard library only at runtime.

## Usage

The task function must be defined at module level, because `LocalRunner` pickles it to send it to worker processes. Save this as `example.py` and run `python example.py`:

```python
import tempfile
from pathlib import Path

from minipipe import Shard
from minipipe.local import LocalRunner


def count_lines(shard: Shard) -> Path:
    """Task: write the line count of the shard input next to it."""
    output = shard.input_path.with_suffix(".count")
    output.write_text(str(len(shard.input_path.read_text().splitlines())))
    return output


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        shards = []
        for name in ("a", "b"):
            path = Path(tmp) / f"{name}.txt"
            path.write_text("one\ntwo\n")
            shards.append(Shard(id=name, input_path=path))
        for result in LocalRunner(count_lines).run(shards):
            print(result.id, result.ok, result.output.read_text() if result.ok else result.error)
```

Output:

```
a True 2
b True 2
```

A task that raises gives `ok=False` and the error text in `error`; the other shards still run.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

`pytest` runs the tests in `tests/` and reports coverage for `minipipe`.
