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

    class DummyResp:
        def __init__(self, data):
            self.data = data

    def dummy_generate(**kwargs):
        captured_kwargs.update(kwargs)
        return DummyResp([type("Node", (), {"b64_json": b64})])

    monkeypatch.setattr(oc._client.images, "generate", dummy_generate)

    result = oc.generate_image("a prompt", model="m")

    assert result == b"imgdata"
    assert captured_kwargs["prompt"] == "a prompt"
    assert captured_kwargs["model"] == "m"
    assert "response_format" not in captured_kwargs
