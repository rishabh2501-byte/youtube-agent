# AI YouTube Agent - Complete Setup Guide

This guide walks you through setting up the AI YouTube Agent from scratch.

## Prerequisites

- **Python 3.9+** installed
- **FFmpeg** installed on your system
- **Git** (optional, for version control)

## Step 1: Install FFmpeg

### macOS
```bash
brew install ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

### Windows
1. Download from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your system PATH

Verify installation:
```bash
ffmpeg -version
```

## Step 2: Set Up Python Environment

```bash
# Navigate to project directory
cd youtube_agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Obtain API Keys

### 3.1 Anthropic API Key (for Claude)
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

### 3.2 OpenAI API Key (alternative/for DALL-E)
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

### 3.3 ElevenLabs API Key (for TTS)
1. Go to https://elevenlabs.io/
2. Sign up or log in
3. Click on your profile → Profile Settings
4. Copy your API key
5. Note a Voice ID you want to use (or use default)

### 3.4 Pexels API Key (for stock footage)
1. Go to https://www.pexels.com/api/
2. Sign up or log in
3. Click "Get Started" or go to your API dashboard
4. Copy your API key

### 3.5 YouTube Data API Setup

This is the most complex setup. Follow carefully:

#### Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Note your project name

#### Enable YouTube Data API
1. Go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

#### Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "YouTube Agent"
   - User support email: Your email
   - Developer contact: Your email
   - Add scopes: `youtube.upload`
   - Add test users: Your Gmail address
4. Back to Credentials → Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "YouTube Agent Desktop"
5. Click "Create"
6. Download the JSON file
7. Rename it to `client_secrets.json`
8. Move it to `youtube_agent/credentials/client_secrets.json`

## Step 4: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

Fill in your API keys:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
ELEVENLABS_API_KEY=xxxxx
PEXELS_API_KEY=xxxxx

# Optional (for DALL-E thumbnails)
OPENAI_API_KEY=sk-xxxxx

# ElevenLabs Voice ID (optional, has default)
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

## Step 5: First Run (Authentication)

The first run will open a browser for YouTube OAuth:

```bash
python main.py --no-upload
```

This will:
1. Test all modules
2. Open browser for YouTube authentication
3. Save the token for future use

When the browser opens:
1. Select your Google account
2. Click "Continue" on the warning (it's your own app)
3. Grant YouTube upload permissions
4. Close the browser when it says "Authentication successful"

## Step 6: Test Run

Run a complete test without uploading:

```bash
python main.py --no-upload --keep-files
```

This creates a video locally so you can verify everything works.

## Step 7: Production Run

### Single Run
```bash
python main.py
```

### With Custom Topic
```bash
python main.py --topic "Amazing Space Facts"
```

### Daily Scheduler
```bash
python scheduler.py --time 09:00 --timezone "America/New_York"
```

## Step 8: Set Up Cron Job (Linux/macOS)

For true automation, set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /full/path/to/youtube_agent && /full/path/to/venv/bin/python main.py >> /full/path/to/logs/cron.log 2>&1
```

Example with actual paths:
```bash
0 9 * * * cd /Users/yourname/youtube_agent && /Users/yourname/youtube_agent/venv/bin/python main.py >> /Users/yourname/youtube_agent/logs/cron.log 2>&1
```

## Troubleshooting

### "FFmpeg not found"
- Ensure FFmpeg is installed and in PATH
- Try running `ffmpeg -version` in terminal

### "API key invalid"
- Double-check the key in `.env`
- Ensure no extra spaces or quotes
- Verify the key is active in the provider's dashboard

### "YouTube quota exceeded"
- YouTube API has daily quotas (10,000 units)
- Video upload costs ~1,600 units
- Wait 24 hours or use a different project

### "OAuth token expired"
- Delete `credentials/youtube_token.json`
- Run again to re-authenticate

### "No trending topics found"
- Check internet connection
- Google Trends may be rate-limiting
- Try again in a few minutes

### "Stock footage download failed"
- Check Pexels API key
- Verify internet connection
- Check Pexels API status

## Directory Structure After Setup

```
youtube_agent/
├── .env                          # Your API keys (DO NOT COMMIT)
├── credentials/
│   ├── client_secrets.json       # YouTube OAuth (DO NOT COMMIT)
│   └── youtube_token.json        # Generated after auth (DO NOT COMMIT)
├── output/
│   ├── videos/                   # Generated videos
│   ├── audio/                    # Generated audio
│   ├── thumbnails/               # Generated thumbnails
│   ├── subtitles/                # Generated subtitles
│   └── footage/                  # Downloaded stock footage
└── logs/
    └── youtube_agent.log         # Application logs
```

## Security Notes

⚠️ **NEVER commit these files to version control:**
- `.env`
- `credentials/client_secrets.json`
- `credentials/youtube_token.json`

The `.gitignore` file is already configured to exclude these.

## Support

If you encounter issues:
1. Check the logs in `logs/youtube_agent.log`
2. Run with `--keep-files` to inspect intermediate outputs
3. Verify all API keys are valid and have sufficient quota
