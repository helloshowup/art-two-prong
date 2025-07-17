import importlib
import base64


def import_oc():
    if "md_batch_gpt.openai_client" in importlib.sys.modules:
        del importlib.sys.modules["md_batch_gpt.openai_client"]
    return importlib.import_module("md_batch_gpt.openai_client")


def test_generate_image(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    oc = import_oc()

    b64 = base64.b64encode(b"imgdata").decode()

    captured_kwargs = {}

    def dummy_create(**kwargs):
        captured_kwargs.update(kwargs)
        return {"data": [{"b64_json": b64}]}

    monkeypatch.setattr(oc.openai.Image, "create", dummy_create)

    result = oc.generate_image("a prompt", model="m")

    assert result == b"imgdata"
    assert captured_kwargs["prompt"] == "a prompt"
    assert captured_kwargs["model"] == "m"
    assert "response_format" not in captured_kwargs
