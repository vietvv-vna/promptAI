import streamlit as st
import json
import os
import google.generativeai as genai

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional for Streamlit Cloud

# Initialize Gemini
def configure_gemini(api_key):
    """Configure Gemini API"""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Lỗi khi cấu hình Gemini: {str(e)}")
        return False

# Get API key from multiple sources
def get_api_key():
    """Get API key from multiple sources"""
    # Try environment variable
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    
    # Try Streamlit secrets
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except:
        pass
    
    return None

# Page configuration
st.set_page_config(
    page_title="Viral Video Script Generator - Powered by Google Gemini",
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
    .free-badge {
        background: linear-gradient(90deg, #4285F4, #34A853);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 1rem 0;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🎬 Viral Video Script Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="free-badge">💯 100% MIỄN PHÍ - Powered by Google Gemini</div>', unsafe_allow_html=True)
st.markdown("**Tạo kịch bản video viral Hollywood-style từ một tiêu đề đơn giản**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # Get default API key
    default_key = get_api_key() or ""
    
    # API Key input
    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=default_key,
        help="Nhập API key Gemini (MIỄN PHÍ). Lấy tại: https://aistudio.google.com/app/apikey"
    )
    
    if not api_key_input:
        st.warning("⚠️ Cần API key Gemini để sử dụng")
        st.success("✨ **Gemini hoàn toàn MIỄN PHÍ!**")
        st.markdown("🔑 [Lấy API key FREE](https://aistudio.google.com/app/apikey)")
    else:
        if configure_gemini(api_key_input):
            st.success("✅ Gemini đã sẵn sàng!")
    
    st.divider()
    
    # Model selection
    model = st.selectbox(
        "Chọn Model Gemini",
        options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b"],
        index=0,
        help="Flash: Nhanh nhất | Pro: Chất lượng cao nhất | Flash-8b: Siêu nhanh"
    )
    
    if "flash-8b" in model:
        st.info("⚡⚡ Flash-8B: Siêu nhanh, nhẹ")
    elif "flash" in model:
        st.info("⚡ Flash: Nhanh, cân bằng tốt")
    else:
        st.info("⭐ Pro: Chất lượng cao nhất")
    
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
    
    st.markdown("### 💰 Chi phí")
    st.success("🎉 **HOÀN TOÀN MIỄN PHÍ!**")
    st.markdown("""
    - ✅ Unlimited videos
    - ✅ Không cần thẻ tín dụng
    - ✅ Chất lượng cao
    - ✅ 1500 requests/ngày
    - ✅ 1 triệu tokens/ngày
    """)

# Initialize session state
if 'title' not in st.session_state:
    st.session_state.title = ""
if 'script' not in st.session_state:
    st.session_state.script = None
if 'characters' not in st.session_state:
    st.session_state.characters = None
if 'scene_prompts' not in st.session_state:
    st.session_state.scene_prompts = []

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📝 Nhập Tiêu Đề", "🎭 Kịch Bản & Nhân Vật", "🎬 Scene Prompts", "💾 Xuất Kết Quả"])

# Tab 1: Input Title
with tab1:
    st.markdown('<div class="step-header">📝 Bước 1: Nhập Tiêu Đề Video</div>', unsafe_allow_html=True)
    
    st.success("🎉 Bạn đang dùng Google Gemini - Hoàn toàn MIỄN PHÍ!")
    
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
                st.error("❌ Vui lòng nhập Gemini API Key!")
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
        st.success("💚 Sử dụng Google Gemini - Hoàn toàn MIỄN PHÍ!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📜 Tạo Kịch Bản (Step 1)", use_container_width=True):
                if not api_key_input:
                    st.error("❌ Vui lòng nhập Gemini API Key!")
                else:
                    with st.spinner(f"Đang tạo kịch bản {num_scenes} cảnh..."):
                        try:
                            script_prompt = f"""You are a viral video scriptwriter specializing in dramatic, suspenseful storytelling.

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

Write the complete script with all {num_scenes} scenes in cinematic paragraphs."""

                            model_obj = genai.GenerativeModel(model)
                            response = model_obj.generate_content(script_prompt)
                            
                            st.session_state.script = response.text
                            st.success("✅ Kịch bản đã được tạo thành công bằng Google Gemini!")
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi: {str(e)}")
                            st.info("💡 Kiểm tra API key tại: https://aistudio.google.com/app/apikey")
        
        with col2:
            if st.button("👥 Tạo Nhân Vật (Step 2)", use_container_width=True):
                if not api_key_input:
                    st.error("❌ Vui lòng nhập Gemini API Key!")
                elif not st.session_state.script:
                    st.error("❌ Vui lòng tạo kịch bản trước!")
                else:
                    with st.spinner("Đang xây dựng nhân vật..."):
                        try:
                            character_prompt = f"""Based on this script, create detailed character profiles for ALL characters (humans and animals).

{st.session_state.script}

For HUMANS: name, age, appearance, clothing, personality, expressions
For ANIMALS: species, size, colors, features, personality, movements

Return as structured text."""

                            model_obj = genai.GenerativeModel(model)
                            response = model_obj.generate_content(character_prompt)
                            
                            st.session_state.characters = response.text
                            st.success("✅ Nhân vật đã được tạo thành công!")
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi: {str(e)}")
        
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
        st.success("💚 100% MIỄN PHÍ với Google Gemini!")
        
        if st.button("🎥 Tạo Scene Prompts (Step 3)", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("❌ Vui lòng nhập Gemini API Key!")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                st.session_state.scene_prompts = []
                
                for i in range(num_scenes):
                    status_text.text(f"Đang tạo prompt cho cảnh {i+1}/{num_scenes}...")
                    progress_bar.progress((i + 1) / num_scenes)
                    
                    try:
                        scene_prompt = f"""Create a detailed cinematic video prompt for Scene {i+1} of {num_scenes}.

CONTEXT:
{st.session_state.script}

CHARACTERS:
{st.session_state.characters}

Generate ONE cinematic paragraph (2000+ characters) for scene {i+1} with: objective, environment, characters, emotions, props, dialogue, actions, camera, lighting, VFX, audio, transitions, and moral undercurrent.

Return as JSON: {{"scene_number": {i+1}, "duration_seconds": 8, "prompt": "your detailed prompt here"}}"""

                        model_obj = genai.GenerativeModel(model)
                        response = model_obj.generate_content(scene_prompt)
                        result = response.text
                        
                        # Try to parse JSON
                        try:
                            if "```json" in result:
                                result = result.split("```json")[1].split("```")[0].strip()
                            elif "```" in result:
                                result = result.split("```")[1].split("```")[0].strip()
                            
                            scene_data = json.loads(result)
                        except:
                            scene_data = {
                                "scene_number": i + 1,
                                "duration_seconds": 8,
                                "prompt": result
                            }
                        
                        st.session_state.scene_prompts.append(scene_data)
                        
                    except Exception as e:
                        st.error(f"❌ Lỗi tại cảnh {i+1}: {str(e)}")
                        continue
                
                status_text.text("✅ Hoàn thành!")
                st.success(f"🎉 Đã tạo thành công {len(st.session_state.scene_prompts)} scene prompts bằng Gemini!")
        
        # Display scene prompts
        if st.session_state.scene_prompts:
            st.markdown("---")
            st.markdown(f"### 📋 Danh Sách {len(st.session_state.scene_prompts)} Cảnh")
            
            for idx, scene in enumerate(st.session_state.scene_prompts):
                with st.expander(f"🎬 Cảnh {scene.get('scene_number', idx+1)} ({scene.get('duration_seconds', 8)}s)"):
                    st.markdown(f"**Prompt:**\n\n{scene.get('prompt', 'N/A')}")

# Tab 4: Export Results
with tab4:
    st.markdown('<div class="step-header">💾 Bước 4: Xuất Kết Quả</div>', unsafe_allow_html=True)
    
    if not st.session_state.scene_prompts:
        st.warning("⚠️ Chưa có dữ liệu để xuất. Vui lòng hoàn thành các bước trước!")
    else:
        st.success(f"✅ Sẵn sàng xuất {len(st.session_state.scene_prompts)} scene prompts")
        st.balloons()
        st.success("🎉 Bạn vừa tạo video script hoàn toàn MIỄN PHÍ với Google Gemini!")
        
        # Create complete JSON export
        export_data = {
            "project_info": {
                "title": st.session_state.title,
                "total_scenes": num_scenes,
                "duration_minutes": video_duration,
                "ai_provider": "Google Gemini",
                "model": model,
                "created_with": "Viral Video Script Generator - Gemini Edition"
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
            st.metric("Chi phí", "FREE! 🎉")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🎬 Viral Video Script Generator - Gemini Edition</p>
    <p>Powered by <strong>Google Gemini</strong> | 100% Miễn phí Forever</p>
</div>
""", unsafe_allow_html=True)
