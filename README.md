# md-batch-gpt

Poetry-managed Python 3.11 project.

## Installation

Install the project's dependencies using Poetry:

```bash
poetry install
```

## Usage

Run the batch processor against the `docs` folder using the provided prompts:

```bash
poetry run mdgpt run docs --prompts prompts/first.txt prompts/second.txt
```

Generate images from JSON description files. Each object in the JSON array must
include an `expected_filename` and a `summary` field. `summary` provides the
prompt text while `expected_filename` specifies the output file name; any other
keys (for example `alt_text`) are ignored.
```bash
poetry run mdgpt generate-images images.json --model gpt-image-1 --size 1024x1024
```

## .env Setup

The application requires an OpenAI API key. Create a `.env` file in the project
root containing:

```bash
OPENAI_API_KEY=<your-api-key>
```

Alternatively, set `OPENAI_API_KEY` in your shell environment before running
the commands above.
