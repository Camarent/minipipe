"""Generate realistic log sources for local runs and the compose stub.

Stdlib only, so it runs in a bare python image with no install step.

The distribution is deliberate: PLANTED_MESSAGE ranks #6 in every source but #1
once sources are combined. Merging per-source top-N loses it; aggregating raw
entries finds it.
"""

import argparse
import random
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

LEVELS = ["DEBUG", "INFO", "INFO", "WARNING", "ERROR"]
UNIQUE_PER_SOURCE = 5
PLANTED_MESSAGE = "Database connection pool exhausted"

NOISE = [
    "Request completed",
    "Cache miss for key",
    "Retrying upstream call",
    "Config reloaded",
    "Session expired",
    "Disk usage above threshold",
    "Slow query detected",
    "Connection reset by peer",
]


def build_counts(index: int, total: int) -> dict[str, int]:
    """Message -> occurrences for one source, with the planted message at rank 6."""
    skeleton = max(60, total * 30 // 100)
    k = max(2, (skeleton - UNIQUE_PER_SOURCE) // (UNIQUE_PER_SOURCE + 1))

    counts = {f"Source {index} failure mode {u}": k + 1 for u in range(UNIQUE_PER_SOURCE)}
    counts[PLANTED_MESSAGE] = k

    remaining = total - sum(counts.values())
    cap = max(1, k // 2)  # shared across sources, so global noise stays under S*k
    variant = 0
    while remaining > 0:
        for template in NOISE:
            if remaining <= 0:
                break
            message = template if variant == 0 else f"{template} (variant {variant})"
            take = min(cap, remaining)
            counts[message] = take
            remaining -= take
        variant += 1
    return counts


def level_for(message: str) -> str:
    """Stable across sources — stats are keyed on (level, message)."""
    return LEVELS[zlib.crc32(message.encode()) % len(LEVELS)]


def render(
    counts: dict[str, int],
    start: datetime,
    days: int,
    rng: random.Random,
    malformed: int,
) -> list[str]:
    span = int(timedelta(days=days).total_seconds())
    entries: list[tuple[datetime, str]] = []
    for message, n in counts.items():
        level = level_for(message)
        for _ in range(n):
            stamp = start + timedelta(seconds=rng.randrange(span))
            entries.append((stamp, f"{stamp.isoformat()} {level} {message}"))

    for _ in range(malformed):
        stamp = start + timedelta(seconds=rng.randrange(span))
        entries.append((stamp, rng.choice(["<<truncated", "NOT A LOG LINE", ""])))

    entries.sort(key=lambda e: e[0])
    return [line for _, line in entries]


def write_config(out: Path, names: list[str], base_url: str) -> None:
    lines = ["[sources]"]
    lines += [f'{name} = "{base_url.rstrip("/")}/{name}.log"' for name in names]
    lines.append(f'missing = "{base_url.rstrip("/")}/does-not-exist.log"')
    (out / "sources.toml").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=int, default=8)
    parser.add_argument("--lines", type=int, default=5000, help="lines per source")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--malformed", type=int, default=1, help="bad lines per source")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data"))
    parser.add_argument("--base-url", help="also write a sources.toml using this base URL")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    start = datetime(2026, 7, 13, tzinfo=UTC)
    args.out.mkdir(parents=True, exist_ok=True)

    names = [f"app{i + 1}" for i in range(args.sources)]
    for index, name in enumerate(names):
        counts = build_counts(index, args.lines)
        lines = render(counts, start, args.days, rng, args.malformed)
        (args.out / f"{name}.log").write_text("\n".join(lines) + "\n")
        print(f"{name}.log: {len(lines)} lines")

    if args.base_url:
        write_config(args.out, names, args.base_url)
        print(f"sources.toml: {len(names)} sources + 1 intentionally missing")


if __name__ == "__main__":
    main()
