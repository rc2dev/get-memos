#!/usr/bin/env python3

import argparse
import json
import sys
import requests
import tomllib
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import TypedDict

CONFIG_FILE = Path(__file__).parent / "config.toml"


class Memo(TypedDict, total=False):
    content: str
    createTime: str
    name: str


class ConfigError(Exception):
    pass


class FetchError(Exception):
    pass


class WriteError(Exception):
    pass


@dataclass
class Config:
    memos_url: str
    memos_token: str
    memos_user: str
    page_size: int
    default_output: str

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "Config":
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError as e:
            raise ConfigError(f"Missing config file: {path}")
        except OSError as e:
            raise ConfigError(f"Error loading config file: {e}")
        return cls(**data)


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export selected memos to markdown files."
    )
    parser.add_argument(
        "-q", "--query", default=None, help="Substring to search in memo content."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=cfg.default_output,
        help=f"Output directory prefix (default: {cfg.default_output})",
    )
    return parser


def fetch_memos(cfg: Config, query: str | None = None) -> list[Memo]:
    memos_api = cfg.memos_url.rstrip("/") + "/api"

    filters = [f"creator == {json.dumps(f'users/{cfg.memos_user}')}"]
    if query:
        filters.append(f"content.contains({json.dumps(query)})")

    headers = {"Authorization": f"Bearer {cfg.memos_token}"}
    endpoint = memos_api + "/memos"
    params = {
        "filter": " && ".join(filters),
        "pageSize": cfg.page_size,
        "orderBy": "create_time desc",
    }
    timeout = (3, 20)

    all_memos = []

    while True:
        try:
            response = requests.get(
                endpoint, headers=headers, params=params, timeout=timeout
            )
            response.raise_for_status()
            response_dict = response.json()
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Failed to fetch memos: {e}")

        if not isinstance(response_dict, dict):
            raise FetchError("Unexpected API response: not a dictionary.")

        page_memos = response_dict.get("memos")
        if not isinstance(page_memos, list):
            raise FetchError("Unexpected API response: no memos list.")

        all_memos.extend(page_memos)

        page_token = response_dict.get("nextPageToken")
        if page_token:
            params["pageToken"] = page_token
        else:
            break

    return all_memos


def build_memo_markdown(memo: Memo) -> str:
    lines = [
        f"# [MEMO: {memo.get('createTime', '')}]",
        "",
        memo.get("content", "").strip(),
        "",
    ]
    return "\n".join(lines)


def build_memo_filename(memo: Memo) -> str:
    created_time = datetime.fromisoformat(memo["createTime"])
    timestamp = created_time.strftime("%Y-%m-%d_%H-%M-%SZ")
    memo_id = memo["name"].rsplit("/", 1)[-1]
    return f"{timestamp}_{memo_id}.md"


def build_readme_markdown(
    memos: list[Memo], cfg: Config, query: str | None, exported_at: datetime
) -> str:
    lines = [
        "# Exported memos",
        "",
        f"- Exported at: {exported_at.isoformat(sep=' ', timespec='seconds')}",
        f"- Instance: <{cfg.memos_url}>",
        f"- User: {cfg.memos_user}",
        f"- Query: '{query}'" if query else "- No query (all memos)",
        f"- Count: {len(memos)}",
        "",
    ]
    return "\n".join(lines)


def write_memos(path: str, memos: list[Memo], cfg: Config, query: str | None) -> None:
    exported_at = datetime.now().astimezone()
    timestamp = exported_at.strftime("%Y-%m-%d_%H-%M-%S")

    output_base = Path(path)
    directory_name = f"{output_base.name}_{timestamp}"
    output_dir = output_base.parent / directory_name

    try:
        output_dir.mkdir(parents=True)

        (output_dir / "README.md").write_text(
            build_readme_markdown(memos, cfg, query, exported_at), encoding="utf-8"
        )

        for memo in memos:
            memo_path = output_dir / build_memo_filename(memo)
            memo_path.write_text(build_memo_markdown(memo), encoding="utf-8")
    except OSError as e:
        raise WriteError(f"Failed to write memos to {output_dir}: {e}")


def log(message: str) -> None:
    print(message, file=sys.stderr)


def fatal(e: Exception) -> None:
    log(str(e))
    sys.exit(1)


def main() -> None:
    try:
        cfg = Config.load()
    except ConfigError as e:
        fatal(e)

    parser = build_parser(cfg)
    args = parser.parse_args()

    try:
        memos = fetch_memos(cfg, args.query)
    except FetchError as e:
        fatal(e)

    try:
        write_memos(args.output, memos, cfg, args.query)
    except WriteError as e:
        fatal(e)


if __name__ == "__main__":
    main()
