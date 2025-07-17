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
    result = runner.invoke(cli.app, [str(docs), "--verbose"])

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
            str(tmp_path),
            "--prompts",
            "tests/data/p1.txt",
            "--regex-json",
            str(regex_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["regex_json"] == regex_path
