"""Optional live DeepSeek integration check.

The default path performs no network call. A real call requires both --live
and an API key from --api-key or DEEPSEEK_API_KEY.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from l1_data import FileMarkdownLoader
from l2_modeling import DeepSeekClient, L2Orchestrator, RawDocument


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optional live L2 DeepSeek test.")
    parser.add_argument("markdown", type=Path, help="Input Markdown file")
    parser.add_argument("--live", action="store_true", help="Actually call DeepSeek")
    parser.add_argument("--api-key", default=None, help="API key; defaults to DEEPSEEK_API_KEY")
    parser.add_argument("--model", default=None, help="DeepSeek model name")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL")
    parser.add_argument("--max-rounds", type=int, default=5)
    args = parser.parse_args(argv)

    if not args.live:
        print("Live DeepSeek test skipped. Re-run with --live and an API key to enable network calls.")
        return 0

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        parser.error("--live requires --api-key or the DEEPSEEK_API_KEY environment variable")

    l1_document = FileMarkdownLoader().load(args.markdown)
    raw_document = RawDocument.from_markdown_document(l1_document)
    client = DeepSeekClient(api_key=api_key, model=args.model, base_url=args.base_url)
    result = L2Orchestrator(client).run(raw_document, max_interaction_rounds=args.max_rounds)
    print(result.model_dump_json(indent=2))
    return 0 if result.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())