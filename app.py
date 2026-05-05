#!/usr/bin/env python3

import argparse
import sys
import requests
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

CONFIG_FILE = Path(__file__).parent / "config.toml"


Memo = Dict[str, Any]


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
    parser = argparse.ArgumentParser(description="Export memos to markdown file.")
    parser.add_argument(
        "-q", "--query", default=None, help="Tag or any string to filter memos."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=cfg.default_output,
        help=f"Output markdown file (default: {cfg.default_output})",
    )
    return parser


def fetch_memos(cfg: Config) -> List[Memo]:
    memos_api = cfg.memos_url + "/api/v1"
    headers = {"Authorization": f"Bearer {cfg.memos_token}"}
    endpoint = memos_api + "/memos"
    params = {
        "user": cfg.memos_user,
        "pageSize": cfg.page_size,
        "sort": "createTime",
    }

    all_memos = []

    while True:
        try:
            response = requests.get(endpoint, headers=headers, params=params)
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


def filter_memos(memos: List[Memo], query: str) -> List[Memo]:
    if not query:
        return memos

    return [m for m in memos if query in m.get("content", "")]


def build_markdown(memos: List[Memo], query: str) -> str:
    lines = []

    lines.append("# Exported memos")
    lines.append("")
    lines.append(f"- Query: '{query}'" if query else "- No query, all memos")
    lines.append(f"- Count: {len(memos)}")
    lines.append("")

    for memo in memos:
        lines.append(f"## { memo.get('createTime', '') }")
        lines.append("")
        lines.append(f"{memo.get('content', '').strip()}")
        lines.append("")

    markdown = "\n".join(lines)
    return markdown


def write_markdown(path: str, content: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        raise WriteError(f"Failed to write file {path}: {e}")

    print(f"Exported to {path}.")


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
        memos = fetch_memos(cfg)
    except FetchError as e:
        fatal(e)

    memos_filtered = filter_memos(memos, args.query) if args.query else memos

    md_content = build_markdown(memos_filtered, args.query)

    try:
        write_markdown(args.output, md_content)
    except WriteError as e:
        fatal(e)


if __name__ == "__main__":
    main()
