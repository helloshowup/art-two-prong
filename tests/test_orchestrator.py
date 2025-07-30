from pathlib import Path

import importlib


def import_orchestrator():
    if "md_batch_gpt.orchestrator" in importlib.sys.modules:
        del importlib.sys.modules["md_batch_gpt.orchestrator"]
    return importlib.import_module("md_batch_gpt.orchestrator")


def test_process_folder(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    calls = []

    def fake_send_prompt(
        prompt: str,
        content: str,
        model: str,
        max_tokens: int | None = None,
    ) -> str:
        calls.append((prompt, content, model, max_tokens))
        return f"{content}[{prompt}]"

    monkeypatch.setattr(orch, "send_prompt", fake_send_prompt)

    (tmp_path / "a.md").write_text("A")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("B")
    (tmp_path / ".hidden.md").write_text("hidden")

    p1 = tmp_path / "p1.txt"
    p1.write_text("p1")
    p2 = tmp_path / "p2.txt"
    p2.write_text("p2")

    orch.process_folder(tmp_path, [p1, p2], model="m")

    assert (tmp_path / "a.md").read_text() == "A[p1][p2]"
    assert (sub / "b.md").read_text() == "B[p1][p2]"
    assert (tmp_path / ".hidden.md").read_text() == "hidden"
    assert len(calls) == 4
    assert all(call[2:] == ("m", None) for call in calls)


def test_process_folder_dry_run(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    send_calls = []
    write_calls = []

    monkeypatch.setattr(orch, "send_prompt", lambda *a, **k: send_calls.append(True))
    monkeypatch.setattr(orch, "write_atomic", lambda *a, **k: write_calls.append(True))

    (tmp_path / "a.md").write_text("A")
    (tmp_path / "b.md").write_text("B")

    p1 = tmp_path / "p1.txt"
    p1.write_text("p1")

    orch.process_folder(tmp_path, [p1], model="m", dry_run=True)

    assert send_calls == []
    assert write_calls == []
    out = capsys.readouterr().out
    assert "a.md" in out
    assert "b.md" in out
    assert "Prompt count: 1" in out


def test_process_folder_verbose(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    def fake_send_prompt(
        prompt: str,
        content: str,
        model: str,
        max_tokens: int | None = None,
    ) -> str:
        return f"{content}[{prompt}]"

    monkeypatch.setattr(orch, "send_prompt", fake_send_prompt)

    md = tmp_path / "a.md"
    md.write_text("A")

    p1 = tmp_path / "p1.txt"
    p1.write_text("p1")
    p2 = tmp_path / "p2.txt"
    p2.write_text("p2")

    orch.process_folder(tmp_path, [p1, p2], model="m", verbose=True)

    out_lines = capsys.readouterr().out.splitlines()
    assert "a.md: pass 1/2" in out_lines[0]
    assert "a.md: pass 2/2" in out_lines[1]


def test_process_folder_max_tokens(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    captured = {}

    def fake_send_prompt(
        prompt: str,
        content: str,
        model: str,
        max_tokens: int | None = None,
    ) -> str:
        captured["max_tokens"] = max_tokens
        return content

    monkeypatch.setattr(orch, "send_prompt", fake_send_prompt)

    (tmp_path / "a.md").write_text("A")
    p = tmp_path / "p.txt"
    p.write_text("p")

    orch.process_folder(tmp_path, [p], model="m", max_tokens=99)

    assert captured["max_tokens"] == 99


def test_process_folder_invalid_bytes(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    def fake_send_prompt(
        prompt: str, content: str, model: str, max_tokens: int | None = None
    ) -> str:
        return f"{content}[{prompt}]"

    monkeypatch.setattr(orch, "send_prompt", fake_send_prompt)

    md = tmp_path / "a.md"
    md.write_bytes(b"A\xffB")

    p = tmp_path / "p.txt"
    p.write_bytes(b"p\xfe")

    orch.process_folder(tmp_path, [p], model="m")

    # Replacement character should appear for invalid bytes
    assert md.read_text(encoding="utf-8") == "A\ufffdB[p\ufffd]"


def test_process_folder_no_markdown(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    send_calls = []
    write_calls = []

    monkeypatch.setattr(orch, "send_prompt", lambda *a, **k: send_calls.append(True))
    monkeypatch.setattr(orch, "write_atomic", lambda *a, **k: write_calls.append(True))

    (tmp_path / "a.txt").write_text("A")
    p1 = tmp_path / "p1.txt"
    p1.write_text("p1")

    orch.process_folder(tmp_path, [p1], model="m")

    assert send_calls == []
    assert write_calls == []
    out = capsys.readouterr().out
    assert f"No markdown files found under {tmp_path}" in out


def test_process_folder_regex_json(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    orch = import_orchestrator()

    def fake_send_prompt(prompt: str, content: str, model: str, max_tokens: int | None = None) -> str:
        return f"{content}[{prompt}]"

    monkeypatch.setattr(orch, "send_prompt", fake_send_prompt)

    md = tmp_path / "a.md"
    md.write_text("foo")

    prompt = tmp_path / "p.txt"
    prompt.write_text("p")

    regex = tmp_path / "r.json"
    regex.write_text('{"foo": "bar"}')

    orch.process_folder(tmp_path, [prompt], model="m", regex_json=regex)

    assert md.read_text(encoding="utf-8") == "bar[p]"
