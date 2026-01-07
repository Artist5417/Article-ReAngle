import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.schemas.rewrite_schema import LLMResponse


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_external_services():
    """
    Mock all external service calls to LLMs and Extractors.
    """
    with patch(
        "app.services.llms.rewriting_client.get_rewriting_result",
        new_callable=AsyncMock,
    ) as mock_rewrite, patch(
        "app.services.llms.tts_client.get_tts_result", new_callable=AsyncMock
    ) as mock_tts, patch(
        "app.services.llms.avatar_client.get_avatar_result", new_callable=AsyncMock
    ) as mock_avatar, patch(
        "app.routers.rewrite.extract_text_from_url", new_callable=AsyncMock
    ) as mock_url, patch(
        "app.routers.rewrite.extract_text_from_docx", new_callable=AsyncMock
    ) as mock_docx, patch(
        "app.routers.rewrite.extract_text_from_pdf", new_callable=AsyncMock
    ) as mock_pdf, patch(
        "app.routers.rewrite.extract_text_from_image", new_callable=AsyncMock
    ) as mock_image:

        # Setup default success returns
        mock_rewrite.return_value = LLMResponse(
            rewritten="Rewritten content by Mock LLM", summary="Summary by Mock LLM"
        )

        mock_tts.return_value = "http://mock.audio/output.mp3"
        mock_avatar.return_value = "http://mock.video/output.mp4"

        mock_url.return_value = "Extracted content from URL"
        mock_docx.return_value = "Extracted content from DOCX"
        mock_pdf.return_value = "Extracted content from PDF"
        mock_image.return_value = "Extracted content from Image"

        yield {
            "rewrite": mock_rewrite,
            "tts": mock_tts,
            "avatar": mock_avatar,
            "url": mock_url,
            "docx": mock_docx,
            "pdf": mock_pdf,
            "image": mock_image,
        }
