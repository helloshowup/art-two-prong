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

This will install all required libraries, including `requests`, which is used to
download generated images from the OpenAI API.

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

Images can also be generated directly from Markdown or JSON files. Markdown
documents may begin with YAML front-matter providing `expected_filename` and
`summary`, or contain a JSON code block with one or more such entries. Any
`*.json` files found in the same folder are treated as specification objects and
used to build the prompt.

```markdown
---
expected_filename: example.png
summary: An example scene
---
```

```json
[{"expected_filename": "example.png", "summary": "An example scene"}]
```

```bash
poetry run mdgpt generate-images-from-docs docs --model gpt-image-1 --size 1024x1024
```

The same functionality is available via the shorter `docs` alias:

```bash
poetry run mdgpt docs docs --model gpt-image-1 --size 1024x1024
```


## .env Setup

The application requires an OpenAI API key. Create a `.env` file in the project
root containing:

```bash
OPENAI_API_KEY=<your-api-key>
```

Alternatively, set `OPENAI_API_KEY` in your shell environment before running
the commands above.
