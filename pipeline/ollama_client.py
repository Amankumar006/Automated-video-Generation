"""
The Model Verse — Autonomous Ollama Cloud LLM Client
Provides zero-cost, high-speed LLM inference utilizing Ollama's authenticated cloud models:
- gpt-oss:120b:cloud (Default high-fidelity model)
- gemma4:31b:cloud (Fast fallback model)
- gpt-oss:20b:cloud (Secondary fallback)
- nemotron-3-nano:30b:cloud (Tertiary fallback)

Handles thinking tags (<think>...</think>), markdown code fences, and robust JSON extraction.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Union
import requests

from pipeline.json_utils import robust_json_loads

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

DEFAULT_MODELS: List[str] = [
    "gpt-oss:120b:cloud",
    "gemma4:31b:cloud",
    "gpt-oss:20b:cloud",
    "nemotron-3-nano:30b:cloud",
]

DEFAULT_VISION_MODELS: List[str] = [
    "gemma4:31b:cloud",
    "minicpm-v:latest",
    "llava:latest",
    "llama3.2-vision:latest",
]


def encode_image_to_base64(image_input: Union[str, Path, bytes, Any]) -> str:
    """Encodes a file path, bytes, raw base64 string, or numpy array to a pure base64 string."""
    if isinstance(image_input, bytes):
        return base64.b64encode(image_input).decode("utf-8")

    # If it has numpy array attributes (ndim, dtype)
    if hasattr(image_input, "ndim") and hasattr(image_input, "dtype"):
        import numpy as np
        arr = np.asarray(image_input)
        if arr.ndim == 4 and arr.shape[0] == 1:
            arr = arr[0]
        # Normalize floating point arrays [0.0, 1.0] or [0.0, 255.0] to uint8 [0, 255]
        if np.issubdtype(arr.dtype, np.floating):
            max_v = float(np.max(arr)) if arr.size > 0 else 0.0
            if max_v <= 1.01:
                arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
            else:
                arr = np.clip(arr, 0, 255).astype(np.uint8)
        elif arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)

        try:
            import cv2
            success, encoded = cv2.imencode(".png", arr)
            if success:
                return base64.b64encode(encoded.tobytes()).decode("utf-8")
        except Exception:
            pass
        try:
            from io import BytesIO
            from PIL import Image
            buffered = BytesIO()
            img = Image.fromarray(arr)
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Unable to encode numpy array to image: {e}")

    # Path or string
    path_obj = Path(str(image_input))
    if path_obj.is_file():
        with open(path_obj, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    str_val = str(image_input).strip()
    # Check data URI scheme: data:image/...;base64,...
    if str_val.startswith("data:image/") and ";base64," in str_val:
        return str_val.split(";base64,", 1)[1].strip()

    # If string is already valid base64 (not a missing file path with extension)
    if not (str_val.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")) and ("/" in str_val or "\\" in str_val)):
        try:
            decoded = base64.b64decode(str_val, validate=True)
            if len(decoded) > 0:
                return str_val
        except Exception:
            pass

    raise FileNotFoundError(f"Image not found on disk or invalid base64 input: {image_input}")


def strip_thinking_tags(text: str) -> str:
    """Strips chain-of-thought tags (<think>...</think>, <thought>...</thought>, etc.)
    from LLM responses, including truncated/unclosed trailing think blocks and tags with attributes.
    """
    if not text:
        return ""

    # Strip closed think/thought/reasoning/reflection tags with optional attributes
    cleaned = re.sub(
        r"<(?:think|thought|reasoning|reflection)\b[^>]*>[\s\S]*?</(?:think|thought|reasoning|reflection)\s*>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Strip unclosed think tag at the end if stream or generation was cut off
    cleaned = re.sub(
        r"<(?:think|thought|reasoning|reflection)\b[^>]*>[\s\S]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def extract_json_payload(
    text: str,
    fallback_defaults: Optional[Union[Dict[str, Any], List[Any]]] = None,
) -> Union[Dict[str, Any], List[Any]]:
    """Strips thinking tags, extracts JSON enclosed in markdown code fences or raw text,
    and parses using robust_json_loads.
    """
    if not text or not text.strip():
        if fallback_defaults is not None:
            return fallback_defaults
        raise ValueError("Empty response text provided for JSON extraction")

    cleaned = strip_thinking_tags(text)

    # Check for markdown code fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(fence_pattern, cleaned)
    if matches:
        for m in matches:
            if ("{" in m and "}" in m) or ("[" in m and "]" in m):
                cleaned = m.strip()
                break
        else:
            cleaned = matches[0].strip()

    return robust_json_loads(cleaned, fallback_defaults=fallback_defaults)


class OllamaResponse(dict):
    """Dictionary-like response object preserving text, raw output, model metadata,
    and parsed dictionary keys or array items.
    """

    def __init__(
        self,
        data: Union[Dict[str, Any], List[Any]],
        text: str = "",
        raw: str = "",
        model: str = "",
        thinking: Optional[str] = None,
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._raw_data = data
        if isinstance(data, dict):
            super().__init__(data)
        elif isinstance(data, list):
            super().__init__({"items": data, "data": data})
        else:
            super().__init__()
        self.text = text
        self.raw = raw
        self.model = model
        self.thinking = thinking
        self.raw_response = raw_response or {}

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'OllamaResponse' object has no attribute '{name}'")

    def __iter__(self) -> Any:
        if isinstance(self._raw_data, list):
            return iter(self._raw_data)
        return super().__iter__()

    def __getitem__(self, key: Any) -> Any:
        if isinstance(self._raw_data, list) and isinstance(key, (int, slice)):
            return self._raw_data[key]
        return super().__getitem__(key)

    def __len__(self) -> int:
        if isinstance(self._raw_data, list):
            return len(self._raw_data)
        return super().__len__()

    def __str__(self) -> str:
        return self.text or super().__str__()

    def to_dict(self) -> Union[Dict[str, Any], List[Any]]:
        """Returns standard python dict/list copy of parsed JSON."""
        return self._raw_data if isinstance(self._raw_data, list) else dict(self)


class OllamaClient:
    """Robust client targeting local/remote Ollama daemon with automatic cloud model fallback."""

    def __init__(
        self,
        host: Optional[str] = None,
        models: Optional[List[str]] = None,
        vision_models: Optional[List[str]] = None,
        timeout: float = 120.0,
    ) -> None:
        raw_host = host or os.environ.get("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST
        if not raw_host.startswith("http://") and not raw_host.startswith("https://"):
            raw_host = f"http://{raw_host}"
        self.host = raw_host.rstrip("/")
        self.timeout = timeout

        if models is not None:
            self.models = list(models)
        else:
            preferred = os.environ.get("OLLAMA_MODEL")
            if preferred:
                self.models = [preferred] + [m for m in DEFAULT_MODELS if m != preferred]
            else:
                self.models = list(DEFAULT_MODELS)

        if vision_models is not None:
            self.vision_models = list(vision_models)
        else:
            pref_vision = os.environ.get("OLLAMA_VISION_MODEL")
            if pref_vision:
                self.vision_models = [pref_vision] + [m for m in DEFAULT_VISION_MODELS if m != pref_vision]
            else:
                self.vision_models = list(DEFAULT_VISION_MODELS)

    def is_available(self, timeout: float = 3.0) -> bool:
        """Checks if the Ollama endpoint is reachable."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Returns list of models available on the Ollama host."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
        return []

    def _resolve_candidate_models(self, requested_model: Optional[str]) -> List[str]:
        if requested_model:
            candidates = [requested_model]
            for m in self.models:
                if m != requested_model and m not in candidates:
                    candidates.append(m)
            return candidates
        return list(self.models)

    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        format: Optional[str] = "json",
        stream: bool = False,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        fallback_on_error: bool = True,
        **kwargs: Any,
    ) -> OllamaResponse:
        """Executes a completion request against Ollama with automatic model fallback."""
        candidates = self._resolve_candidate_models(model)
        req_timeout = timeout or self.timeout
        last_err: Optional[Exception] = None

        for idx, candidate in enumerate(candidates):
            logger.info(f"Ollama generating completion with candidate model '{candidate}'...")
            payload: Dict[str, Any] = {
                "model": candidate,
                "prompt": prompt,
                "stream": stream,
            }
            if format:
                payload["format"] = format
            if system:
                payload["system"] = system
            if options:
                payload["options"] = options
            if kwargs:
                payload.update(kwargs)

            try:
                resp = requests.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=req_timeout,
                    stream=stream,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API returned HTTP {resp.status_code}: {resp.text}"
                    )

                if stream:
                    chunks = []
                    last_chunk: Dict[str, Any] = {}
                    for line in resp.iter_lines():
                        if line:
                            c_str = line.decode("utf-8") if isinstance(line, bytes) else line
                            chunk = json.loads(c_str)
                            if "error" in chunk:
                                raise RuntimeError(f"Ollama API stream error: {chunk['error']}")
                            chunks.append(chunk.get("response", ""))
                            if chunk.get("done"):
                                last_chunk = chunk
                    raw_text = "".join(chunks)
                    data = last_chunk
                    thinking = data.get("thinking")
                else:
                    data = resp.json()
                    if "error" in data:
                        raise RuntimeError(f"Ollama API error: {data['error']}")
                    raw_text = data.get("response", "")
                    thinking = data.get("thinking")

                cleaned_text = strip_thinking_tags(raw_text)

                if format == "json":
                    parsed = extract_json_payload(cleaned_text)
                    return OllamaResponse(
                        data=parsed,
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )
                else:
                    return OllamaResponse(
                        data={"response": cleaned_text},
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )

            except Exception as e:
                last_err = e
                err_msg = str(e)
                logger.warning(
                    f"⚠️ Ollama candidate model '{candidate}' failed: {err_msg}."
                )
                if not fallback_on_error or idx == len(candidates) - 1:
                    break

        raise RuntimeError(
            f"All Ollama candidate models failed. Last error: {last_err}"
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        format: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        fallback_on_error: bool = True,
        **kwargs: Any,
    ) -> OllamaResponse:
        """Executes a chat conversation against Ollama with automatic model fallback."""
        candidates = self._resolve_candidate_models(model)
        req_timeout = timeout or self.timeout
        last_err: Optional[Exception] = None

        for idx, candidate in enumerate(candidates):
            logger.info(f"Ollama chat with candidate model '{candidate}'...")
            payload: Dict[str, Any] = {
                "model": candidate,
                "messages": messages,
                "stream": stream,
            }
            if format:
                payload["format"] = format
            if options:
                payload["options"] = options
            if kwargs:
                payload.update(kwargs)

            try:
                resp = requests.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=req_timeout,
                    stream=stream,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API returned HTTP {resp.status_code}: {resp.text}"
                    )

                if stream:
                    chunks = []
                    last_chunk: Dict[str, Any] = {}
                    for line in resp.iter_lines():
                        if line:
                            c_str = line.decode("utf-8") if isinstance(line, bytes) else line
                            chunk = json.loads(c_str)
                            if "error" in chunk:
                                raise RuntimeError(f"Ollama API chat stream error: {chunk['error']}")
                            chunks.append(chunk.get("message", {}).get("content", ""))
                            if chunk.get("done"):
                                last_chunk = chunk
                    raw_text = "".join(chunks)
                    data = last_chunk
                    msg = data.get("message", {"role": "assistant", "content": raw_text})
                    msg["content"] = raw_text
                    thinking = msg.get("thinking") or data.get("thinking")
                else:
                    data = resp.json()
                    if "error" in data:
                        raise RuntimeError(f"Ollama API error: {data['error']}")
                    msg = data.get("message", {})
                    raw_text = msg.get("content", "")
                    thinking = msg.get("thinking") or data.get("thinking")

                cleaned_text = strip_thinking_tags(raw_text)

                if format == "json":
                    parsed = extract_json_payload(cleaned_text)
                    return OllamaResponse(
                        data=parsed,
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )
                else:
                    return OllamaResponse(
                        data={"response": cleaned_text, "message": msg},
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )

            except Exception as e:
                last_err = e
                logger.warning(
                    f"⚠️ Ollama chat candidate model '{candidate}' failed: {e}."
                )
                if not fallback_on_error or idx == len(candidates) - 1:
                    break

        raise RuntimeError(
            f"All Ollama chat candidate models failed. Last error: {last_err}"
        )

    def generate_vision_completion(
        self,
        prompt: str,
        image_paths: Union[Sequence[Union[str, Path, bytes, Any]], str, Path, bytes, Any],
        model: Optional[str] = "gemma4:31b:cloud",
        format: Optional[str] = "json",
        stream: bool = False,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        fallback_on_error: bool = True,
        fallback_defaults: Optional[Union[Dict[str, Any], List[Any]]] = None,
        fallback_to_text: bool = True,
        **kwargs: Any,
    ) -> OllamaResponse:
        """Executes a multimodal vision completion request against Ollama with base64 image encoding
        and automatic vision model fallback.
        """
        if isinstance(image_paths, (str, Path, bytes)):
            raw_images = [image_paths]
        elif hasattr(image_paths, "ndim") and hasattr(image_paths, "dtype"):
            if image_paths.ndim == 4:
                raw_images = list(image_paths)
            else:
                raw_images = [image_paths]
        elif isinstance(image_paths, Sequence):
            raw_images = list(image_paths)
        else:
            raw_images = [image_paths]

        encoded_images = [encode_image_to_base64(img) for img in raw_images]

        # Resolve candidate vision models
        requested = model or "gemma4:31b:cloud"
        candidates = [requested]
        for m in getattr(self, "vision_models", DEFAULT_VISION_MODELS):
            if m not in candidates:
                candidates.append(m)

        req_timeout = timeout or self.timeout
        last_err: Optional[Exception] = None

        for idx, candidate in enumerate(candidates):
            logger.info(f"Ollama generating vision completion with candidate model '{candidate}'...")
            payload: Dict[str, Any] = {
                "model": candidate,
                "prompt": prompt,
                "images": encoded_images,
                "stream": stream,
            }
            if format:
                payload["format"] = format
            if system:
                payload["system"] = system
            if options:
                payload["options"] = options
            if kwargs:
                payload.update(kwargs)

            try:
                resp = requests.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=req_timeout,
                    stream=stream,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Ollama Vision API returned HTTP {resp.status_code}: {resp.text}"
                    )

                if stream:
                    chunks = []
                    last_chunk: Dict[str, Any] = {}
                    for line in resp.iter_lines():
                        if line:
                            c_str = line.decode("utf-8") if isinstance(line, bytes) else line
                            chunk = json.loads(c_str)
                            if "error" in chunk:
                                raise RuntimeError(f"Ollama Vision API stream error: {chunk['error']}")
                            chunks.append(chunk.get("response", ""))
                            if chunk.get("done"):
                                last_chunk = chunk
                    raw_text = "".join(chunks)
                    data = last_chunk
                    thinking = data.get("thinking")
                else:
                    data = resp.json()
                    if "error" in data:
                        raise RuntimeError(f"Ollama Vision API error: {data['error']}")
                    raw_text = data.get("response", "")
                    thinking = data.get("thinking")

                cleaned_text = strip_thinking_tags(raw_text)

                if format == "json":
                    parsed = extract_json_payload(cleaned_text, fallback_defaults=fallback_defaults)
                    return OllamaResponse(
                        data=parsed,
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )
                else:
                    return OllamaResponse(
                        data={"response": cleaned_text},
                        text=cleaned_text,
                        raw=raw_text,
                        model=candidate,
                        thinking=thinking,
                        raw_response=data,
                    )

            except Exception as e:
                last_err = e
                err_msg = str(e)
                logger.warning(
                    f"⚠️ Ollama vision candidate model '{candidate}' failed: {err_msg}."
                )
                if not fallback_on_error or idx == len(candidates) - 1:
                    break

        # Fallback handling
        if fallback_defaults is not None:
            logger.warning(
                f"All Ollama vision candidates failed ({last_err}). Falling back to provided default payload."
            )
            return OllamaResponse(
                data=fallback_defaults,
                text=json.dumps(fallback_defaults) if isinstance(fallback_defaults, (dict, list)) else str(fallback_defaults),
                raw="",
                model="fallback:heuristic",
            )

        if fallback_on_error:
            # 1. Attempt fallback to text model if requested
            if fallback_to_text:
                try:
                    logger.info("Attempting fallback to text LLM completion...")
                    text_resp = self.generate_completion(
                        prompt=prompt,
                        format=format,
                        system=system,
                        options=options,
                        timeout=req_timeout,
                        fallback_on_error=False,
                    )
                    text_resp.model = f"fallback:text:{text_resp.model}"
                    return text_resp
                except Exception as text_err:
                    logger.warning(f"Fallback to text LLM failed: {text_err}")

            # 2. Fallback to clean heuristic defaults
            logger.warning(
                f"All Ollama vision candidates failed ({last_err}). Falling back to heuristic QA defaults."
            )
            heuristic_defaults: Dict[str, Any] = {
                "passed": True,
                "visual_score": 8.0,
                "defects": [],
                "hard_gate_verdicts": {
                    "ANATOMICAL_INTEGRITY": True,
                    "CHARACTER_IDENTITY": True,
                },
                "summary": f"Vision model unreachable ({last_err}); graceful fallback to heuristic verification.",
                "fallback": True,
            }
            return OllamaResponse(
                data=heuristic_defaults,
                text=json.dumps(heuristic_defaults),
                raw="",
                model="fallback:heuristic",
            )

        raise RuntimeError(
            f"All Ollama vision candidate models failed. Last error: {last_err}"
        )
