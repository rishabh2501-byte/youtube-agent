# AI YouTube Agent - Fully Automated Faceless YouTube Channel

A production-ready, fully automated system that creates and uploads YouTube videos daily without manual intervention.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI YouTube Agent                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Trending   │───▶│    Topic     │───▶│   Script     │                   │
│  │   Fetcher    │    │   Selector   │    │  Generator   │                   │
│  │ (pytrends)   │    │   (LLM)      │    │  (Claude)    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                                       │                            │
│         ▼                                       ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Stock      │───▶│    Video     │◀───│    TTS       │                   │
│  │   Footage    │    │   Generator  │    │   Engine     │                   │
│  │  (Pexels)    │    │   (FFmpeg)   │    │ (ElevenLabs) │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Thumbnail   │    │   Subtitle   │    │     SEO      │                   │
│  │  Generator   │    │   Generator  │    │   Metadata   │                   │
│  │  (DALL-E)    │    │   (Whisper)  │    │   Generator  │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         └───────────────────┼───────────────────┘                            │
│                             ▼                                                │
│                    ┌──────────────┐                                          │
│                    │   YouTube    │                                          │
│                    │   Uploader   │                                          │
│                    │  (Data API)  │                                          │
│                    └──────────────┘                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Trending Topics**: Fetches daily trending topics from Google Trends
- **Smart Topic Selection**: Uses LLM to select the most engaging topic
- **Script Generation**: Creates 45-60 second engaging scripts
- **AI Voice Narration**: Converts scripts to natural speech using ElevenLabs/OpenAI TTS
- **Stock Footage**: Automatically fetches relevant videos from Pexels
- **Video Production**: Combines footage, audio, and subtitles using FFmpeg
- **Thumbnail Generation**: Creates eye-catching thumbnails with DALL-E
- **SEO Optimization**: Generates optimized titles, descriptions, and tags
- **Auto Upload**: Uploads directly to YouTube with scheduling support
- **Daily Automation**: Runs automatically via cron scheduler

## Project Structure

```
youtube_agent/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── modules/
│   ├── __init__.py
│   ├── trending_fetcher.py
│   ├── topic_selector.py
│   ├── script_generator.py
│   ├── tts_engine.py
│   ├── stock_footage.py
│   ├── video_generator.py
│   ├── subtitle_generator.py
│   ├── thumbnail_generator.py
│   ├── seo_generator.py
│   └── youtube_uploader.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── helpers.py
├── prompts/
│   ├── script_prompt.txt
│   ├── topic_selection_prompt.txt
│   └── seo_prompt.txt
├── output/
│   ├── videos/
│   ├── audio/
│   ├── thumbnails/
│   └── subtitles/
├── credentials/
│   └── .gitkeep
├── main.py
└── scheduler.py
```

## Prerequisites

- Python 3.9+
- FFmpeg installed on system
- API Keys for:
  - OpenAI or Anthropic (Claude)
  - ElevenLabs (for TTS)
  - Pexels (for stock footage)
  - YouTube Data API v3

## Installation

### 1. Clone and Setup

```bash
cd youtube_agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Setup YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Download the JSON file and save as `credentials/client_secrets.json`

## Environment Variables

```env
# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Text-to-Speech
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_preferred_voice_id

# Stock Footage
PEXELS_API_KEY=your_pexels_api_key

# YouTube
YOUTUBE_CLIENT_SECRETS_FILE=credentials/client_secrets.json

# Configuration
VIDEO_DURATION_SECONDS=60
TRENDING_REGION=US
OUTPUT_DIR=output
```

## Usage

### Run Once (Manual)

```bash
python main.py
```

### Run with Scheduler (Daily Automation)

```bash
python scheduler.py
```

### Setup Cron Job (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/youtube_agent && /path/to/venv/bin/python main.py >> /path/to/logs/youtube_agent.log 2>&1
```

## Module Documentation

### 1. Trending Fetcher
Fetches trending topics from Google Trends using pytrends library.

### 2. Topic Selector
Uses LLM to analyze trending topics and select the most engaging one for video content.

### 3. Script Generator
Generates a 45-60 second engaging script optimized for YouTube Shorts/videos.

### 4. TTS Engine
Converts script to natural-sounding speech using ElevenLabs or OpenAI TTS.

### 5. Stock Footage
Fetches relevant stock videos from Pexels API based on script keywords.

### 6. Video Generator
Uses FFmpeg to combine stock footage, audio narration, and subtitles.

### 7. Subtitle Generator
Generates SRT subtitles from the script with proper timing.

### 8. Thumbnail Generator
Creates eye-catching thumbnails using DALL-E or Stable Diffusion.

### 9. SEO Generator
Generates optimized title, description, and tags for YouTube.

### 10. YouTube Uploader
Uploads the final video to YouTube using the Data API v3.

## Example LLM Prompts

See the `prompts/` directory for all prompt templates used in the system.

## Troubleshooting

### FFmpeg not found
Ensure FFmpeg is installed and in your system PATH.

### YouTube API quota exceeded
The YouTube Data API has daily quotas. Consider using multiple projects or upgrading.

### Rate limiting
The system includes built-in delays to respect API rate limits.

## License

MIT License - Feel free to use and modify for your projects.

## Disclaimer

This tool is for educational purposes. Ensure you comply with:
- YouTube's Terms of Service
- API providers' usage policies
- Copyright laws for generated content
