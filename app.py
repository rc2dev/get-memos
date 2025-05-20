#!/usr/bin/env python3

import requests
import argparse
from config import Config

MEMOS_API = Config.MEMOS_URL + "/api/v1/memos"
HEADERS = {
    "Authorization": f"Bearer {Config.MEMOS_TOKEN}"
}
PARAMS = {
    "user": Config.MEMOS_USER,
    "pageSize": Config.MAX_MEMOS
}

def get_filtered_memos(filter):
    response = requests.get(MEMOS_API, headers=HEADERS, params=PARAMS)
    response.raise_for_status()
    response_dict = response.json()

    memos_filtered = [
        memo for memo in response_dict["memos"]
        if filter in memo["content"]
    ]
    return memos_filtered

def create_markdown(memos, filter):
    markdown = f"# Memos with '{filter}'\n\n"
    markdown += f"Memos found: {len(memos)}\n\n"
    for memo in sorted(memos, key=lambda m: m["createTime"]):
        markdown += f"## { memo['createTime'] }\n\n"
        markdown += f"{memo['content'].strip()}\n\n"
    return markdown

def write_markdown(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Export memos to markdown file.")
    parser.add_argument("filter", help="Tag or string to filter memos")
    args = parser.parse_args()

    memos_filtered = get_filtered_memos(args.filter)
    md = create_markdown(memos_filtered, args.filter)
    write_markdown("memos.md", md)
    print("Done.")

if __name__ == "__main__":
    main()
