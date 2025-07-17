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

Generate images from JSON description files:
```bash
poetry run mdgpt generate-images images1.json images2.json --model dall-e-3 --size 1024x1024
```

## .env Setup

The application requires an OpenAI API key. Create a `.env` file in the project
root containing:

```bash
OPENAI_API_KEY=<your-api-key>
```

Alternatively, set `OPENAI_API_KEY` in your shell environment before running
the commands above.
