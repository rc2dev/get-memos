#!/usr/bin/env python3

import requests
import argparse
import sys
from config import Config

MEMOS_API = Config.MEMOS_URL + "/api/v1"
HEADERS = {
    "Authorization": f"Bearer {Config.MEMOS_TOKEN}"
}


def get_memos():
    endpoint = MEMOS_API + "/memos"
    params = {
        "user": Config.MEMOS_USER,
        "pageSize": Config.PAGE_SIZE,
        "sort": "createTime"
    }

    all_memos = []

    while True:
        try:
            response = requests.get(endpoint, headers=HEADERS, params=params)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch memos: {e}", file=sys.stderr)
            return None

        response_dict = response.json()

        page_memos = response_dict.get("memos", [])
        all_memos.extend(page_memos)

        page_token = response_dict.get("nextPageToken")
        if page_token:
            params["pageToken"] = page_token
        else:
            break

    return all_memos


def filter_memos(memos, query):
    return [
        memo for memo in memos 
        if query in memo.get("content", "") 
    ]


def create_markdown(memos, query):
    markdown = f"# Memos with '{query}'\n\n"
    markdown += f"Memos found: {len(memos)}\n\n"
    for memo in memos:
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

    memos = get_memos()
    if memos is None:
        print("Exiting with error.")
        sys.exit(1)

    memos_filtered = filter_memos(memos, args.query)

    output_content = create_markdown(memos_filtered, args.query)
    success = write_markdown(args.output, output_content)
    if not success:
        print("Exiting with error.")
        sys.exit(1)

         
if __name__ == "__main__":
    main()
