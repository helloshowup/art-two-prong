from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import yaml

from .file_io import iter_markdown_files


def parse_markdown_image_entries(folder: Path) -> List[Dict[str, str]]:
    """Return a list of image generation entries from Markdown files in *folder*.

    Each Markdown file must start with YAML front-matter containing
    ``expected_filename`` and ``summary`` keys. Any additional fields are
    ignored. The function uses :func:`iter_markdown_files` to locate ``*.md``
    files under *folder*.
    """
    entries: List[Dict[str, str]] = []
    for md_path in iter_markdown_files(folder):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            raise ValueError(f"{md_path} missing YAML front matter")
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"{md_path} missing closing YAML delimiter")
        fm_text = parts[1]
        data = yaml.safe_load(fm_text) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{md_path} front matter is not a mapping")
        filename = data.get("expected_filename")
        summary = data.get("summary")
        if not filename or not summary:
            raise ValueError(
                f"{md_path} front matter missing expected_filename or summary"
            )
        entries.append({"expected_filename": filename, "summary": summary})
    return entries
