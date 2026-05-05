#!/usr/bin/env python3

import argparse
import sys
import requests
from config import Config
from typing import List, Dict, Any

MEMOS_API = Config.MEMOS_URL + "/api/v1"
HEADERS = {"Authorization": f"Bearer {Config.MEMOS_TOKEN}"}

Memo = Dict[str, Any]


class FetchError(Exception):
    pass


class WriteError(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export memos to markdown file.")
    parser.add_argument(
        "-q", "--query", default=None, help="Tag or any string to filter memos."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=Config.DEFAULT_OUTPUT,
        help=f"Output markdown file (default: {Config.DEFAULT_OUTPUT})",
    )
    return parser


def fetch_memos() -> List[Memo]:
    endpoint = MEMOS_API + "/memos"
    params = {
        "user": Config.MEMOS_USER,
        "pageSize": Config.PAGE_SIZE,
        "sort": "createTime",
    }

    all_memos = []

    while True:
        try:
            response = requests.get(endpoint, headers=HEADERS, params=params)
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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        memos = fetch_memos()
    except FetchError as e:
        log(e)
        sys.exit(1)

    memos_filtered = filter_memos(memos, args.query) if args.query else memos

    md_content = build_markdown(memos_filtered, args.query)

    try:
        write_markdown(args.output, md_content)
    except WriteError as e:
        log(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
