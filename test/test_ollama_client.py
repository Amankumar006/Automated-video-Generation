"""
Tests for OllamaClient and Project Aether Ollama Cloud Integration.
Covers:
- Thinking tag stripping (<think>...</think>, unclosed tags, case insensitivity)
- Robust JSON extraction with code fences and LaTeX sanitization
- OllamaResponse dict and attribute behaviors
- Automatic model priority fallback on HTTP errors, API errors, and timeouts
- Live/mock Ollama API generate and chat calls
- Project Aether LLM-assisted complexity evaluation, narrative breakdown, and production brief generation
- Script generator routing to Ollama Cloud
"""

import json
from unittest.mock import MagicMock, patch
import pytest
import requests

import numpy as np

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.schemas import ComplexityLevel, ComplexityPlan, ShotRequirement
from aether.director.orchestrator import AetherDirector, generate_production_brief
from aether.director.schemas import DirectorProductionBrief, FilmScene
from aether.state.schemas import SceneState
from pipeline.ollama_client import (
    DEFAULT_MODELS,
    DEFAULT_VISION_MODELS,
    OllamaClient,
    OllamaResponse,
    encode_image_to_base64,
    extract_json_payload,
    strip_thinking_tags,
)


# ==============================================================================
# 1. Thinking Tag Stripping Tests
# ==============================================================================

def test_strip_thinking_tags_basic():
    raw = "<think>Let me analyze the problem first...</think>Hello world!"
    assert strip_thinking_tags(raw) == "Hello world!"


def test_strip_thinking_tags_unclosed():
    raw = "Intro <think>This stream was abruptly cut off while reasoning..."
    assert strip_thinking_tags(raw) == "Intro"


def test_strip_thinking_tags_multiple_variants():
    raw = "<THINK>Plan 1</THINK>First <thought>Plan 2</thought>Second <reasoning>Plan 3</reasoning>Third"
    assert strip_thinking_tags(raw) == "First Second Third"


def test_strip_thinking_tags_empty_and_no_tags():
    assert strip_thinking_tags("") == ""
    assert strip_thinking_tags("   ") == ""
    assert strip_thinking_tags("Pure text without any tags") == "Pure text without any tags"


# ==============================================================================
# 2. JSON Extraction Tests
# ==============================================================================

def test_extract_json_payload_plain_json():
    raw = '{"id": "test_1", "count": 42}'
    res = extract_json_payload(raw)
    assert res == {"id": "test_1", "count": 42}


def test_extract_json_payload_markdown_code_fences():
    raw = '```json\n{\n  "title": "Attention Mechanism",\n  "beats": [1, 2, 3]\n}\n```'
    res = extract_json_payload(raw)
    assert res["title"] == "Attention Mechanism"
    assert res["beats"] == [1, 2, 3]


def test_extract_json_payload_with_thinking_and_fences():
    raw = """
<think>
Thinking about the response format:
Must return valid JSON with beat structure.
</think>
```json
{
  "status": "ok",
  "score": 98.5
}
```
"""
    res = extract_json_payload(raw)
    assert res["status"] == "ok"
    assert res["score"] == 98.5


def test_extract_json_payload_latex_sanitization():
    raw = r'{"formula": "\alpha + \beta = \gamma", "fraction": "\frac{a}{b}"}'
    res = extract_json_payload(raw)
    assert "formula" in res
    assert "fraction" in res


def test_extract_json_payload_fallback_defaults():
    raw = "Not valid JSON at all!"
    res = extract_json_payload(raw, fallback_defaults={"error": True})
    assert res == {"error": True}


def test_extract_json_payload_empty_raises_or_fallbacks():
    with pytest.raises(ValueError):
        extract_json_payload("")
    assert extract_json_payload("", fallback_defaults={"default": 1}) == {"default": 1}


# ==============================================================================
# 3. OllamaResponse Tests
# ==============================================================================

def test_ollama_response_dict_and_attr_access():
    data = {"status": "success", "count": 10}
    resp = OllamaResponse(
        data=data,
        text='{"status": "success", "count": 10}',
        raw="<think>t</think>...",
        model="gpt-oss:120b:cloud",
        thinking="some reasoning",
    )

    # Dict access
    assert resp["status"] == "success"
    assert resp.get("count") == 10
    assert "status" in resp
    assert resp.to_dict() == data

    # Attribute access
    assert resp.model == "gpt-oss:120b:cloud"
    assert resp.thinking == "some reasoning"
    assert resp.text == '{"status": "success", "count": 10}'
    assert str(resp) == '{"status": "success", "count": 10}'


# ==============================================================================
# 4. OllamaClient Unit Tests (Mocked Networking)
# ==============================================================================

def test_ollama_client_init_and_url_normalization():
    client1 = OllamaClient(host="localhost:11434/")
    assert client1.host == "http://localhost:11434"

    client2 = OllamaClient(host="https://my-ollama-cloud.com/")
    assert client2.host == "https://my-ollama-cloud.com"

    client3 = OllamaClient(models=["custom:model"])
    assert client3.models == ["custom:model"]


@patch("requests.get")
def test_ollama_client_is_available_and_list_models(mock_get):
    client = OllamaClient()

    # Success check
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "models": [{"name": "gpt-oss:120b:cloud"}, {"name": "gemma4:31b:cloud"}]
    }
    assert client.is_available() is True
    models = client.list_models()
    assert "gpt-oss:120b:cloud" in models

    # Failure check
    mock_get.side_effect = requests.ConnectionError("Connection refused")
    assert client.is_available() is False
    assert client.list_models() == []


@patch("requests.post")
def test_ollama_client_generate_completion_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "gpt-oss:120b",
        "response": '```json\n{"message": "Hello from mock"}\n```',
        "done": True,
    }
    mock_post.return_value = mock_resp

    client = OllamaClient()
    res = client.generate_completion(prompt="Say hi in JSON", format="json")

    assert res["message"] == "Hello from mock"
    assert res.model == "gpt-oss:120b:cloud"


@patch("requests.post")
def test_ollama_client_chat_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "gpt-oss:120b",
        "message": {"role": "assistant", "content": '{"chat": "ok"}'},
        "done": True,
    }
    mock_post.return_value = mock_resp

    client = OllamaClient()
    res = client.chat(messages=[{"role": "user", "content": "ping"}], format="json")

    assert res["chat"] == "ok"
    assert res.model == "gpt-oss:120b:cloud"


@patch("requests.post")
def test_ollama_client_automatic_model_fallback(mock_post):
    # First model returns 404, second model returns 200 OK
    resp_fail = MagicMock()
    resp_fail.status_code = 404
    resp_fail.text = '{"error": "model not found"}'

    resp_ok = MagicMock()
    resp_ok.status_code = 200
    resp_ok.json.return_value = {
        "model": "gemma4:31b",
        "response": '{"fallback_success": true}',
        "done": True,
    }

    mock_post.side_effect = [resp_fail, resp_ok]

    client = OllamaClient(models=["gpt-oss:120b:cloud", "gemma4:31b:cloud"])
    res = client.generate_completion(prompt="test", format="json")

    assert res["fallback_success"] is True
    assert res.model == "gemma4:31b:cloud"
    assert mock_post.call_count == 2


@patch("requests.post")
def test_ollama_client_all_models_fail_raises(mock_post):
    resp_fail = MagicMock()
    resp_fail.status_code = 500
    resp_fail.text = "Internal Server Error"
    mock_post.return_value = resp_fail

    client = OllamaClient(models=["m1", "m2"])
    with pytest.raises(RuntimeError) as exc_info:
        client.generate_completion(prompt="test", format="json")

    assert "All Ollama candidate models failed" in str(exc_info.value)


# ==============================================================================
# 5. Live Local Ollama Cloud Verification
# ==============================================================================

def test_live_ollama_cloud_connectivity():
    client = OllamaClient()
    if not client.is_available():
        pytest.skip("Local Ollama daemon is not running on localhost:11434")

    # Live generation using gpt-oss:120b:cloud
    res = client.generate_completion(
        prompt="Respond with a JSON object: {\"live_test\": \"passed\", \"cost\": 0.0}",
        model="gpt-oss:120b:cloud",
        format="json",
        timeout=30.0,
    )
    assert isinstance(res, dict)
    assert res.get("live_test") == "passed" or "live_test" in res
    assert res.model == "gpt-oss:120b:cloud"


def test_live_ollama_cloud_fallback_model():
    client = OllamaClient()
    if not client.is_available():
        pytest.skip("Local Ollama daemon is not running on localhost:11434")

    # Force fallback from invalid model to gemma4:31b:cloud
    client = OllamaClient(models=["invalid_model_for_fallback_test", "gemma4:31b:cloud"])
    res = client.generate_completion(
        prompt="Respond with JSON: {\"status\": \"fallback_verified\"}",
        format="json",
        timeout=30.0,
    )
    assert isinstance(res, dict)
    assert res.get("status") == "fallback_verified" or "status" in res
    assert res.model == "gemma4:31b:cloud"


# ==============================================================================
# 6. Project Aether LLM Integration Tests (Complexity & Director)
# ==============================================================================

def test_complexity_planner_evaluate_with_llm_mocked():
    planner = ComplexityPlanner()
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "complexity_level": 4,
            "rationale": ["Multi-character handoff", "Complex camera path"],
            "recommended_representations": ["previs_3d", "depth_map"],
            "recommended_provider": "kling_3_0",
        },
        model="gpt-oss:120b:cloud",
    )

    state = SceneState(scene_id="SC_001", location="stage")
    req = ShotRequirement(shot_id="SHOT_001", target_duration=5.0)

    plan = planner.evaluate_with_llm(
        scene_state=state,
        shot_requirement=req,
        client=mock_client,
    )

    assert plan.complexity_level == ComplexityLevel.THREED_BLOCKING
    assert "Multi-character handoff" in plan.rationale[0]
    assert plan.recommended_provider.value == "kling_3_0"


def test_aether_director_decompose_narrative_with_llm_mocked():
    director = AetherDirector()
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "scenes": [
                {
                    "scene_id": "SC_001",
                    "narrative_beat": "Establishing high tension in server room",
                    "location": "server_room",
                    "shot_list_requirements": [
                        {"shot_id": "SHOT_001", "target_duration": 4.0, "camera_movement": "dolly_in"},
                        {"shot_id": "SHOT_002", "target_duration": 6.0, "camera_movement": "pan_right"},
                    ],
                }
            ]
        },
        model="gpt-oss:120b:cloud",
    )

    brief = DirectorProductionBrief(
        title="Silicon Breach",
        logline="A rogue agent infiltrates an H100 GPU cluster.",
        target_duration=10.0,
    )

    scenes = director.decompose_narrative_with_llm(brief, client=mock_client)
    assert len(scenes) == 1
    assert scenes[0].scene_id == "SC_001"
    assert len(scenes[0].shot_list_requirements) == 2


def test_generate_production_brief_with_llm_mocked():
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "title": "Quantum Odyssey",
            "logline": "Scientists discover an anomaly in superconducting qubits.",
            "target_duration": 45.0,
            "aspect_ratio": "16:9",
            "visual_style": "cyberpunk noir",
            "target_models": ["veo_3_1"],
            "speculative_draft": True,
            "budget_limit": 50.0,
        },
        model="gpt-oss:120b:cloud",
    )

    brief = generate_production_brief(
        premise="Scientists discover an anomaly in superconducting qubits.",
        target_duration=45.0,
        aspect_ratio="16:9",
        client=mock_client,
    )

    assert brief.title == "Quantum Odyssey"
    assert brief.aspect_ratio == "16:9"
    assert brief.target_duration == 45.0
    assert brief.budget_limit == 50.0


# ==============================================================================
# 7. Script Generator Ollama Routing Test
# ==============================================================================

@patch("pipeline.script_generator.OllamaClient")
def test_script_generator_ollama_routing(mock_ollama_cls, monkeypatch):
    from pipeline.script_generator import generate_script

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    mock_instance = MagicMock()
    mock_ollama_cls.return_value = mock_instance

    mock_script_data = {
        "id": "speculative_decoding_test",
        "title": "Speculative Decoding Speedup",
        "category": "mechanism_deepdive",
        "domain_taxonomy": "hardware_efficiency",
        "hook_tag": "SPEEDUP SHOWDOWN",
        "beats": [
            {
                "beat_id": 1,
                "text": "Every time your coding agent writes Python, your GPU stalls waiting for memory.",
                "visual_focus": "GPU stall visual",
                "highlight_words": {"GPU stalls": "#EF4444"},
                "svo_action": {
                    "subject": "GPU Memory",
                    "action_verb": "stalls",
                    "direct_object": "Compute Cores",
                    "anchor_word": "stalls",
                    "semantic_role": "state_transition",
                },
                "visual_blueprint": {
                    "layout": "grid_memory",
                    "title": "GPU MEMORY BOTTLENECK",
                    "sub": "VRAM memory stall latency",
                    "params": {"active_cell_label": "HBM3 Stalls"},
                },
            },
            {
                "beat_id": 2,
                "text": "Why? Sequential token generation creates a massive memory bandwidth wall.",
                "visual_focus": "Memory wall",
                "highlight_words": {"bandwidth wall": "#EF4444"},
                "svo_action": {"subject": "Memory Wall", "action_verb": "blocks", "direct_object": "Bandwidth", "anchor_word": "bandwidth", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "barrier_separation", "title": "MEMORY WALL", "sub": "Sequential tokens", "params": {}},
            },
            {
                "beat_id": 3,
                "text": "Speculative decoding breaks this wall using a lightweight draft model to predict tokens.",
                "visual_focus": "Draft model speculation",
                "highlight_words": {"draft model": "#38BDF8"},
                "svo_action": {"subject": "Draft Model", "action_verb": "predicts", "direct_object": "Token Sequence", "anchor_word": "predict", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "SPECULATIVE FORWARD PASS", "sub": "Draft model", "params": {}},
            },
            {
                "beat_id": 4,
                "text": "The large model verifies all predicted tokens in a single parallel forward pass.",
                "visual_focus": "Parallel verification",
                "highlight_words": {"parallel": "#34D399"},
                "svo_action": {"subject": "Target Model", "action_verb": "verifies", "direct_object": "Draft Tokens", "anchor_word": "verifies", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "pipeline_stages", "title": "PARALLEL VERIFICATION", "sub": "Verification pass", "params": {}},
            },
            {
                "beat_id": 5,
                "text": "The result is 3x higher throughput with zero mathematical degradation in accuracy.",
                "visual_focus": "3x speedup metric",
                "highlight_words": {"3x higher throughput": "#34D399"},
                "svo_action": {"subject": "Speculative Engine", "action_verb": "delivers", "direct_object": "3x Speedup", "anchor_word": "throughput", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "comparison_side_by_side", "title": "3X THROUGHPUT GAIN", "sub": "Zero loss", "params": {}},
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily deep-dives into modern AI architecture.",
                "visual_focus": "Branding outro",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "demystifies", "direct_object": "AI Systems", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "catalog_routing", "title": "THE MODEL VERSE", "sub": "Daily AI deep-dives", "params": {}},
            },
        ],
        "math_formulas": [
            {"beat_id": 1, "latex": "$B_{\\mathrm{VRAM}} = 3.2\\,\\mathrm{TB/s}$", "fontsize": 24, "color": "#38BDF8"},
            {"beat_id": 2, "latex": "$\\mathcal{O}(N)$", "fontsize": 24, "color": "#EF4444"},
            {"beat_id": 3, "latex": "$\\mathbf{y} = M_{\\mathrm{draft}}(\\mathbf{x})$", "fontsize": 24, "color": "#38BDF8"},
            {"beat_id": 4, "latex": "$\\alpha_{\\mathrm{accept}} = 0.82$", "fontsize": 24, "color": "#F59E0B"},
            {"beat_id": 5, "latex": "$\\mathrm{Speedup} = 3.2\\times$", "fontsize": 24, "color": "#34D399"},
        ],
        "metadata": {
            "scale_metric": "3.2x",
            "scale_label": "Throughput Multiplier",
        },
    }

    mock_instance.generate_completion.return_value = OllamaResponse(
        data=mock_script_data,
        text=json.dumps(mock_script_data),
        model="gpt-oss:120b:cloud",
    )

    spec = generate_script(topic="Speculative Decoding in LLMs")

    assert "speculative" in spec["id"]
    assert len(spec["beats"]) == 6
    assert len(spec["math_formulas"]) == 5
    assert mock_instance.generate_completion.called


def test_strip_thinking_tags_attributes_and_reflection():
    raw = '<think model="deepseek" step="1">Analyzing context</think>Final Output'
    assert strip_thinking_tags(raw) == "Final Output"

    raw2 = '<reflection>\nSelf-critique here\n</reflection>Improved Output'
    assert strip_thinking_tags(raw2) == "Improved Output"

    raw3 = '<reasoning priority="high">\nStill reasoning...'
    assert strip_thinking_tags(raw3) == ""


def test_extract_json_payload_array_and_latex():
    raw_array = r'[{"formula": "\alpha + \beta"}, {"value": 42}]'
    res = extract_json_payload(raw_array)
    assert isinstance(res, list)
    assert len(res) == 2
    assert "formula" in res[0]
    assert res[1]["value"] == 42


def test_ollama_response_list_support():
    items = [{"shot_id": "SHOT_1"}, {"shot_id": "SHOT_2"}]
    resp = OllamaResponse(data=items, text=json.dumps(items), model="gpt-oss:120b:cloud")

    assert len(resp) == 2
    assert resp[0]["shot_id"] == "SHOT_1"
    assert resp[1]["shot_id"] == "SHOT_2"
    assert [x["shot_id"] for x in resp] == ["SHOT_1", "SHOT_2"]
    assert resp.to_dict() == items
    assert resp.model == "gpt-oss:120b:cloud"


def test_ollama_client_init_empty_models():
    client = OllamaClient(models=[])
    assert client.models == []


@patch("requests.post")
def test_ollama_client_stream_generate(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'{"response": "{\\"id\\": \\"test\\", ", "done": false}',
        b'{"response": "\\"val\\": 1}", "done": true}',
    ]
    mock_post.return_value = mock_resp

    client = OllamaClient()
    res = client.generate_completion(prompt="stream test", format="json", stream=True)
    assert res["id"] == "test"
    assert res["val"] == 1
    assert res.text == '{"id": "test", "val": 1}'


@patch("requests.post")
def test_ollama_client_stream_chat(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'{"message": {"role": "assistant", "content": "hello "}, "done": false}',
        b'{"message": {"role": "assistant", "content": "world"}, "done": true}',
    ]
    mock_post.return_value = mock_resp

    client = OllamaClient()
    res = client.chat(messages=[{"role": "user", "content": "hi"}], stream=True)
    assert res.text == "hello world"
    assert "hello world" in str(res)


@patch("pipeline.script_generator.OllamaClient")
def test_script_generator_gemini_none_no_crash(mock_ollama_cls, monkeypatch):
    import pipeline.script_generator as sg

    monkeypatch.setattr(sg, "genai", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    mock_inst = MagicMock()
    mock_inst.generate_completion.return_value = OllamaResponse(
        data={
            "id": "gemini_none_test",
            "title": "Title",
            "beats": [{"beat_id": i, "text": f"Beat {i}"} for i in range(1, 7)],
        },
        model="gpt-oss:120b:cloud",
    )
    mock_ollama_cls.return_value = mock_inst

    spec = sg.generate_script(topic="Speculative Decoding")
    assert spec["id"] == "gemini_none_test"
    assert mock_inst.generate_completion.called


@patch("pipeline.script_generator.OllamaClient")
def test_script_generator_gemini_429_immediate_fallback(mock_ollama_cls, monkeypatch):
    import pipeline.script_generator as sg

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    mock_genai = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded")
    mock_genai.GenerativeModel.return_value = mock_model
    monkeypatch.setattr(sg, "genai", mock_genai)

    mock_ollama_inst = MagicMock()
    mock_ollama_inst.generate_completion.return_value = OllamaResponse(
        data={
            "id": "quota_recovery_test",
            "title": "Quota Recovery",
            "beats": [{"beat_id": i, "text": f"Beat {i}"} for i in range(1, 7)],
        },
        model="gpt-oss:120b:cloud",
    )
    mock_ollama_cls.return_value = mock_ollama_inst

    spec = sg.generate_script(topic="Speculative Decoding")
    assert spec["id"] == "quota_recovery_test"
    assert mock_model.generate_content.call_count == 1
    assert mock_ollama_inst.generate_completion.called


# ==============================================================================
# 8. Ollama Vision Completion & Image Encoding Tests
# ==============================================================================

def test_encode_image_to_base64_from_bytes():
    raw_bytes = b"fake_png_data"
    encoded = encode_image_to_base64(raw_bytes)
    assert isinstance(encoded, str)
    assert encoded == "ZmFrZV9wbmdfZGF0YQ=="


def test_encode_image_to_base64_from_numpy():
    frame = np.zeros((16, 16, 3), dtype=np.uint8)
    encoded = encode_image_to_base64(frame)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_encode_image_to_base64_from_file(tmp_path):
    img_file = tmp_path / "test_frame.png"
    img_file.write_bytes(b"image_content_binary")
    encoded = encode_image_to_base64(img_file)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_encode_image_to_base64_from_data_uri():
    data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    encoded = encode_image_to_base64(data_uri)
    assert encoded == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"


def test_encode_image_to_base64_from_raw_base64():
    raw_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    encoded = encode_image_to_base64(raw_b64)
    assert encoded == raw_b64


def test_encode_image_to_base64_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        encode_image_to_base64("/nonexistent/path/to/frame.png")


@patch("requests.post")
def test_ollama_client_generate_vision_completion_payload(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "gemma4:31b:cloud",
        "response": '{"passed": true, "defects": []}',
        "done": True,
    }
    mock_post.return_value = mock_resp

    client = OllamaClient()
    res = client.generate_vision_completion(
        prompt="Inspect this keyframe for anatomy",
        image_paths=[b"test_image_data"],
        model="gemma4:31b:cloud",
        format="json",
    )

    assert res["passed"] is True
    assert res.model == "gemma4:31b:cloud"
    assert mock_post.called

    # Verify payload contains images field
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert "images" in payload
    assert len(payload["images"]) == 1
    assert payload["model"] == "gemma4:31b:cloud"
    assert payload["format"] == "json"


@patch("requests.post")
def test_ollama_client_generate_vision_completion_fallback(mock_post):
    # First model fails, second model succeeds
    resp_fail = MagicMock()
    resp_fail.status_code = 404
    resp_fail.text = "Model not found"

    resp_ok = MagicMock()
    resp_ok.status_code = 200
    resp_ok.json.return_value = {
        "model": "minicpm-v:latest",
        "response": '{"passed": false, "defects": [{"type": "polydactyly"}]}',
        "done": True,
    }
    mock_post.side_effect = [resp_fail, resp_ok]

    client = OllamaClient(vision_models=["gemma4:31b:cloud", "minicpm-v:latest"])
    res = client.generate_vision_completion(
        prompt="Inspect",
        image_paths=[b"dummy_image"],
        model="gemma4:31b:cloud",
        format="json",
    )

    assert res["passed"] is False
    assert len(res["defects"]) == 1
    assert res.model == "minicpm-v:latest"
    assert mock_post.call_count == 2


@patch("requests.post")
def test_ollama_client_generate_vision_completion_fallback_defaults(mock_post):
    resp_fail = MagicMock()
    resp_fail.status_code = 500
    resp_fail.text = "Server Error"
    mock_post.return_value = resp_fail

    client = OllamaClient(vision_models=["gemma4:31b:cloud"])
    fallback = {"passed": True, "defects": [], "fallback": True}

    res = client.generate_vision_completion(
        prompt="Inspect",
        image_paths=[b"dummy_image"],
        format="json",
        fallback_defaults=fallback,
    )

    assert res["passed"] is True
    assert res["fallback"] is True
    assert res.model == "fallback:heuristic"


def test_encode_image_to_base64_from_float_numpy():
    # Float frame in [0.0, 1.0] should be scaled to [0, 255] and encoded without warnings
    frame = np.full((16, 16, 3), 0.5, dtype=np.float32)
    encoded = encode_image_to_base64(frame)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_encode_image_to_base64_from_4d_batch_tensor():
    # 4D tensor with batch size 1 should squeeze and encode cleanly
    frame = np.zeros((1, 16, 16, 3), dtype=np.uint8)
    encoded = encode_image_to_base64(frame)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


@patch("requests.post")
def test_ollama_client_generate_vision_completion_4d_tensor_input(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "gemma4:31b:cloud",
        "response": '{"passed": true, "defects": []}',
        "done": True,
    }
    mock_post.return_value = mock_resp

    client = OllamaClient()
    video_tensor = np.zeros((3, 16, 16, 3), dtype=np.uint8)
    res = client.generate_vision_completion(
        prompt="Inspect video frames",
        image_paths=video_tensor,
        model="gemma4:31b:cloud",
    )

    assert res["passed"] is True
    payload = mock_post.call_args[1]["json"]
    assert "images" in payload
    assert len(payload["images"]) == 3


@patch("requests.post")
def test_ollama_client_generate_vision_completion_fallback_to_heuristic_without_defaults(mock_post):
    resp_fail = MagicMock()
    resp_fail.status_code = 503
    resp_fail.text = "Model unavailable"
    mock_post.return_value = resp_fail

    client = OllamaClient(vision_models=["gemma4:31b:cloud"])
    res = client.generate_vision_completion(
        prompt="Inspect",
        image_paths=[b"dummy_image"],
        format="json",
        fallback_to_text=False,
    )

    assert res["passed"] is True
    assert res["fallback"] is True
    assert res.model == "fallback:heuristic"


@patch("requests.post")
def test_ollama_client_generate_vision_completion_fallback_on_error_false_raises(mock_post):
    resp_fail = MagicMock()
    resp_fail.status_code = 500
    resp_fail.text = "Server down"
    mock_post.return_value = resp_fail

    client = OllamaClient(vision_models=["gemma4:31b:cloud"])
    with pytest.raises(RuntimeError):
        client.generate_vision_completion(
            prompt="Inspect",
            image_paths=[b"dummy_image"],
            fallback_on_error=False,
        )


@patch("requests.post")
def test_ollama_client_generate_vision_completion_fallback_to_text(mock_post):
    # Vision endpoint fails, but text endpoint succeeds
    resp_vision_fail = MagicMock()
    resp_vision_fail.status_code = 404
    resp_vision_fail.text = "Vision model not found"

    resp_text_ok = MagicMock()
    resp_text_ok.status_code = 200
    resp_text_ok.json.return_value = {
        "model": "gpt-oss:120b:cloud",
        "response": '{"passed": true, "defects": []}',
        "done": True,
    }

    mock_post.side_effect = [resp_vision_fail, resp_text_ok]

    client = OllamaClient(vision_models=["gemma4:31b:cloud"])
    res = client.generate_vision_completion(
        prompt="Inspect keyframe",
        image_paths=[b"dummy_image"],
        format="json",
        fallback_to_text=True,
    )

    assert res["passed"] is True
    assert "fallback:text" in res.model



