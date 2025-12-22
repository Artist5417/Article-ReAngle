"""
根据不同输入源提取文本
"""

import httpx
import docx
import pypdf
import io
from bs4 import BeautifulSoup
from readability import Document
from fastapi import UploadFile
from loguru import logger

from app.core.exceptions import ContentExtractionError, InvalidInputError

# 轻量 OCR（中英混排效果较好）
try:
    from rapidocr_onnxruntime import RapidOCR  # type: ignore
    _rapid_ocr = RapidOCR()  # 初始化一次复用
except Exception:
    _rapid_ocr = None
    logger.warning("RapidOCR is not available. Image OCR will be disabled.")
from PIL import Image  
import numpy as np
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
import re
import asyncio

# 可选：yt-dlp 元信息探测（不下载媒体）
try:
    from yt_dlp import YoutubeDL  # type: ignore
    _yt_dlp_available = True
except Exception:
    _yt_dlp_available = False
    logger.warning("yt-dlp is not available. YouTube metadata probing disabled.")

# 可选：YouTube 字幕提取（v1：仅字幕，不做 ASR）
try:
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    from youtube_transcript_api._errors import (  # type: ignore
        NoTranscriptFound,
        TranscriptsDisabled,
        CouldNotRetrieveTranscript,
        VideoUnavailable,
    )
    _yt_transcript_available = True
except Exception:
    _yt_transcript_available = False
    logger.warning("youtube-transcript-api is not available. Transcript extraction disabled.")

_YOUTUBE_ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

def validate_and_get_video_id(url: str) -> str:
    """
    第一步：本地校验且提取 videoId（不发网络）。
    仅接受 http/https，且 host 在白名单，且形态为单视频（watch?v= / youtu.be / shorts / embed）。
    如为 playlist/channel 等非单视频形态，或 videoId 非法，抛 InvalidInputError。
    """
    try:
        # 规范化协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            raise InvalidInputError("Only http/https allowed for YouTube URL")
        # SSRF 基础防护：只允许常规端口
        netloc = (parsed.netloc or "")
        host_port = netloc.split("@")[-1]  # 去掉 userinfo
        host = host_port.split(":")[0].lower()
        if host not in _YOUTUBE_ALLOWED_HOSTS:
            raise InvalidInputError("Unsupported YouTube host")
        path = parsed.path or ""
        query = parse_qs(parsed.query or "")

        # 明确拒绝 playlist 形态（URL 层面）
        lower_path = path.lower()
        if "playlist" in lower_path:
            raise InvalidInputError("Playlist URL is not supported")
        if lower_path.startswith("/channel/") or lower_path.startswith("/c/") or "/@"+"" in lower_path:
            # 简易处理频道/自定义用户名路径；如需更严格可细化
            raise InvalidInputError("Channel or user URL is not supported")

        video_id = ""
        if host == "youtu.be":
            video_id = path.strip("/").split("/")[0]
        else:
            if lower_path.startswith("/watch"):
                video_id = (query.get("v") or [""])[0]
                # 只有 list 而没有 v → 认为是 playlist
                if not video_id and "list" in query:
                    raise InvalidInputError("Playlist URL is not supported")
            elif lower_path.startswith("/shorts/"):
                parts = path.split("/")
                video_id = parts[2] if len(parts) >= 3 else ""
            elif lower_path.startswith("/embed/"):
                parts = path.split("/")
                video_id = parts[2] if len(parts) >= 3 else ""

        if not _VIDEO_ID_RE.match(video_id or ""):
            raise InvalidInputError("Invalid or missing YouTube videoId")
        return video_id
    except InvalidInputError:
        raise
    except Exception as e:
        logger.debug(f"validate_and_get_video_id unexpected error: {e}")
        raise InvalidInputError("Invalid YouTube URL")

def probe_youtube_basic_info(url: str) -> Dict[str, Any]:
    """
    第二步：轻量网络探测（不下载媒体）。
    使用 yt-dlp 提取基础元信息，判断是否为单视频、是否直播、是否需会员/私有等。
    返回: { videoId, title, duration, is_live, availability, age_limit }
    若判定不可解析，抛 ContentExtractionError（带可读原因）。
    """
    if not _yt_dlp_available:
        raise ContentExtractionError(
            "yt-dlp not installed. Please `pip install yt-dlp` to enable YouTube probing."
        )
    # 保证 URL 可用（如用户输入裸域名）
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": "discard_in_playlist",
        "socket_timeout": 10,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        # playlist 识别
        if info.get("_type") == "playlist" or "entries" in info:
            raise ContentExtractionError("Playlist URL is not supported")
        video_id = info.get("id") or ""
        title = info.get("title") or ""
        duration = info.get("duration")
        is_live = bool(info.get("is_live") or (info.get("live_status") in {"is_live", "is_upcoming"}))
        availability = (info.get("availability") or "").lower()
        age_limit = int(info.get("age_limit") or 0)
        # 基本可播性判断
        if is_live:
            raise ContentExtractionError("Live stream is not supported")
        if not isinstance(duration, (int, float)) or int(duration) <= 0:
            raise ContentExtractionError("Video is not playable or duration is unknown")
        if availability and availability not in {"public", "unlisted"}:
            # 常见：private, needs_auth, premium_only, subscriber_only 等
            raise ContentExtractionError("Video requires membership or is restricted")
        # v1 可选直接拒绝年龄限制
        if age_limit >= 18:
            raise ContentExtractionError("Age restricted video is not supported in v1")
        return {
            "videoId": video_id,
            "title": title,
            "duration": int(duration),
            "is_live": is_live,
            "availability": availability,
            "age_limit": age_limit,
        }
    except ContentExtractionError:
        raise
    except Exception as e:
        logger.exception(f"yt-dlp probing failed for url={url} | reason={e}")
        raise ContentExtractionError(f"Failed to probe YouTube metadata: {str(e)}")

# ---------- 第三步：字幕优先提取 ----------

def _expand_language_preferences(prefer_langs: Optional[List[str]]) -> List[str]:
    """
    将用户的语言优先级扩展为更细语言代码，保持顺序且去重。
    例如: ["zh","en"] -> ["zh-Hans","zh-Hant","zh","zh-CN","zh-TW","en"]
    也支持其他传入语言码，原样保留。
    """
    prefer_langs = prefer_langs or ["zh", "en"]
    expanded: List[str] = []
    for code in prefer_langs:
        code_lower = (code or "").lower()
        variants: List[str]
        if code_lower == "zh":
            variants = ["zh-Hans", "zh-Hant", "zh", "zh-CN", "zh-TW"]
        elif code_lower == "en":
            variants = ["en"]
        else:
            variants = [code]
        for v in variants:
            if v not in expanded:
                expanded.append(v)
    return expanded

def clean_transcript_text(raw_text: str) -> str:
    """
    轻量清洗字幕文本：
    - 去掉常见方括号提示（[Music] 等）
    - 折叠多空行
    - 压缩重复空格
    """
    text = raw_text or ""
    # 去掉方括号内的常见噪声标签
    text = re.sub(r"\s*\[(?:music|applause|laughter|silence|ambient noise|.+?)\]\s*", " ", text, flags=re.IGNORECASE)
    # 压缩多空格
    text = re.sub(r"[ \t]{2,}", " ", text)
    # 折叠多空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def normalize_transcript_text(text: str) -> str:
    """
    第四步：进一步规范化合并结果（在基础清洗之后）：
    - 去除零宽字符/不可见字符
    - 连续重复行去重
    - 统一空行与空白
    """
    s = (text or "").replace("\u200b", "").replace("\ufeff", "")
    lines = [ln.strip() for ln in s.splitlines()]
    normalized: List[str] = []
    prev = None
    for ln in lines:
        if not ln:
            # 折叠多空行
            if normalized and normalized[-1] != "":
                normalized.append("")
            continue
        if ln == prev:
            continue
        normalized.append(ln)
        prev = ln
    out = "\n".join(normalized)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()

async def fetch_youtube_transcript(
    video_id: str,
    prefer_langs: Optional[List[str]] = None,
    fallback_any_language: bool = True,
) -> Dict[str, Any]:
    """
    第三步：仅用字幕将视频转成文本（不做 ASR）。
    - 优先人工字幕，其次自动字幕
    - 语言优先级默认 ["zh","en"]，同时会展开常见变体
    - 若 fallback_any_language=True，在中英都不可用时，使用任意可用字幕（优先人工）
    返回:
      {
        "text": str,
        "transcript_type": "human" | "auto",
        "lang": str,
        "orig_len": int,
      }
    """
    if not _yt_transcript_available:
        raise ContentExtractionError(
            "youtube-transcript-api not installed. Please `pip install youtube-transcript-api`."
        )
    try:
        languages = _expand_language_preferences(prefer_langs)
        # 获取可用字幕列表（阻塞 -> 线程池）
        transcripts = await asyncio.to_thread(YouTubeTranscriptApi.list_transcripts, video_id)

        selected = None
        transcript_type = ""
        # 先找人工字幕
        try:
            selected = transcripts.find_transcript(languages)
            transcript_type = "human"
        except Exception:
            # 再找自动字幕
            try:
                selected = transcripts.find_generated_transcript(languages)
                transcript_type = "auto"
            except Exception:
                if fallback_any_language:
                    # 任意人工字幕
                    try:
                        # Transcripts 对象可迭代
                        manual = [t for t in transcripts if not getattr(t, "is_generated", False)]
                        if manual:
                            selected = manual[0]
                            transcript_type = "human"
                        else:
                            auto = [t for t in transcripts if getattr(t, "is_generated", False)]
                            if auto:
                                selected = auto[0]
                                transcript_type = "auto"
                    except Exception:
                        selected = None
                # 若仍无，抛错
        if not selected:
            raise ContentExtractionError("该视频无可用字幕，暂不支持（后续将支持音频转写）")

        # 拉取字幕条目（阻塞 -> 线程池）
        items = await asyncio.to_thread(selected.fetch)
        lines: List[str] = []
        for it in items or []:
            txt = (it.get("text") or "").strip()
            if txt:
                lines.append(txt)
        merged = "\n".join(lines).strip()
        if not merged:
            raise ContentExtractionError("字幕拉取为空")
        cleaned = clean_transcript_text(merged)
        return {
            "text": cleaned,
            "transcript_type": transcript_type or ("auto" if getattr(selected, "is_generated", False) else "human"),
            "lang": getattr(selected, "language_code", "") or "",
            "orig_len": len(cleaned),
        }
    except (NoTranscriptFound, TranscriptsDisabled):
        raise ContentExtractionError("该视频无字幕或字幕被禁用，暂不支持（后续将支持音频转写）")
    except (CouldNotRetrieveTranscript, VideoUnavailable) as e:
        raise ContentExtractionError(f"字幕获取失败：{str(e)}")
    except ContentExtractionError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching transcript for video_id={video_id}")
        raise ContentExtractionError(f"字幕提取异常：{str(e)}")

# ---------- 编排：串联第1/2/3步 ----------

async def ingest_youtube_url(
    url: str,
    prefer_langs: Optional[List[str]] = None,
    fallback_any_language: bool = True,
) -> Dict[str, Any]:
    """
    串联第1/2/3步，将 YouTube 链接转换为可用文本与元信息。
    - Step1: validate_and_get_video_id（本地校验）
    - Step2: probe_youtube_basic_info（轻量探测，确保可解析）
    - Step3: fetch_youtube_transcript（仅字幕，不做 ASR）
    返回:
      {
        "text": str,
        "meta": {
          "videoId": str,
          "title": str,
          "duration": int,
          "transcript_type": "human"|"auto",
          "lang": str,
        }
      }
    """
    # Step 1
    vid_from_url = validate_and_get_video_id(url)
    logger.info(f"[youtube] step1 ok | video_id={vid_from_url}")
    # Step 2
    basic = probe_youtube_basic_info(url)
    logger.info(
        "[youtube] step2 ok | video_id={} | title={} | duration={} | availability={}",
        basic.get("videoId"),
        basic.get("title"),
        basic.get("duration"),
        basic.get("availability"),
    )
    # Step 3
    tr = await fetch_youtube_transcript(
        video_id=basic.get("videoId") or vid_from_url,
        prefer_langs=prefer_langs,
        fallback_any_language=fallback_any_language,
    )
    # Step 4: 清洗 + 合并（进一步规范化）
    final_text = normalize_transcript_text(tr.get("text") or "")
    logger.info(
        "[youtube] step3+4 ok | video_id={} | lang={} | type={} | text_len={}",
        basic.get("videoId"),
        tr.get("lang"),
        tr.get("transcript_type"),
        len(final_text),
    )
    return {
        "text": final_text,
        "meta": {
            "videoId": basic.get("videoId") or vid_from_url,
            "title": basic.get("title") or "",
            "duration": basic.get("duration") or 0,
            "transcript_type": tr.get("transcript_type") or "",
            "lang": tr.get("lang") or "",
        },
    }
async def extract_text_from_url(url: str) -> str:
    """
    从 URL 提取主要文本内容。
    """
    try:
        logger.info(f"Starting URL extraction: {url}")

        # 确保URL有协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            logger.debug(f"URL protocol added: {url}")

        async with httpx.AsyncClient() as client:
            logger.debug("Sending HTTP request...")
            response = await client.get(url, timeout=30.0)
            logger.debug(f"HTTP response status: {response.status_code}")
            response.raise_for_status()

        logger.debug("Parsing HTML content...")
        doc = Document(response.text)
        summary = doc.summary()
        logger.debug(f"Readability summary length: {len(summary)}")

        soup = BeautifulSoup(summary, "html.parser")
        text = soup.get_text()

        # 清理文本
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result = "\n".join(lines)
        logger.info(f"Extraction complete. Length: {len(result)}")

        if not result:
            raise ContentExtractionError("Extracted text is empty")

        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during extraction: {e}")
        raise ContentExtractionError(f"Failed to download URL: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error extracting from URL: {url}")
        raise ContentExtractionError(f"Error extracting from URL: {str(e)}")


async def extract_text_from_docx(file: UploadFile) -> str:
    """
    从 DOCX 文件提取文本。
    """
    try:
        logger.info(f"Starting DOCX extraction: {file.filename}")
        content = await file.read()
        doc = docx.Document(io.BytesIO(content))

        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())

        result = "\n".join(text_parts)
        logger.info(f"DOCX extraction complete. Length: {len(result)}")
        return result

    except Exception as e:
        logger.exception(f"Error extracting from DOCX: {file.filename}")
        raise ContentExtractionError(f"Error extracting from DOCX: {str(e)}")


async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    从 PDF 文件提取文本。
    """
    try:
        logger.info(f"Starting PDF extraction: {file.filename}")
        content = await file.read()
        pdf_reader = pypdf.PdfReader(io.BytesIO(content))

        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text and text.strip():
                text_parts.append(text.strip())

        result = "\n".join(text_parts)
        logger.info(f"PDF extraction complete. Length: {len(result)}")
        return result

    except Exception as e:
        logger.exception(f"Error extracting from PDF: {file.filename}")
        raise ContentExtractionError(f"Error extracting from PDF: {str(e)}")


async def extract_text_from_image(file: UploadFile) -> str:
    """
    从图片文件提取文本（OCR）。支持常见格式：png/jpg/jpeg/webp。
    优先使用 RapidOCR；若不可用则报错提示安装。
    """
    if _rapid_ocr is None:
        raise ContentExtractionError(
            "OCR not available. Please install rapidocr-onnxruntime."
        )
    try:
        logger.info(f"Starting IMAGE OCR: {file.filename}")
        content = await file.read()
        # 基础预处理：转 RGB，尽量消除模式差异
        image = Image.open(io.BytesIO(content)).convert("RGB")
        np_img = np.array(image)
        result, _ = _rapid_ocr(np_img)
        lines = []
        for item in (result or []):
            # 兼容不同版本 RapidOCR 的返回：
            # 1) [box, text, score]
            # 2) [box, (text, score)]
            text = ""
            if isinstance(item, (list, tuple)):
                if len(item) >= 3:
                    # [box, text, score]
                    text = str(item[1] or "")
                elif len(item) == 2:
                    second = item[1]
                    if isinstance(second, (list, tuple)) and second:
                        text = str(second[0] or "")
                    else:
                        text = str(second or "")
            else:
                # 非预期结构，跳过
                continue
            if text.strip():
                lines.append(text.strip())
        extracted = "\n".join(lines)
        logger.info(f"IMAGE OCR complete. Length: {len(extracted)}")
        if not extracted.strip():
            # 给到用户可读的错误，便于前端提示
            raise ContentExtractionError("OCR result is empty. Try a clearer image.")
        return extracted
    except ContentExtractionError:
        raise
    except Exception as e:
        logger.exception(f"Error extracting from IMAGE: {file.filename}")
        raise ContentExtractionError(f"Error extracting from IMAGE: {str(e)}")

 
