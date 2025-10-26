import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="Viral Video Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🎬 Viral Video Script Generator</div>', unsafe_allow_html=True)
st.markdown("**Tạo kịch bản video viral Hollywood-style từ một tiêu đề đơn giản**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # API Key input
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Nhập API key của bạn hoặc cấu hình trong file .env"
    )
    
    if api_key_input:
        client = OpenAI(api_key=api_key_input)
    
    st.divider()
    
    # Number of scenes configuration
    num_scenes = st.selectbox(
        "Số lượng cảnh",
        options=[24, 36, 45, 60],
        index=2,
        help="Chọn số cảnh cho video (mỗi cảnh 8 giây)"
    )
    
    video_duration = (num_scenes * 8) / 60
    st.info(f"⏱️ Thời lượng video: {video_duration:.1f} phút")
    
    st.divider()
    
    # Model selection
    model = st.selectbox(
        "Mô hình OpenAI",
        options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0,
        help="Chọn mô hình AI để tạo nội dung"
    )
    
    st.divider()
    
    st.markdown("### 📋 Quy trình")
    st.markdown("""
    1. **Nhập tiêu đề** video
    2. **Tạo kịch bản** viral (Step 1)
    3. **Xây dựng nhân vật** (Step 2)
    4. **Tạo prompts** cho từng cảnh (Step 3)
    5. **Xuất kết quả** dưới dạng JSON
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📝 Nhập Tiêu Đề", "🎭 Kịch Bản & Nhân Vật", "🎬 Scene Prompts", "💾 Xuất Kết Quả"])

# Initialize session state
if 'title' not in st.session_state:
    st.session_state.title = ""
if 'script' not in st.session_state:
    st.session_state.script = None
if 'characters' not in st.session_state:
    st.session_state.characters = None
if 'scene_prompts' not in st.session_state:
    st.session_state.scene_prompts = []

# Tab 1: Input Title
with tab1:
    st.markdown('<div class="step-header">📝 Bước 1: Nhập Tiêu Đề Video</div>', unsafe_allow_html=True)
    
    title_input = st.text_input(
        "Nhập tiêu đề video của bạn:",
        placeholder="Ví dụ: The Giant Frog That Swallowed a Village",
        help="Tiêu đề nên ngắn gọn, hấp dẫn và có yếu tố kịch tính"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 Bắt đầu tạo kịch bản", type="primary", use_container_width=True):
            if not title_input:
                st.error("❌ Vui lòng nhập tiêu đề video!")
            elif not api_key_input:
                st.error("❌ Vui lòng nhập OpenAI API Key!")
            else:
                st.session_state.title = title_input
                st.success(f"✅ Đã lưu tiêu đề: {title_input}")
                st.info("👉 Chuyển sang tab **Kịch Bản & Nhân Vật** để tiếp tục")
    
    if st.session_state.title:
        st.markdown("---")
        st.markdown(f"**Tiêu đề hiện tại:** {st.session_state.title}")

# Tab 2: Script and Characters
with tab2:
    st.markdown('<div class="step-header">🎭 Bước 2: Tạo Kịch Bản và Nhân Vật</div>', unsafe_allow_html=True)
    
    if not st.session_state.title:
        st.warning("⚠️ Vui lòng nhập tiêu đề ở tab đầu tiên!")
    else:
        st.markdown(f"**Đang làm việc với tiêu đề:** {st.session_state.title}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📜 Tạo Kịch Bản (Step 1)", use_container_width=True):
                with st.spinner(f"Đang tạo kịch bản {num_scenes} cảnh..."):
                    try:
                        script_prompt = f"""You are a viral video scriptwriter specializing in dramatic, suspenseful storytelling (một nhà làm phim hàng đầu Hollywood về điện ảnh).

Title: {st.session_state.title}

Create a cinematic script for a {video_duration:.1f}-minute short film, divided into {num_scenes} cinematic scenes (each 8 seconds long).

STRUCTURE:
- Cold Open – Chaos: {int(num_scenes * 0.11)} scenes
- Flashback – Origin: {int(num_scenes * 0.11)} scenes  
- First Attack: {int(num_scenes * 0.18)} scenes
- Rescue Team Formation: {int(num_scenes * 0.18)} scenes
- Chaos Escalates: {int(num_scenes * 0.22)} scenes
- Final Rescue: {int(num_scenes * 0.09)} scenes
- Ending & Reflection: {int(num_scenes * 0.11)} scenes

For each scene, write one continuous cinematic paragraph (not a list) that combines:
- Realistic action and emotional rhythm
- Detailed visual descriptions
- Character emotions and interactions
- Environmental details
- Moral undertones about humanity and nature

VISUAL TONE: Photorealistic 4K, IMAX-level detail
CAMERA: Cinematic realism with sweeping aerials, close-ups, dynamic POV transitions
LIGHTING: Dramatic contrast (teal/orange), volumetric atmosphere
SOUND: Layered ambience, evolving music from ominous to heroic to soft
EMOTION FLOW: Fear → Curiosity → Resolve → Chaos → Sacrifice → Redemption → Compassion

Write the complete script now with all {num_scenes} scenes."""

                        response = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": script_prompt}],
                            temperature=0.8,
                            max_tokens=4000
                        )
                        
                        st.session_state.script = response.choices[0].message.content
                        st.success("✅ Kịch bản đã được tạo thành công!")
                        
                    except Exception as e:
                        st.error(f"❌ Lỗi khi tạo kịch bản: {str(e)}")
        
        with col2:
            if st.button("👥 Tạo Nhân Vật (Step 2)", use_container_width=True):
                if not st.session_state.script:
                    st.error("❌ Vui lòng tạo kịch bản trước!")
                else:
                    with st.spinner("Đang xây dựng nhân vật..."):
                        try:
                            character_prompt = f"""Based on this script:

{st.session_state.script}

Create detailed character profiles for ALL characters (humans and animals) that appear in the story.

For HUMANS, include:
- Tên nhân vật (English name)
- Nguồn gốc / Quốc tịch / Văn hóa
- Độ tuổi (specific age)
- Giới tính / Vai trò
- Thể hình: chiều cao, cân nặng, tỷ lệ
- Da & Màu da (skin tone description)
- Khuôn mặt: hình dạng, nếp nhăn, mắt, lông mày, mũi, miệng, cằm
- Tóc: màu, độ dài, kiểu
- Trang phục: áo, quần, màu sắc, phong cách
- Phụ kiện: kính, mũ, khăn, đồng hồ, etc.
- Tính cách
- Biểu cảm và ngôn ngữ cơ thể
- Tông giọng

For ANIMALS, include:
- Tên nhân vật
- Loài / Giống
- Tuổi / Giai đoạn phát triển
- Kích thước: chiều cao, cân nặng, tỷ lệ
- Màu lông/da/vảy: màu chính + hoa văn
- Đặc điểm cơ thể: mắt, tai, mũi, miệng, đuôi, chân
- Phụ kiện / dấu hiệu đặc trưng
- Biểu cảm và tính cách
- Cử động đặc trưng
- Môi trường gắn liền

Return the character profiles in a structured JSON format."""

                            response = client.chat.completions.create(
                                model=model,
                                messages=[{"role": "user", "content": character_prompt}],
                                temperature=0.7,
                                max_tokens=3000
                            )
                            
                            st.session_state.characters = response.choices[0].message.content
                            st.success("✅ Nhân vật đã được tạo thành công!")
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi khi tạo nhân vật: {str(e)}")
        
        # Display results
        if st.session_state.script:
            st.markdown("---")
            st.markdown("### 📜 Kịch Bản")
            with st.expander("Xem kịch bản đầy đủ", expanded=False):
                st.markdown(st.session_state.script)
        
        if st.session_state.characters:
            st.markdown("---")
            st.markdown("### 👥 Nhân Vật")
            with st.expander("Xem thông tin nhân vật", expanded=False):
                st.markdown(st.session_state.characters)

# Tab 3: Scene Prompts
with tab3:
    st.markdown('<div class="step-header">🎬 Bước 3: Tạo Prompts Cho Từng Cảnh</div>', unsafe_allow_html=True)
    
    if not st.session_state.script or not st.session_state.characters:
        st.warning("⚠️ Vui lòng hoàn thành Step 1 và Step 2 trước!")
    else:
        st.markdown(f"**Tạo {num_scenes} prompts chi tiết cho video**")
        
        if st.button("🎥 Tạo Scene Prompts (Step 3)", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            st.session_state.scene_prompts = []
            
            for i in range(num_scenes):
                status_text.text(f"Đang tạo prompt cho cảnh {i+1}/{num_scenes}...")
                progress_bar.progress((i + 1) / num_scenes)
                
                try:
                    scene_prompt = f"""Create a detailed cinematic video prompt for Scene {i+1} of {num_scenes}.

SCRIPT CONTEXT:
{st.session_state.script}

CHARACTER PROFILES:
{st.session_state.characters}

Generate ONE continuous cinematic paragraph (minimum 2000 characters) for scene {i+1}, following the 15-layer structure:

1. Scene Objective & Core Message
2. Environment & Time of Day (chi tiết thời tiết, ánh sáng, thiên nhiên)
3. Characters & Appearance (use full details from character profiles above)
4. Emotions & Expressions (eyes, breathing, body language)
5. Props & Rescue Tools
6. Dialogue & Callouts (short, action-tied)
7. Actions & Teamwork
8. Camera & Composition (shot type, angles, motion)
9. Lighting & Color Grading (teal/orange, volumetric, moody)
10. VFX & Particles (mud, water, dust, light rays)
11. Audio & Music (soundtrack rhythm, sound effects)
12. Rhythm & Beatmap (music hits aligned with action)
13. No On-Screen Text
14. Scene Transitions (fade, cut, drone sweep)
15. Moral & Emotional Undercurrent

OUTPUT FORMAT: Return as valid JSON with this structure:
{{
    "scene_number": {i+1},
    "duration_seconds": 8,
    "prompt": "your detailed 2000+ character cinematic description here",
    "technical_specs": {{
        "resolution": "4K",
        "style": "photorealistic IMAX",
        "camera_movement": "description",
        "lighting": "description",
        "color_grade": "description"
    }}
}}

Write the prompt as one flowing cinematic paragraph, not bullet points."""

                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": scene_prompt}],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # Try to parse JSON, if fails, create structured response
                    content = response.choices[0].message.content
                    try:
                        # Extract JSON if wrapped in markdown
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                        
                        scene_data = json.loads(content)
                    except:
                        # If JSON parsing fails, create structured data
                        scene_data = {
                            "scene_number": i + 1,
                            "duration_seconds": 8,
                            "prompt": content,
                            "technical_specs": {
                                "resolution": "4K",
                                "style": "photorealistic IMAX"
                            }
                        }
                    
                    st.session_state.scene_prompts.append(scene_data)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi tại cảnh {i+1}: {str(e)}")
                    continue
            
            status_text.text("✅ Hoàn thành!")
            st.success(f"🎉 Đã tạo thành công {len(st.session_state.scene_prompts)} scene prompts!")
        
        # Display scene prompts
        if st.session_state.scene_prompts:
            st.markdown("---")
            st.markdown(f"### 📋 Danh Sách {len(st.session_state.scene_prompts)} Cảnh")
            
            for idx, scene in enumerate(st.session_state.scene_prompts):
                with st.expander(f"🎬 Cảnh {scene.get('scene_number', idx+1)} ({scene.get('duration_seconds', 8)}s)"):
                    st.markdown(f"**Prompt:**\n\n{scene.get('prompt', 'N/A')}")
                    
                    if 'technical_specs' in scene:
                        st.markdown("**Technical Specs:**")
                        st.json(scene['technical_specs'])

# Tab 4: Export Results
with tab4:
    st.markdown('<div class="step-header">💾 Bước 4: Xuất Kết Quả</div>', unsafe_allow_html=True)
    
    if not st.session_state.scene_prompts:
        st.warning("⚠️ Chưa có dữ liệu để xuất. Vui lòng hoàn thành các bước trước!")
    else:
        st.success(f"✅ Sẵn sàng xuất {len(st.session_state.scene_prompts)} scene prompts")
        
        # Create complete JSON export
        export_data = {
            "project_info": {
                "title": st.session_state.title,
                "total_scenes": num_scenes,
                "duration_minutes": video_duration,
                "created_with": "Viral Video Script Generator"
            },
            "script": st.session_state.script,
            "characters": st.session_state.characters,
            "scenes": st.session_state.scene_prompts
        }
        
        json_output = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Tải xuống JSON",
                data=json_output,
                file_name=f"viral_video_{st.session_state.title.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                label="📄 Tải xuống Script (TXT)",
                data=st.session_state.script,
                file_name=f"script_{st.session_state.title.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Preview
        st.markdown("---")
        st.markdown("### 👀 Xem Trước JSON")
        with st.expander("Xem cấu trúc JSON đầy đủ"):
            st.json(export_data)
        
        # Statistics
        st.markdown("---")
        st.markdown("### 📊 Thống Kê")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tổng số cảnh", len(st.session_state.scene_prompts))
        
        with col2:
            st.metric("Thời lượng", f"{video_duration:.1f} phút")
        
        with col3:
            total_chars = sum(len(scene.get('prompt', '')) for scene in st.session_state.scene_prompts)
            st.metric("Tổng ký tự", f"{total_chars:,}")
        
        with col4:
            avg_chars = total_chars // len(st.session_state.scene_prompts) if st.session_state.scene_prompts else 0
            st.metric("TB/cảnh", f"{avg_chars:,} ký tự")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🎬 Viral Video Script Generator | Powered by OpenAI & Streamlit</p>
    <p>Tạo kịch bản video Hollywood-style chỉ trong vài phút</p>
</div>
""", unsafe_allow_html=True)
