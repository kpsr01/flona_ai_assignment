# Flona AI - Automated B-Roll Insertion System

An intelligent system that automatically plans B-roll clip insertions into A-roll (talking-head/UGC) videos using Google's Gemini AI for video understanding and semantic matching.

## 🎯 Problem Statement

Given an A-roll video (person speaking to camera) and multiple B-roll clips, the system:
1. Analyzes the A-roll video and extracts timestamped transcription
2. Analyzes B-roll clips to understand their visual content
3. Automatically decides where and which B-roll clips should be inserted
4. Outputs a structured timeline plan with reasoning
5. Optionally renders the final stitched video

## ✨ Features

- **A-Roll Transcription**: Gemini-powered transcription with timestamps (supports Hinglish)
- **B-Roll Analysis**: AI-enhanced visual content descriptions for each clip
- **Intelligent Matching**: Semantic matching that considers context, timing, and visual relevance
- **Timeline Visualization**: Interactive React UI to view transcript and proposed insertions
- **Video Rendering**: FFmpeg-based video stitching with smooth crossfade transitions
- **Continuous Audio**: A-roll narration remains uninterrupted throughout

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   Gemini AI     │
│   (Frontend)    │◀────│   (Backend)     │◀────│   (Analysis)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   FFmpeg        │
                        │   (Rendering)   │
                        └─────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Frontend** | React 18, Vite, TailwindCSS |
| **AI/LLM** | Google Gemini 2.5 Flash Lite |
| **Video Processing** | FFmpeg |
| **HTTP Client** | httpx, axios |

## 📋 Prerequisites

1. **Python 3.11+** - [Download](https://python.org)
2. **Node.js 18+** - [Download](https://nodejs.org)
3. **FFmpeg** - Required for video rendering
4. **Google Gemini API Key** - [Get API Key](https://aistudio.google.com/app/apikey)

### Installing FFmpeg

**Windows:**
```bash
winget install FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/flona-ai.git
cd flona-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 3. Configure Environment Variables

Edit `backend/.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

## ▶️ Running the Application

### Terminal 1 - Start Backend

```bash
cd backend
venv\Scripts\activate  # Windows
# OR: source venv/bin/activate  # Linux/macOS

uvicorn app.main:app --reload --port 8000
```

### Terminal 2 - Start Frontend

```bash
cd frontend
npm run dev
```

### Access the Application

Open **http://localhost:5173** in your browser.

## 📖 Usage Guide

1. **View Sample Videos**: The app loads pre-configured A-roll and B-roll videos
2. **Generate Plan**: Click "Generate B-Roll Plan" to analyze videos (~1-2 minutes)
3. **Review Results**:
   - View the visual timeline with insertion markers
   - Read the full transcript with timestamps
   - See each B-roll insertion with confidence score and reasoning
4. **Download Plan**: Export the timeline plan as JSON
5. **Render Video**: Generate the final stitched video with B-roll overlays

## 📤 Output Format

### Timeline Plan JSON

```json
{
  "a_roll_duration": 40.11,
  "transcript": [
    {
      "start_sec": 0.78,
      "end_sec": 2.31,
      "text": "Aapko pata hai?"
    }
  ],
  "insertions": [
    {
      "start_sec": 12.5,
      "duration_sec": 2.0,
      "broll_id": "broll_3",
      "confidence": 0.85,
      "reason": "Speaker mentions hygiene concerns, matching B-roll showing uncovered food"
    }
  ],
  "b_rolls": [...]
}
```

### Rendered Video

- Format: MP4 (H.264 video, AAC audio)
- B-roll overlays with 0.3s crossfade transitions
- Continuous A-roll audio throughout

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check with Gemini status |
| `/sample-data` | GET | Get sample video URLs |
| `/generate-plan` | POST | Generate B-roll insertion plan |
| `/render-video` | POST | Render final video (async) |
| `/render-status/{job_id}` | GET | Check render job status |
| `/download/{filename}` | GET | Download rendered video |
| `/timeline-plan` | GET | Get last saved plan |

## 📁 Project Structure

```
flona-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI routes
│   │   ├── config.py         # Settings
│   │   ├── models.py         # Pydantic models
│   │   ├── gemini_service.py # Gemini AI integration
│   │   └── video_renderer.py # FFmpeg rendering
│   ├── outputs/              # Generated plans & videos
│   ├── uploads/              # Uploaded files
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VideoPreview.jsx
│   │   │   ├── TranscriptView.jsx
│   │   │   ├── Timeline.jsx
│   │   │   └── InsertionsList.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── video_urls.json           # Sample video URLs
└── README.md
```

## 🧠 Design Decisions

### Why Gemini for Everything?

1. **Unified API**: Single dependency for transcription, vision, and reasoning
2. **Multimodal Native**: Direct video understanding without frame extraction
3. **Hinglish Support**: Excellent mixed-language transcription
4. **Cost-Effective**: Gemini 2.5 Flash Lite offers great performance/cost ratio

### Matching Logic

The system goes beyond naive random insertion:
- **Semantic Matching**: Aligns B-roll content with transcript meaning
- **Timing Rules**: Minimum 5-second gaps between insertions
- **Context Awareness**: Avoids critical speaking moments
- **Visual Enhancement**: Prefers moments where visuals add value

### B-Roll Constraints

| Constraint | Value |
|------------|-------|
| Insertions per video | 3-6 |
| Duration per insertion | 1.5-3 seconds |
| Minimum gap | 5 seconds |
| Transitions | 0.3s crossfade |

## ⚠️ Limitations

- A-roll length: 30-90 seconds (optimized range)
- B-roll clips: Up to 6 clips
- Requires internet for Gemini API
- FFmpeg required for video rendering

## 🔧 Troubleshooting

### "Gemini API key not configured"
- Ensure `.env` file exists in `backend/`
- Verify `GEMINI_API_KEY` is set correctly
- Restart the backend server

### "FFmpeg not found"
- Install FFmpeg and ensure it's in system PATH
- Restart terminal after installation
- Test with: `ffmpeg -version`

### "Video processing failed"
- Check video URLs are accessible
- Verify Gemini API quota not exceeded
- Check backend logs for detailed errors

## 📄 License

MIT License

## 🙏 Acknowledgments

- Google Gemini AI for multimodal video understanding
- FFmpeg for video processing capabilities
