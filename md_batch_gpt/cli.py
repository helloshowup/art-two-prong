from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

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


if __name__ == "__main__":  # pragma: no cover
    app()
