# get-memos

Export [Memos](https://www.usememos.com/) to a markdown file.

## Installation

1. Clone the repository.

2. Make sure you have Python's `requests` module installed.

3. Create a token on your Memos instance.

4. Create your configuration from the example:
   `cp config_example.py config.py && $EDITOR config.py`.

## Usage

Run `./app.py -h` for usage information.

## Known limitations

This only intends to export text. Attachments are not handled.

## License

Licensed under [GPLv3](LICENSE)

Copyright (C) 2025 [Rafael Cavalcanti](https://rafaelc.org/dev)
