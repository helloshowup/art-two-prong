from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

from .openai_client import generate_image
from .markdown_parser import parse_markdown_image_entries

import typer

from .orchestrator import process_folder


def validate_prompts(_: typer.Context, value: Tuple[Path, ...]) -> List[Path]:
    """Return *value* if all paths exist, otherwise raise BadParameter."""
    for p in value:
        if not p.exists():
            raise typer.BadParameter(f"File not found: {p}")
    return list(value)


app = typer.Typer()


@app.command()
def run(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    prompts: List[Path] = typer.Option(
        [],
        "--prompts",
        help="Space-separated list of prompt files",
        callback=validate_prompts,
    ),
    model: str = typer.Option("o3", "--model", help="OpenAI model to use"),
    max_tokens: int | None = typer.Option(
        None, "--max-tokens", help="Max tokens for completion"
    ),
    regex_json: Path = typer.Option(
        None,
        "--regex-json",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to JSON file of regex patterns",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="List files to be processed without sending prompts",
    ),
) -> None:
    """Run the batch processor on *folder* using *prompts*."""
    prompt_list = list(prompts)
    if len(prompt_list) == 0:
        default_dir = Path(__file__).parent.parent / "prompts"
        prompt_paths = sorted(default_dir.glob("*.txt"))
        if not prompt_paths:
            raise typer.BadParameter(
                f"No prompt files found in {default_dir}. "
                "Pass --prompts explicitly or add *.txt files."
            )
        prompt_list = list(prompt_paths)

    if verbose:
        typer.echo(f"Folder: {folder}")
        typer.echo(f"Prompts: {', '.join(str(p) for p in prompt_list)}")
        typer.echo(f"Model: {model} Max tokens: {max_tokens}")
        if regex_json:
            typer.echo(f"Regex JSON: {regex_json}")
    process_folder(
        folder,
        prompt_list,
        model=model,
        max_tokens=max_tokens,
        regex_json=regex_json,
        dry_run=dry_run,
        verbose=verbose,
    )
    if verbose:
        typer.echo("Done")


@app.command("generate-image")
def generate_image_cmd(
    prompt_file: Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    model: str = typer.Option(
        "dall-e-3", "--model", help="OpenAI model for image generation"
    ),
    size: str = typer.Option("1024x1024", "--size", help="Image size, e.g. 1024x1024"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate an image using a filename and prompt from *prompt_file*."""
    text = prompt_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        raise typer.BadParameter("Prompt file is empty")
    filename = lines[0].strip()
    prompt = "\n".join(lines[1:]).strip()
    if not filename:
        raise typer.BadParameter("Missing filename on first line")
    if not prompt:
        raise typer.BadParameter("Missing prompt text")
    if verbose:
        typer.echo(f"Generating {filename} with model {model}")
    image_bytes = generate_image(prompt, model=model, size=size)
    Path(filename).write_bytes(image_bytes)
    if verbose:
        typer.echo(f"Wrote {filename}")


@app.command("generate-images")
def generate_images_cmd(
    json_files: List[Path] = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    model: str = typer.Option(
        "dall-e-3", "--model", help="OpenAI model for image generation"
    ),
    size: str = typer.Option("1024x1024", "--size", help="Image size, e.g. 1024x1024"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate images for each entry in one or more JSON files."""
    for json_file in json_files:
        if verbose:
            typer.echo(f"Processing {json_file}")
        try:
            entries = json.loads(
                json_file.read_text(encoding="utf-8", errors="replace")
            )
        except json.JSONDecodeError as exc:  # pragma: no cover - error path
            raise typer.BadParameter(f"Invalid JSON in {json_file}: {exc}") from exc
        if not isinstance(entries, list):
            raise typer.BadParameter(f"{json_file} does not contain a list")
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise typer.BadParameter(f"Entry {idx} in {json_file} is not an object")
            filename = entry.get("expected_filename")
            prompt = entry.get("summary")
            if not filename or not prompt:
                raise typer.BadParameter(
                    f"Entry {idx} in {json_file} missing expected_filename or summary"
                )
            if verbose:
                typer.echo(f"  Generating {filename}")
            image_bytes = generate_image(prompt, model=model, size=size)
            Path(filename).write_bytes(image_bytes)
            if verbose:
                typer.echo(f"  Wrote {filename}")


@app.command("generate-images-from-docs")
def generate_images_from_docs_cmd(
    docs_folder: Path = typer.Argument(
        ..., exists=True, file_okay=False, dir_okay=True
    ),
    model: str = typer.Option(
        "dall-e-3", "--model", help="OpenAI model for image generation"
    ),
    size: str = typer.Option("1024x1024", "--size", help="Image size, e.g. 1024x1024"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate images based on Markdown/JSON files under *docs_folder*."""
    entries = parse_markdown_image_entries(docs_folder)

    for json_path in docs_folder.glob("*.json"):
        try:
            raw = json.loads(
                json_path.read_text(encoding="utf-8", errors="replace")
            )
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Invalid JSON in {json_path}: {exc}") from exc

        specs = raw if isinstance(raw, list) else [raw]
        for spec in specs:
            if not isinstance(spec, dict):
                raise typer.BadParameter(f"{json_path} entry is not an object")
            if not spec.get("expected_filename") or not spec.get("summary"):
                raise typer.BadParameter(
                    f"{json_path} missing expected_filename or summary"
                )
            entries.append(spec)

    for entry in entries:
        filename = entry["expected_filename"]
        if entry.get("alt_text"):
            prompt = (
                f"Create a file named `{entry['expected_filename']}` with alt text \"{entry['alt_text']}\".\n"
                f"Description:\n{entry['summary']}"
            )
            if entry.get("lesson_number") or entry.get("lesson_title"):
                prompt += (
                    f"\n(Lesson {entry.get('lesson_number')}: {entry.get('lesson_title')})"
                )
        else:
            prompt = entry["summary"]
        if verbose:
            typer.echo(f"Generating {filename}")
        image_bytes = generate_image(prompt, model=model, size=size)
        Path(filename).write_bytes(image_bytes)
        if verbose:
            typer.echo(f"Wrote {filename}")


if __name__ == "__main__":  # pragma: no cover
    app()
