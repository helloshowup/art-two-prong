from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import yaml
import json
import re

JSON_BLOCK_RE = re.compile(r"```(?:json)?\n(.*?)```", re.DOTALL)

from .file_io import iter_markdown_files


def parse_markdown_image_entries(folder: Path) -> List[Dict[str, str]]:
    """Return a list of image generation entries from Markdown files in *folder*.

    Each Markdown file may either begin with YAML front matter containing
    ``expected_filename`` and ``summary`` keys or contain a JSON block with one
    or more such entries. Additional fields are preserved. The function uses
    :func:`iter_markdown_files` to locate ``*.md`` files under *folder*. JSON
    blocks may appear anywhere in the document.
    """
    entries: List[Dict[str, str]] = []
    for md_path in sorted(iter_markdown_files(folder)):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        stripped = text.lstrip()
        if stripped.startswith("---"):
            parts = stripped.split("---", 2)
            if len(parts) < 3:
                raise ValueError(f"{md_path} missing closing YAML delimiter")
            fm_text = parts[1]
            data = yaml.safe_load(fm_text) or {}
            if (
                isinstance(data, dict)
                and data.get("expected_filename")
                and data.get("summary")
            ):
                entries.append(data)
                continue
            if isinstance(data, dict):
                # Detected YAML front matter but required keys missing
                raise ValueError(
                    f"{md_path} front matter missing expected_filename or summary"
                )
            # Not valid YAML front matter; fall through treating remainder as text
            stripped = parts[2].lstrip()

        json_text = stripped
        match = JSON_BLOCK_RE.search(json_text)
        if match:
            json_text = match.group(1)
        elif json_text.startswith("```"):
            first_nl = json_text.find("\n")
            if first_nl == -1:
                raise ValueError(f"{md_path} malformed JSON code block")
            json_text = json_text[first_nl + 1 :]
            end = json_text.rfind("```")
            if end == -1:
                raise ValueError(f"{md_path} missing closing code block")
            json_text = json_text[:end]
        else:
            json_text = json_text.strip()
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{md_path} contains invalid JSON") from exc

        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError(f"{md_path} JSON must be object or list")

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"{md_path} JSON entry {idx} is not a mapping")
            filename = item.get("expected_filename")
            summary = item.get("summary")
            if not filename or not summary:
                raise ValueError(
                    f"{md_path} JSON entry {idx} missing expected_filename or summary"
                )
            entries.append(item)
    return entries
