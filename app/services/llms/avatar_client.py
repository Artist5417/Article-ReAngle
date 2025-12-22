import os
import asyncio
import httpx
from loguru import logger
from app.core.exceptions import LLMProviderError


class AvatarClient:
    def __init__(self):
        self.api_key = os.getenv("HEYGEN_API_KEY")
        self.base_url = "https://api.heygen.com"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def get_avatar_result(self, text: str) -> str:
        """
        Generates an avatar video from text using HeyGen API V2.

        Args:
            text: The text for the avatar to speak.

        Returns:
            str: The URL of the generated video.

        Raises:
            LLMProviderError: If the generation fails or times out.
        """
        if not self.api_key:
            raise LLMProviderError("Missing HEYGEN_API_KEY environment variable")

        video_id = await self._generate_video(text)
        return await self._poll_video_status(video_id)

    async def _generate_video(self, text: str) -> str:
        url = f"{self.base_url}/v2/video/generate"
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": "Daisy-hq",
                        "scale": 1.0,
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": "2d5b0e6ccf79403280d0926203731d0e",
                    },
                    "background": {"type": "color", "value": "#FAFAFA"},
                }
            ],
            "dimension": {"width": 1280, "height": 720},
            "test": True,  # Enable test mode to save credits
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=self.headers, json=payload, timeout=30.0
                )

            if response.status_code != 200:
                logger.error(f"HeyGen generation failed: {response.text}")
                raise LLMProviderError(f"HeyGen API generation error: {response.text}")

            data = response.json()
            if "data" not in data or "video_id" not in data["data"]:
                logger.error(f"HeyGen invalid response: {data}")
                raise LLMProviderError("Invalid response from HeyGen API")

            video_id = data["data"]["video_id"]
            logger.info(f"HeyGen video generation started. Video ID: {video_id}")
            return video_id

        except httpx.RequestError as e:
            logger.error(f"HeyGen network error: {e}")
            raise LLMProviderError(f"Network error interacting with HeyGen: {str(e)}")

    async def _poll_video_status(self, video_id: str) -> str:
        url = f"{self.base_url}/v1/video_status.get"
        params = {"video_id": video_id}

        max_retries = 30  # 30 * 4s = 120s timeout
        for _ in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url, headers=self.headers, params=params, timeout=10.0
                    )

                if response.status_code != 200:
                    logger.warning(f"HeyGen status check failed: {response.text}")
                    continue

                data = response.json()
                status = data.get("data", {}).get("status")

                if status == "completed":
                    video_url = data["data"].get("video_url")
                    logger.info(f"HeyGen video completed: {video_url}")
                    return video_url
                elif status == "failed":
                    error = data.get("data", {}).get("error")
                    logger.error(f"HeyGen video processing failed: {error}")
                    raise LLMProviderError(f"Video processing failed: {error}")

                logger.debug(f"HeyGen video status: {status}")
                await asyncio.sleep(4)

            except httpx.RequestError as e:
                logger.warning(f"HeyGen polling network error: {e}")

        raise LLMProviderError("Video generation timed out")


# Create a singleton instance
_client = AvatarClient()


async def get_avatar_result(text: str) -> str:
    """
    Module-level entry point for avatar generation, matching the pattern of tts_client.
    """
    return await _client.get_avatar_result(text)
