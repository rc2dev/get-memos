#!/usr/bin/env python3

import requests
import argparse
import sys
from config import Config

MEMOS_API = Config.MEMOS_URL + "/api/v1/memos"
HEADERS = {
    "Authorization": f"Bearer {Config.MEMOS_TOKEN}"
}
PARAMS = {
    "user": Config.MEMOS_USER,
    "pageSize": Config.MAX_MEMOS
}

def get_filtered_memos(query):
    try:
        response = requests.get(MEMOS_API, headers=HEADERS, params=PARAMS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch memos: {e}", file=sys.stderr)
        return None

    response_dict = response.json()
    memos_filtered = [
        memo for memo in response_dict["memos"]
        if query in memo["content"]
    ]
    return memos_filtered

def create_markdown(memos, query):
    markdown = f"# Memos with '{query}'\n\n"
    markdown += f"Memos found: {len(memos)}\n\n"
    for memo in sorted(memos, key=lambda m: m["createTime"]):
        markdown += f"## { memo['createTime'] }\n\n"
        markdown += f"{memo['content'].strip()}\n\n"
    return markdown

def write_markdown(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        print(f"Failed to write file {path}: {e}", file=sys.stderr)
        return False

    print(f"Exported to {path}.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Export memos to markdown file.")
    parser.add_argument("query", help="Tag or any string to filter memos. Use \"\" for all.")
    parser.add_argument("-o", "--output", default=Config.DEFAULT_OUTPUT, help=f"Output markdown file (default: {Config.DEFAULT_OUTPUT})")
    args = parser.parse_args()

    memos_filtered = get_filtered_memos(args.query)
    if memos_filtered is None:
        sys.exit(1)

    output_content = create_markdown(memos_filtered, args.query)
    success = write_markdown(args.output, output_content)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
