"""
YouTube Agent - Web UI
Simple Streamlit interface to generate and upload videos.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import YouTubeAgent
from locations_data import get_random_topic, LOCATIONS

# Page config
st.set_page_config(
    page_title="AI YouTube Agent",
    page_icon="🎬",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #FF0000;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF0000;
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #CC0000;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🎬 AI YouTube Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Enter a topic and generate a video automatically!</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    upload_to_youtube = st.checkbox("Upload to YouTube", value=True)
    
    st.divider()
    
    st.header("📍 Quick Topics")
    if st.button("🎲 Random Topic"):
        st.session_state.topic = get_random_topic()
    
    st.divider()
    
    st.header("📊 Categories")
    category = st.selectbox(
        "Select category:",
        ["countries", "cities", "states_regions", "landmarks"]
    )
    
    if category:
        location = st.selectbox(
            "Select location:",
            LOCATIONS.get(category, [])
        )
        if st.button(f"Use: {location}"):
            st.session_state.topic = f"Amazing Facts About {location}"

# Main content
st.header("📝 Enter Your Topic")

# Topic input
topic = st.text_input(
    "Topic:",
    value=st.session_state.get("topic", ""),
    placeholder="e.g., Amazing Facts About Japan"
)

# Generate button
col1, col2 = st.columns([3, 1])

with col1:
    generate_btn = st.button("🚀 Generate Video", type="primary", use_container_width=True)

with col2:
    test_btn = st.button("🧪 Test (No Upload)", use_container_width=True)

# Process
if generate_btn or test_btn:
    if not topic:
        st.error("❌ Please enter a topic!")
    else:
        upload = upload_to_youtube and not test_btn
        
        st.info(f"🎬 Creating video for: **{topic}**")
        st.info(f"📤 Upload to YouTube: **{'Yes' if upload else 'No (Test Mode)'}**")
        
        # Progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Initializing agent...")
            progress_bar.progress(10)
            
            agent = YouTubeAgent()
            
            status_text.text("Generating script...")
            progress_bar.progress(20)
            
            # Run the pipeline
            with st.spinner("🎥 Generating video... This may take 1-2 minutes"):
                result = agent.create_video_from_topic(topic, upload=upload)
            
            progress_bar.progress(100)
            
            if result:
                st.success("✅ Video created successfully!")
                
                # Results
                st.header("📊 Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Topic", result.get("topic", topic))
                    st.metric("Title", result.get("title", "N/A"))
                    st.metric("Duration", f"{result.get('duration_seconds', 0):.1f}s")
                
                with col2:
                    st.metric("Processing Time", f"{result.get('processing_time_seconds', 0):.1f}s")
                    if result.get("video_id"):
                        st.metric("Video ID", result.get("video_id"))
                
                # YouTube link
                if result.get("video_url"):
                    st.header("🔗 YouTube Link")
                    st.markdown(f"**[{result.get('video_url')}]({result.get('video_url')})**")
                    st.balloons()
                
                # Video preview
                video_path = result.get("video_path")
                if video_path and Path(video_path).exists():
                    st.header("🎥 Video Preview")
                    st.video(video_path)
                
            else:
                st.error("❌ Video generation failed. Check logs for details.")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            progress_bar.progress(0)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    Made with ❤️ using Groq AI, Pexels, and gTTS
</div>
""", unsafe_allow_html=True)
