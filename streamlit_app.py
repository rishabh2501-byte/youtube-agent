"""
YouTube Agent - Cloud Web UI
Streamlit Cloud compatible version (video generation only, no YouTube upload).
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile
import base64

# Page config
st.set_page_config(
    page_title="AI YouTube Video Generator",
    page_icon="🎬",
    layout="centered"
)

# Check for required API keys
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
PEXELS_API_KEY = st.secrets.get("PEXELS_API_KEY", os.environ.get("PEXELS_API_KEY", ""))

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not found in secrets!")
    st.info("Add GROQ_API_KEY in Streamlit Cloud secrets or environment variables.")
    st.stop()

# Set environment variables
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["PEXELS_API_KEY"] = PEXELS_API_KEY
os.environ["LLM_PROVIDER"] = "groq"
os.environ["TTS_PROVIDER"] = "gtts"
os.environ["IMAGE_GENERATOR"] = "placeholder"

# Now import after env vars are set
from main import YouTubeAgent
from locations_data import get_random_topic, LOCATIONS

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF0000, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #FF0000, #CC0000);
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 10px;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #CC0000, #990000);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🎬 AI Video Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Generate YouTube-ready videos with AI!</p>', unsafe_allow_html=True)

# Initialize session state
if "topic" not in st.session_state:
    st.session_state.topic = ""

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.info("💡 Videos are generated but NOT uploaded to YouTube. Download and upload manually.")
    
    st.divider()
    
    st.header("🎲 Quick Topics")
    if st.button("Random Topic", use_container_width=True):
        st.session_state.topic = get_random_topic()
        st.rerun()
    
    st.divider()
    
    st.header("📍 Categories")
    category = st.selectbox(
        "Category:",
        ["countries", "cities", "states_regions", "landmarks"]
    )
    
    if category:
        location = st.selectbox(
            "Location:",
            LOCATIONS.get(category, [])
        )
        if st.button(f"Use: {location}", use_container_width=True):
            st.session_state.topic = f"Amazing Facts About {location}"
            st.rerun()

# Main content
st.header("📝 Enter Your Topic")

topic = st.text_input(
    "Topic:",
    value=st.session_state.topic,
    placeholder="e.g., Amazing Facts About Japan",
    key="topic_input"
)

# Update session state
if topic != st.session_state.topic:
    st.session_state.topic = topic

# Generate button
if st.button("🚀 Generate Video", type="primary", use_container_width=True):
    if not topic:
        st.error("❌ Please enter a topic!")
    else:
        st.info(f"🎬 Creating video for: **{topic}**")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔧 Initializing...")
            progress_bar.progress(10)
            
            agent = YouTubeAgent()
            
            status_text.text("📝 Generating script...")
            progress_bar.progress(20)
            
            with st.spinner("🎥 Generating video... This takes 1-2 minutes"):
                result = agent.create_video_from_topic(topic, upload=False)
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            if result:
                st.success("✅ Video created successfully!")
                
                # Results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("📌 Topic", result.get("topic", topic)[:30] + "...")
                    st.metric("⏱️ Duration", f"{result.get('duration_seconds', 0):.1f}s")
                
                with col2:
                    st.metric("📊 Title", result.get("title", "N/A")[:25] + "...")
                    st.metric("⚡ Process Time", f"{result.get('processing_time_seconds', 0):.1f}s")
                
                # Video preview & download
                video_path = result.get("video_path")
                if video_path and Path(video_path).exists():
                    st.header("🎥 Your Video")
                    st.video(video_path)
                    
                    # Download button
                    with open(video_path, "rb") as f:
                        video_bytes = f.read()
                    
                    st.download_button(
                        label="📥 Download Video",
                        data=video_bytes,
                        file_name=f"{topic.replace(' ', '_')[:30]}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    
                    st.balloons()
                
            else:
                st.error("❌ Video generation failed.")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            progress_bar.progress(0)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem;">
    Powered by Groq AI • Pexels • gTTS<br>
    <a href="https://github.com/rishabh2501-byte/youtube-agent" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
