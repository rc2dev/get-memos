# get-memos

Export [Memos](https://www.usememos.com/) to a markdown file.

## Requirements

- Python 3.12 or later.
- Python `requests` package.
- Memos 26.10.0 or later.

## Installation

1. Clone the repository.

2. Create a token on your Memos instance.

3. Create your configuration from the example:
   `cp config.sample.toml config.toml && $EDITOR config.toml`.

## Usage

Run `./app.py -h` for usage information.

## Known limitations

This only intends to export text. Attachments are not handled.

## License

Licensed under [GPLv3](LICENSE)

Copyright (C) 2025-2026 [Rafael Cavalcanti](https://rafaelc.org/dev)
