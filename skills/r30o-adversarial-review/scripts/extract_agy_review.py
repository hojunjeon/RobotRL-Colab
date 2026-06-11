from __future__ import annotations

import argparse
import json
from pathlib import Path


def extract(conversation_id: str, output: Path) -> None:
    transcript = (
        Path.home()
        / ".gemini"
        / "antigravity-cli"
        / "brain"
        / conversation_id
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    if not transcript.exists():
        raise FileNotFoundError(transcript)

    chunks: list[str] = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("source") != "MODEL":
            continue
        for key in ("content", "text", "message"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n---\n\n".join(chunks), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Antigravity model text from a CLI conversation transcript.")
    parser.add_argument("conversation_id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extract(args.conversation_id, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
