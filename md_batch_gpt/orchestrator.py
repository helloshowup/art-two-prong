from __future__ import annotations

from pathlib import Path
from typing import List

from .file_io import iter_markdown_files, write_atomic
from .openai_client import send_prompt
import typer


def process_folder(
    folder: Path,
    prompt_paths: List[Path],
    model: str,
    max_tokens: int | None = None,
    regex_json: Path | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Process Markdown files in *folder* using prompts from *prompt_paths*.

    When *dry_run* is True, print the files that would be processed and the
    number of prompts, but make no changes.
    """
    prompts = [
        Path(p).read_text(encoding="utf-8", errors="replace") for p in prompt_paths
    ]
    files = list(iter_markdown_files(folder))
    if dry_run:
        for f in files:
            print(f)
        print(f"Prompt count: {len(prompts)}")
        return

    for md_file in files:
        text = md_file.read_text(encoding="utf-8", errors="replace")
        for idx, prompt in enumerate(prompts):
            if verbose:
                typer.echo(f"{md_file}: pass {idx + 1}/{len(prompts)}")
            text = send_prompt(prompt, text, model, max_tokens)
            write_atomic(md_file, text)
