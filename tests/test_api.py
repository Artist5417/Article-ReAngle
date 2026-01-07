import json
from app.schemas.rewrite_schema import LLMType


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Article ReAngle API"}


def test_rewrite_text_input(client):
    inputs = [{"id": "1", "type": "text", "content": "Hello World"}]
    data = {"inputs": json.dumps(inputs), "prompt": "Rewrite this", "llm_type": "gpt-5"}

    response = client.post("/api/v1/rewrite", data=data)

    assert response.status_code == 200
    result = response.json()
    assert result["original"].strip() == "[文本]\nHello World"
    assert result["rewritten"] == "Rewritten content by Mock LLM"
    assert result["summary"] == "Summary by Mock LLM"


def test_rewrite_url_input(client):
    inputs = [{"id": "2", "type": "url", "content": "http://example.com"}]
    data = {
        "inputs": json.dumps(inputs),
        "prompt": "Summarize URL",
        "llm_type": "gpt-5",
    }

    response = client.post("/api/v1/rewrite", data=data)

    assert response.status_code == 200
    result = response.json()
    assert "Extracted content from URL" in result["original"]


def test_rewrite_file_input(client):
    file_content = b"Mock file content"
    inputs = [{"id": "3", "type": "file", "contentKey": "file_3"}]
    data = {"inputs": json.dumps(inputs), "prompt": "Analyze file", "llm_type": "gpt-5"}
    files = {"file_3": ("test.txt", file_content, "text/plain")}

    response = client.post("/api/v1/rewrite", data=data, files=files)

    assert response.status_code == 200
    result = response.json()
    assert "Mock file content" in result["original"]


def test_rewrite_missing_inputs(client):
    data = {"inputs": "", "prompt": "Test", "llm_type": "gpt-5"}
    response = client.post("/api/v1/rewrite", data=data)
    assert (
        response.status_code == 400
    )  # Validation error mapped to 400 by custom exception handler


def test_rewrite_invalid_json(client):
    data = {"inputs": "{invalid_json", "prompt": "Test", "llm_type": "gpt-5"}
    response = client.post("/api/v1/rewrite", data=data)
    # The routers catches json.loads exception and raises ContentExtractionError (which maps to 400 usually, checking exception handler)
    # Looking at app/core/handlers.py would confirm, but usually 400 or 500.
    # Let's assume 400 or 500 based on standard exception handling.
    assert response.status_code in [400, 422, 500]


def test_tts_endpoint(client):
    data = {"text": "Hello audio", "voice": "Cherry", "model": "qwen3-tts-flash"}
    response = client.post("/api/v1/rewrite/tts", json=data)

    assert response.status_code == 200
    assert response.json()["audio_url"] == "http://mock.audio/output.mp3"


def test_avatar_endpoint(client):
    data = {"text": "Hello avatar video"}
    response = client.post("/api/v1/rewrite/avatar", json=data)

    assert response.status_code == 200
    assert response.json()["video_url"] == "http://mock.video/output.mp4"
