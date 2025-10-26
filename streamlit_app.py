# streamlit_app.py
# ------------------------------------------------------------
# Hollywood-Style Viral Script & Scene-Prompt Generator
# Stack: Streamlit + OpenAI (python SDK >= 1.0)
# Author: You (Viet Vu)
# ------------------------------------------------------------
# Quickstart
# 1) pip install -U streamlit openai pydantic pandas python-docx
# 2) set OPENAI_API_KEY in your environment
# 3) streamlit run streamlit_app.py
# ------------------------------------------------------------
# Notes
# - App nhận tiêu đề (title) -> tạo kịch bản điện ảnh 6 phút theo cấu trúc Hollywood
# - Tách thành N cảnh (mặc định 45, tùy chọn 24/36/60...), mỗi cảnh ~8 giây
# - Mỗi cảnh sinh ra prompt JSON theo cấu trúc 15-layer nâng cao
# - Có Step 2: Xây dựng ngoại hình nhân vật & động vật; có thể Auto-generate bằng OpenAI hoặc điền tay
# - Xuất ra JSON/CSV; UI cho phép review, chỉnh sửa nhanh
# ------------------------------------------------------------

from __future__ import annotations
import os
import json
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
from pydantic import BaseModel, Field, validator

# OpenAI SDK (>=1.0 style)
try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# -------------------------
# Domain Models (Pydantic)
# -------------------------

PHASES_DEFAULT = [
    {"key": "cold_open", "name": "Cold Open – Chaos", "scenes": 5, "emotion": "Fear / Panic"},
    {"key": "flashback", "name": "Flashback – Origin", "scenes": 5, "emotion": "Mystery / Awe"},
    {"key": "first_attack", "name": "First Attack", "scenes": 8, "emotion": "Tension / Shock"},
    {"key": "team_formation", "name": "Rescue Team Formation", "scenes": 8, "emotion": "Resolve / Humanity"},
    {"key": "chaos_escalates", "name": "Chaos Escalates", "scenes": 10, "emotion": "Desperation / Courage"},
    {"key": "final_rescue", "name": "Final Rescue", "scenes": 8, "emotion": "Action / Redemption"},
    {"key": "ending_reflection", "name": "Ending & Reflection", "scenes": 5, "emotion": "Calm / Compassion"},
]

class CharacterSpec(BaseModel):
    name: str = Field(..., description="English name")
    origin: str = Field(..., description="Origin/Nationality/Culture")
    age: str = Field(..., description="Exact age (e.g., '32')")
    gender_role: str = Field(..., description="Gender / Role")
    body_shape: str = Field(..., description="Height/Weight/Proportions")
    skin: str
    face: str
    eyes: str
    eyebrows: str
    nose: str
    mouth: str
    jawline: str
    hair: str
    top: str
    bottom: str
    accessories: str
    outfit_style: str
    palette: str
    personality: str
    base_expression: str
    body_language: str
    backdrop_env: str
    extra_expressions: str
    voice_tone: str

class AnimalSpec(BaseModel):
    name: str
    species: str
    life_stage: str
    size_shape: str
    color_markings: str
    standout_features: str
    eyes: str
    ears: str
    snout: str
    mouth: str
    tail: str
    limbs: str
    accessories_marks: str
    default_expression: str
    extra_expressions: str
    personality: str
    signature_motion: str
    habitat: str
    relationship: str

class SceneJSON(BaseModel):
    scene_number: int
    phase_key: str
    phase_name: str
    objective: str
    core_emotion: str
    duration_sec: int = 8
    title: str
    cinematic_prompt: str
    continuity_notes: str
    # Optional helpful fields:
    dialogue_short: Optional[str] = None
    tools_props: Optional[str] = None
    camera_notes: Optional[str] = None
    lighting_notes: Optional[str] = None
    sound_music_notes: Optional[str] = None

    @validator("duration_sec")
    def _dur(cls, v):
        if v != 8:
            raise ValueError("Each scene must be 8 seconds by design.")
        return v

# -------------------------
# Helpers
# -------------------------

def _allocate_scenes(total_scenes: int) -> List[Dict[str, Any]]:
    """Distribute total_scenes across default phases proportionally to baseline 45.
    Ensures sum = total_scenes.
    """
    baseline = sum(p["scenes"] for p in PHASES_DEFAULT)  # 45
    # proportional allocation
    provisional = [max(1, round(total_scenes * p["scenes"] / baseline)) for p in PHASES_DEFAULT]
    # fix rounding
    diff = total_scenes - sum(provisional)
    # adjust from largest remainders approach (simple tweak: add to middle phases first)
    order = [4, 2, 3, 5, 0, 1, 6]  # tạm: ưu tiên Chaos Escalates, First Attack, Team Formation, Final Rescue...
    idx = 0
    while diff != 0:
        j = order[idx % len(order)]
        if diff > 0:
            provisional[j] += 1
            diff -= 1
        else:
            if provisional[j] > 1:
                provisional[j] -= 1
                diff += 1
        idx += 1

    allocation = []
    for i, p in enumerate(PHASES_DEFAULT):
        q = p.copy()
        q["scenes"] = provisional[i]
        allocation.append(q)
    return allocation

def _ensure_client() -> Optional[OpenAI]:
    if OpenAI is None:
        st.warning("openai package not found. Please `pip install openai`.")
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is not set.")
        return None
    try:
        client = OpenAI()
        return client
    except Exception as e:
        st.error(f"Failed to init OpenAI client: {e}")
        return None

# -------------------------
# Prompt Builders (System/User)
# -------------------------

SYSTEM_ROLE = (
    "You are a viral video scriptwriter specializing in dramatic, suspenseful storytelling, "
    "a top Hollywood filmmaker. Keep cinematic realism, photorealistic 4K tone, and film-grade detail."
)

GLOBAL_STYLE = (
    "Visual tone: photorealistic 4K, IMAX-level detail.\n"
    "Camera language: cinematic realism — sweeping aerials, micro-emotion close-ups, dynamic POV transitions.\n"
    "Lighting: dramatic contrast (teal/orange), volumetric atmosphere, backlight silhouettes.\n"
    "Sound: layered ambience (sirens, rain, roars, muffled cries).\n"
    "Music arc: ominous strings → heroic brass → soft piano at dawn.\n"
    "Emotional flow: Fear → Curiosity → Resolve → Chaos → Sacrifice → Redemption → Compassion.\n"
    "Moral closure: Even monsters crave survival; every rescue reveals our shared heartbeat with nature."
)

def build_characters_prompt(title: str) -> str:
    return f"""
Given the TITLE below, propose a concise but richly detailed Character & Animal bible for Step 2.
Return two JSON arrays: "characters" and "animals" with fields exactly as listed.
- Keep 2–6 human characters and 1–3 key animals relevant to an animal-rescue, high-stakes story.
- Ensure each field is filled with specific, visual details (not generic).

TITLE: {title}

For humans, include fields: {list(CharacterSpec.__fields__.keys())}
For animals, include fields: {list(AnimalSpec.__fields__.keys())}
""".strip()

def build_script_prompt(title: str, total_scenes: int, allocation: List[Dict[str, Any]]) -> str:
    # Build phase table description
    lines = ["Story Phase\tScenes\tEmotion Focus"]
    for p in allocation:
        lines.append(f"{p['name']}\t{p['scenes']}\t{p['emotion']}")
    phase_table = "\n".join(lines)

    return f"""
🎬 Instruction Chatbot: Giant Creature Rescue — Cinematic Script
Input: TITLE only. Output: A cinematic script divided into {total_scenes} scenes (each ~8 seconds).
Each scene must be written as one continuous cinematic paragraph (not a list), blending realistic action, emotional rhythm, and detailed visual description.
Keep the style directives:\n{GLOBAL_STYLE}

STRUCTURE TABLE\n{phase_table}

TITLE: {title}

Write the full script body as {total_scenes} numbered scenes (SCENE 1..{total_scenes}), each a single cinematic paragraph. No bullet lists.
""".strip()

FIFTEEN_LAYER = (
    "1) Scene Objective & Core Emotion; 2) Environment & Time of Day; 3) Character appearances from Step 2; "
    "4) Emotions & facial detail; 5) Props & rescue tools; 6) Brief dialogue; 7) Actions & teamwork; "
    "8) Camera & composition; 9) Lighting & color; 10) VFX & particles; 11) Audio & music; 12) Editing pace; "
    "13) Transition in/out; 14) Continuity to next scene; 15) Moral/emotional undercurrent."
)

def build_scene_prompt(title: str, scene_number: int, phase: Dict[str, Any], characters: List[CharacterSpec], animals: List[AnimalSpec], target_len: int) -> str:
    chars_json = json.dumps([c.dict() for c in characters], ensure_ascii=False, indent=2)
    animals_json = json.dumps([a.dict() for a in animals], ensure_ascii=False, indent=2)
    return f"""
TITLE: {title}
You will generate one continuous cinematic paragraph (~8 seconds) for SCENE {scene_number} following the 15-layer advanced structure below.
Strictly avoid itemized lists; write a single flowing paragraph. Aim length ≥ {target_len} characters.

PHASE: {phase['name']} | Core Emotion: {phase['emotion']}

CHARACTERS (Step 2 bible):\n{chars_json}
ANIMALS (Step 2 bible):\n{animals_json}

15-LAYER STRUCTURE:\n{FIFTEEN_LAYER}

GLOBAL STYLE (apply consistently):\n{GLOBAL_STYLE}
""".strip()

# -------------------------
# OpenAI Calls
# -------------------------

def llm_complete(client: OpenAI, model: str, system: str, user: str, temperature: float = 0.7, seed: Optional[int] = None, max_tokens: int = 1500) -> str:
    """Simple wrapper using Responses API if available; fallback to Chat Completions for older sdk.
    """
    try:
        # Prefer the modern Responses API if present
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"OpenAI call failed: {e}")

# -------------------------
# Streamlit UI
# -------------------------

st.set_page_config(page_title="Hollywood Scene Prompt Generator", page_icon="🎬", layout="wide")

st.title("🎬 Hollywood Scene-Prompt Generator (Animal Rescue)")
with st.sidebar:
    st.header("Settings")
    model = st.text_input("OpenAI model", value="gpt-4.1-mini")
    temperature = st.slider("Temperature", 0.0, 1.2, 0.7, 0.1)
    seed = st.number_input("Seed (optional)", value=0, min_value=0, step=1)
    total_scenes = st.selectbox("Total Scenes (N)", options=[24, 36, 45, 60], index=2)
    target_char_len = st.slider("Min chars per scene paragraph", 600, 2400, 1200, 100)
    max_tokens = st.slider("max_tokens per call", 512, 4096, 1500, 128)

# Session state
if "characters" not in st.session_state:
    st.session_state.characters: List[CharacterSpec] = []
if "animals" not in st.session_state:
    st.session_state.animals: List[AnimalSpec] = []
if "script_text" not in st.session_state:
    st.session_state.script_text = ""
if "scenes_json" not in st.session_state:
    st.session_state.scenes_json: List[SceneJSON] = []

# Inputs
st.subheader("Step 0 – Input TITLE")
title = st.text_input("Video Title (animal rescue / dramatic) *", placeholder="The Giant Frog That Swallowed a Village")

colA, colB = st.columns(2)
with colA:
    if st.button("Step 2 – Auto-generate Characters/Animals", type="primary"):
        client = _ensure_client()
        if client and title:
            prompt = build_characters_prompt(title)
            text = llm_complete(client, model, SYSTEM_ROLE, prompt, temperature=temperature, seed=(seed or None), max_tokens=max_tokens)
            # Expect 2 JSON arrays; try to parse heuristically
            try:
                data = json.loads(text)
                chars = [CharacterSpec(**c) for c in data.get("characters", [])]
                anims = [AnimalSpec(**a) for a in data.get("animals", [])]
                st.session_state.characters = chars
                st.session_state.animals = anims
                st.success("Generated character & animal specs.")
            except Exception:
                # fallback: try to find JSON blocks
                st.warning("Cannot parse JSON directly; attempting heuristic extraction.")
                # naive extraction
                start_c = text.find("[")
                end_c = text.rfind("]")
                if start_c != -1 and end_c != -1 and end_c > start_c:
                    try:
                        arr = json.loads(text[start_c:end_c+1])
                        # assume characters only; animals empty
                        st.session_state.characters = [CharacterSpec(**c) for c in arr]
                        st.session_state.animals = []
                        st.info("Parsed a single array as characters; please review.")
                    except Exception as e:
                        st.error(f"JSON parse failed: {e}")
        else:
            st.error("Please provide a TITLE and set OPENAI_API_KEY.")

with colB:
    if st.button("Step 1 – Generate Script (N cinematic scenes)"):
        client = _ensure_client()
        if client and title:
            allocation = _allocate_scenes(total_scenes)
            prompt = build_script_prompt(title, total_scenes, allocation)
            text = llm_complete(client, model, SYSTEM_ROLE, prompt, temperature=temperature, seed=(seed or None), max_tokens=max_tokens)
            st.session_state.script_text = text
            st.success("Script generated.")
        else:
            st.error("Please provide a TITLE and set OPENAI_API_KEY.")

# Editors for Step 2 (allow manual edits)
st.markdown("---")
st.subheader("Step 2 – Character & Animal Builder (editable)")

# Editable grid for characters
if st.session_state.characters:
    df_chars = pd.DataFrame([c.dict() for c in st.session_state.characters])
    edited_chars = st.data_editor(df_chars, num_rows="dynamic", use_container_width=True)
    st.session_state.characters = [CharacterSpec(**row) for _, row in edited_chars.iterrows()]
else:
    st.info("No characters yet. Use auto-generate or add manually below.")
    if st.checkbox("Add a blank human character"):
        st.session_state.characters.append(CharacterSpec(
            name="", origin="", age="", gender_role="", body_shape="", skin="", face="", eyes="", eyebrows="",
            nose="", mouth="", jawline="", hair="", top="", bottom="", accessories="", outfit_style="",
            palette="", personality="", base_expression="", body_language="", backdrop_env="", extra_expressions="",
            voice_tone=""
        ))

# Editable grid for animals
if st.session_state.animals:
    df_animals = pd.DataFrame([a.dict() for a in st.session_state.animals])
    edited_animals = st.data_editor(df_animals, num_rows="dynamic", use_container_width=True)
    st.session_state.animals = [AnimalSpec(**row) for _, row in edited_animals.iterrows()]
else:
    st.info("No animals yet. Use auto-generate or add manually below.")
    if st.checkbox("Add a blank animal"):
        st.session_state.animals.append(AnimalSpec(
            name="", species="", life_stage="", size_shape="", color_markings="", standout_features="",
            eyes="", ears="", snout="", mouth="", tail="", limbs="", accessories_marks="", default_expression="",
            extra_expressions="", personality="", signature_motion="", habitat="", relationship=""
        ))

# Script viewer/editor
st.markdown("---")
st.subheader("Step 1 – Script (editable)")
st.session_state.script_text = st.text_area("Cinematic Script Output", value=st.session_state.script_text, height=260)

# Generate Scene JSONs
st.markdown("---")
st.subheader("Step 3 – Generate Per-Scene Cinematic JSON Prompts")

if st.button("Build Scene JSONs", type="primary"):
    if not st.session_state.script_text.strip():
        st.error("Script is empty. Generate the script first.")
    else:
        allocation = _allocate_scenes(total_scenes)
        # Build a list mapping scene index to phase
        phases_flat: List[Dict[str, Any]] = []
        for p in allocation:
            phases_flat.extend([p] * p["scenes"])

        # If user wants LLM-enhanced paragraph per scene, we can call LLM here.
        # Otherwise, we fallback to using the script split heuristics.
        client = _ensure_client()
        scenes_out: List[SceneJSON] = []

        # Heuristic: try to split by lines like "SCENE 1".. or fallback to evenly split paragraphs.
        lines = [ln.strip() for ln in st.session_state.script_text.splitlines() if ln.strip()]
        scene_paras: Dict[int, str] = {}
        cur_scene = 0
        buf: List[str] = []
        def flush():
            nonlocal buf, cur_scene
            if buf:
                scene_paras[cur_scene] = " ".join(buf).strip()
                buf = []

        for ln in lines:
            if ln.upper().startswith("SCENE "):
                # new scene marker
                try:
                    num = int(ln.split()[1].strip(".:"))
                    # flush current
                    flush()
                    cur_scene = num
                except Exception:
                    buf.append(ln)
            else:
                buf.append(ln)
        flush()

        # Build prompts
        characters = st.session_state.characters
        animals = st.session_state.animals

        for i in range(1, total_scenes + 1):
            phase = phases_flat[i - 1] if i - 1 < len(phases_flat) else allocation[-1]
            # If we have LLM: rewrite paragraph to 15-layer style
            if client is not None and model:
                prompt = build_scene_prompt(title, i, phase, characters, animals, target_len=target_char_len)
                try:
                    para = llm_complete(client, model, SYSTEM_ROLE, prompt, temperature=temperature, seed=(seed or None), max_tokens=max_tokens)
                except Exception as e:
                    para = scene_paras.get(i, f"Placeholder cinematic paragraph for scene {i}.") + f" [LLM error: {e}]"
            else:
                para = scene_paras.get(i, f"Placeholder cinematic paragraph for scene {i}.")

            scene = SceneJSON(
                scene_number=i,
                phase_key=phase["key"],
                phase_name=phase["name"],
                objective=f"{phase['name']} for title '{title}'",
                core_emotion=phase["emotion"],
                duration_sec=8,
                title=f"{title} – Scene {i}",
                cinematic_prompt=para,
                continuity_notes="Ensure seamless emotional bridge into next scene; maintain photorealistic tone.",
            )
            scenes_out.append(scene)

        st.session_state.scenes_json = scenes_out
        st.success(f"Generated {len(scenes_out)} scene JSON prompts.")

# Display / Export
if st.session_state.scenes_json:
    st.markdown("---")
    st.subheader("Review Scenes")
    df = pd.DataFrame([s.dict() for s in st.session_state.scenes_json])
    st.dataframe(df, use_container_width=True, height=420)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download scenes.json",
            data=json.dumps([s.dict() for s in st.session_state.scenes_json], ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="scenes.json",
            mime="application/json",
        )
    with col2:
        st.download_button(
            "Download scenes.csv",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="scenes.csv",
            mime="text/csv",
        )

# Footer
st.markdown(
    """
---
**Guidance**
- Bước tạo nhân vật (Step 2) là quan trọng để tái sử dụng thông tin ngoại hình đồng nhất cho mọi cảnh.
- Có thể điều chỉnh `Total Scenes (N)` để ứng với 24/36/45/60 cảnh; thuật toán sẽ phân bổ theo tỷ lệ gốc.
- `Min chars per scene` cho phép kiểm soát độ chi tiết; tăng số này nếu muốn prompt dài theo chuẩn 15-layer.
- Để tối ưu chi phí: giảm `max_tokens`, dùng model rẻ hơn (ví dụ `gpt-4.1-mini`).
- Sau khi xuất JSON, có thể đưa trực tiếp vào pipeline video GenAI hoặc trình biên tập.
"""
)
