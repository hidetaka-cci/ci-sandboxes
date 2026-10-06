#!/usr/bin/env python3
"""Prefetch Decider + pinned base model into the Hugging Face cache."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_versions() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / "versions.env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k] = v
    return env


def pin_main(hub: Path, repo_id: str, revision: str) -> None:
    """So offline from_pretrained(repo_id) without revision resolves the pin."""
    refs = hub / ("models--" + repo_id.replace("/", "--")) / "refs"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "main").write_text(revision + "\n")
    print(f"pinned {repo_id} main -> {revision}")


def main() -> int:
    versions = load_versions()
    from huggingface_hub import snapshot_download

    hub = Path(
        __import__("os").environ.get(
            "HF_HUB_CACHE",
            str(Path(__import__("os").environ.get("HF_HOME", str(Path.home() / ".cache/huggingface"))) / "hub"),
        )
    )

    decider = snapshot_download(
        versions["DECIDER_HUB_ID"],
        revision=versions["DECIDER_REVISION"],
    )
    base = snapshot_download(
        versions["BASE_MODEL_ID"],
        revision=versions["BASE_MODEL_REVISION"],
    )
    pin_main(hub, versions["DECIDER_HUB_ID"], versions["DECIDER_REVISION"])
    pin_main(hub, versions["BASE_MODEL_ID"], versions["BASE_MODEL_REVISION"])
    print(f"DECIDER_PATH={decider}")
    print(f"BASE_PATH={base}")
    print("prefetch ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
