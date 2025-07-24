from pathlib import Path
from md_batch_gpt.markdown_parser import parse_markdown_image_entries


def test_parse_json_block_middle(tmp_path: Path):
    md = tmp_path / "doc.md"
    md.write_text(
        """Intro text

```json
[{\"expected_filename\": \"img.png\", \"summary\": \"desc\", \"alt_text\": \"alt\"}]
```
Outro"""
    )
    entries = parse_markdown_image_entries(tmp_path)
    assert entries == [{"expected_filename": "img.png", "summary": "desc", "alt_text": "alt"}]
