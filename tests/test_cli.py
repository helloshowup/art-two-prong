import importlib
from pathlib import Path

from typer.testing import CliRunner


def import_cli():
    if "md_batch_gpt.cli" in importlib.sys.modules:
        del importlib.sys.modules["md_batch_gpt.cli"]
    return importlib.import_module("md_batch_gpt.cli")


def test_run_dry_run(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()
    monkeypatch.setattr("md_batch_gpt.orchestrator.send_prompt", lambda *a, **k: "")

    (tmp_path / "a.md").write_text("A")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("B")

    runner = CliRunner()
    result = runner.invoke(
        cli.app,
        [
            "run",
            str(tmp_path),
            "--dry-run",
            "--prompts",
            "tests/data/p1.txt",
            "--prompts",
            "tests/data/p2.txt",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "a.md" in result.stdout
    assert "b.md" in result.stdout
    assert "Prompt count: 2" in result.stdout


def test_run_max_tokens(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    captured = {}

    def fake_process_folder(
        folder: Path,
        prompt_paths: list[Path],
        model: str,
        max_tokens: int | None = None,
        regex_json: Path | None = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        captured["max_tokens"] = max_tokens

    monkeypatch.setattr(cli, "process_folder", fake_process_folder)

    (tmp_path / "a.md").write_text("A")

    runner = CliRunner()
    result = runner.invoke(
        cli.app,
        [
            "run",
            str(tmp_path),
            "--prompts",
            "tests/data/p1.txt",
            "--max-tokens",
            "123",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["max_tokens"] == 123


def test_run_auto_prompt_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()
    monkeypatch.setattr("md_batch_gpt.orchestrator.send_prompt", lambda *a, **k: "")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("A")

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    for i in range(1, 4):
        (prompts_dir / f"{i:02d}.txt").write_text(f"p{i}")

    dummy_cli_path = tmp_path / "pkg" / "cli.py"
    dummy_cli_path.parent.mkdir()
    dummy_cli_path.write_text("")
    monkeypatch.setattr(cli, "__file__", str(dummy_cli_path))

    runner = CliRunner()
    result = runner.invoke(cli.app, ["run", str(docs), "--verbose"])

    assert result.exit_code == 0, result.stdout
    assert "pass 3/3" in result.stdout


def test_run_regex_json(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    captured = {}

    def fake_process_folder(
        folder: Path,
        prompt_paths: list[Path],
        model: str,
        max_tokens: int | None = None,
        regex_json: Path | None = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        captured["regex_json"] = regex_json

    monkeypatch.setattr(cli, "process_folder", fake_process_folder)

    (tmp_path / "a.md").write_text("A")
    regex_path = tmp_path / "regex.json"
    regex_path.write_text("{}")

    runner = CliRunner()
    result = runner.invoke(
        cli.app,
        [
            "run",
            str(tmp_path),
            "--prompts",
            "tests/data/p1.txt",
            "--regex-json",
            str(regex_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["regex_json"] == regex_path


def test_generate_image_command(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    generated = {}

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        generated["prompt"] = prompt
        generated["model"] = model
        generated["size"] = size
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        prompt_file = Path("p.txt")
        prompt_file.write_text("out.png\nA cat in space")
        result = runner.invoke(
            cli.app,
            ["generate-image", str(prompt_file), "--model", "m1", "--size", "256x256"],
        )

        assert result.exit_code == 0, result.stdout
        assert Path("out.png").read_bytes() == b"imgbytes"
        assert generated == {
            "prompt": "A cat in space",
            "model": "m1",
            "size": "256x256",
        }


def test_generate_images_command(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    calls = []

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        calls.append((prompt, model, size))
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    j1 = tmp_path / "f1.json"
    j1.write_text('[{"expected_filename": "a.png", "summary": "A"}]')
    j2 = tmp_path / "f2.json"
    j2.write_text(
        '[{"expected_filename": "b.png", "summary": "B"}, {"expected_filename": "c.png", "summary": "C"}]'
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli.app,
            ["generate-images", str(j1), str(j2), "--model", "m", "--size", "256x256"],
        )

        assert result.exit_code == 0, result.stdout
        assert Path("a.png").read_bytes() == b"imgbytes"
        assert Path("b.png").read_bytes() == b"imgbytes"
        assert Path("c.png").read_bytes() == b"imgbytes"

    prompts = [call[0] for call in calls]
    assert prompts == ["A", "B", "C"]
    assert all(call[1:] == ("m", "256x256") for call in calls)


def test_generate_images_extra_fields(monkeypatch, tmp_path: Path):
    """Extra fields in the JSON entries should be ignored."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    captured: list[tuple[str, str]] = []

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        captured.append((prompt, model))
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    data = (
        '[{"expected_filename": "img.png", "summary": "An image", "alt_text": "extra"}]'
    )
    json_file = tmp_path / "entry.json"
    json_file.write_text(data)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli.app, ["generate-images", str(json_file), "--model", "gpt-image-1"]
        )

        assert result.exit_code == 0, result.stdout
        assert Path("img.png").read_bytes() == b"imgbytes"

    assert captured == [("An image", "gpt-image-1")]


def test_generate_images_from_docs(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    calls: list[tuple[str, str, str]] = []

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        calls.append((prompt, model, size))
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "one.md").write_text(
        """---
expected_filename: one.png
summary: first image
---
content
"""
    )
    (docs / "two.md").write_text(
        """---
expected_filename: two.png
summary: second image
---
text
"""
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli.app,
            [
                "generate-images-from-docs",
                str(docs),
                "--model",
                "m",
                "--size",
                "256x256",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert Path("one.png").read_bytes() == b"imgbytes"
        assert Path("two.png").read_bytes() == b"imgbytes"

    prompts = [c[0] for c in calls]
    assert prompts == ["first image", "second image"]
    assert all(c[1:] == ("m", "256x256") for c in calls)


def test_generate_images_from_docs_json_block(monkeypatch, tmp_path: Path):
    """JSON blocks at the beginning of Markdown files should be processed."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    calls: list[tuple[str, str, str]] = []

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        calls.append((prompt, model, size))
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "json.md").write_text(
        """```json
[{"expected_filename": "j.png", "summary": "json entry"}]
```"""
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli.app,
            [
                "generate-images-from-docs",
                str(docs),
                "--model",
                "m",
                "--size",
                "256x256",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert Path("j.png").read_bytes() == b"imgbytes"

    assert calls == [("json entry", "m", "256x256")]


def test_generate_images_from_docs_file_start(monkeypatch, tmp_path: Path):
    """Files with FILE START markers should be parsed using the JSON block."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    cli = import_cli()

    calls: list[tuple[str, str, str]] = []

    def fake_generate_image(
        prompt: str, model: str = "dall-e-3", size: str = "1024x1024"
    ):
        calls.append((prompt, model, size))
        return b"imgbytes"

    monkeypatch.setattr(cli, "generate_image", fake_generate_image)

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "entry.md").write_text(
        """--- FILE START ---
```json
[{"expected_filename": "fs.png", "summary": "file start"}]
```
--- FILE END ---"""
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli.app,
            [
                "generate-images-from-docs",
                str(docs),
                "--model",
                "m",
                "--size",
                "256x256",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert Path("fs.png").read_bytes() == b"imgbytes"

    assert calls == [("file start", "m", "256x256")]

