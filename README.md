# md-batch-gpt

Utilities for generating visual art at scale. This project grew out of an
earlier automation approach known as the **two prong** workflow and is focused
on producing image assets from structured prompts. Poetry-managed Python 3.11
project.

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

Generate images from JSON description files. Each entry must include
`expected_filename` and `summary` keys. Any additional fields are ignored.
The prompt text comes from `summary`, and the resulting image is saved to
`expected_filename`.

```bash
poetry run mdgpt generate-images images1.json images2.json --model gpt-image-1 --size 1024x1024
```

## .env Setup

The application requires an OpenAI API key. Create a `.env` file in the project
root containing:

```bash
OPENAI_API_KEY=<your-api-key>
```

Alternatively, set `OPENAI_API_KEY` in your shell environment before running
the commands above.
