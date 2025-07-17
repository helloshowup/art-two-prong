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

    class DummyImages:
        def __init__(self):
            self.kwargs = None

        def generate(self, **kwargs):
            self.kwargs = kwargs
            return type("Resp", (), {"data": [{"b64_json": b64}]})()

    dummy_client = type("Client", (), {"images": DummyImages()})()

    monkeypatch.setattr(oc, "_client", dummy_client)

    result = oc.generate_image("a prompt", model="m")

    assert result == b"imgdata"
    assert dummy_client.images.kwargs["prompt"] == "a prompt"
    assert dummy_client.images.kwargs["model"] == "m"
    assert dummy_client.images.kwargs["response_format"] == "b64_json"
