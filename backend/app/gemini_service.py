import google.generativeai as genai
import httpx
import os
import tempfile
import json
import re
from typing import List, Optional
from .config import settings
from .models import TranscriptSegment, BRollClip, BRollInsertion

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

async def download_video(url: str) -> str:
    """Download video from URL to a temporary file."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Create temp file with .mp4 extension
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)
        
        return temp_path

def upload_to_gemini(file_path: str, mime_type: str = "video/mp4"):
    """Upload a file to Gemini and return the file object."""
    file = genai.upload_file(file_path, mime_type=mime_type)
    return file

async def transcribe_a_roll(video_url: str) -> tuple[List[TranscriptSegment], float]:
    """
    Transcribe A-roll video using Gemini's multimodal capabilities.
    Returns transcript segments with timestamps and video duration.
    """
    # Download video
    temp_path = await download_video(video_url)
    
    try:
        # Upload to Gemini
        video_file = upload_to_gemini(temp_path)
        
        # Wait for file to be processed
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {video_file.state.name}")
        
        # Use Gemini to transcribe
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        prompt = """Analyze this video and provide a detailed transcript with timestamps.

The speaker may be speaking in Hinglish (Hindi-English mix). Transcribe exactly what is said.

Return ONLY a valid JSON object in this exact format:
{
    "duration_sec": <total video duration in seconds>,
    "segments": [
        {
            "start_sec": <start time in seconds>,
            "end_sec": <end time in seconds>,
            "text": "<transcribed text for this segment>"
        }
    ]
}

Rules:
1. Break the transcript into sentence-level segments
2. Each segment should be 2-8 seconds long
3. Timestamps must be accurate to 0.5 seconds
4. Include all spoken content
5. Return ONLY the JSON, no other text"""

        response = model.generate_content([video_file, prompt])
        
        # Parse response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        data = json.loads(response_text)
        
        segments = [
            TranscriptSegment(
                start_sec=seg["start_sec"],
                end_sec=seg["end_sec"],
                text=seg["text"]
            )
            for seg in data["segments"]
        ]
        
        # Clean up uploaded file
        genai.delete_file(video_file.name)
        
        return segments, data["duration_sec"]
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def analyze_b_roll(b_roll: dict) -> BRollClip:
    """
    Analyze a B-roll clip using Gemini Vision to enhance its description.
    """
    temp_path = await download_video(b_roll["url"])
    
    try:
        # Upload to Gemini
        video_file = upload_to_gemini(temp_path)
        
        # Wait for processing
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {video_file.state.name}")
        
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        prompt = f"""Analyze this B-roll video clip and provide information about it.

Existing metadata: {b_roll['metadata']}

Return ONLY a valid JSON object in this exact format:
{{
    "duration_sec": <video duration in seconds>,
    "enhanced_description": "<detailed description of visual content, mood, colors, movement, and themes>",
    "keywords": ["<keyword1>", "<keyword2>", ...]
}}

Focus on:
1. What is visually shown
2. The mood and atmosphere
3. Key objects and settings
4. Visual themes that could match spoken content about food, hygiene, health, or lifestyle"""

        response = model.generate_content([video_file, prompt])
        
        # Parse response
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        data = json.loads(response_text)
        
        # Clean up
        genai.delete_file(video_file.name)
        
        return BRollClip(
            id=b_roll["id"],
            url=b_roll["url"],
            metadata=b_roll["metadata"],
            duration_sec=data.get("duration_sec", 3.0),
            enhanced_description=data.get("enhanced_description", b_roll["metadata"])
        )
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def generate_insertion_plan(
    transcript: List[TranscriptSegment],
    a_roll_duration: float,
    b_rolls: List[BRollClip]
) -> List[BRollInsertion]:
    """
    Use Gemini to generate an intelligent B-roll insertion plan.
    """
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    # Prepare transcript text
    transcript_text = "\n".join([
        f"[{seg.start_sec:.1f}s - {seg.end_sec:.1f}s]: {seg.text}"
        for seg in transcript
    ])
    
    # Prepare B-roll descriptions
    b_roll_text = "\n".join([
        f"- {br.id}: {br.enhanced_description or br.metadata} (duration: {br.duration_sec:.1f}s)"
        for br in b_rolls
    ])
    
    prompt = f"""You are a professional video editor. Analyze the following A-roll transcript and B-roll clips, then create an optimal B-roll insertion plan.

A-ROLL TRANSCRIPT (duration: {a_roll_duration:.1f}s):
{transcript_text}

AVAILABLE B-ROLL CLIPS:
{b_roll_text}

RULES:
1. Insert 3-6 B-roll clips total
2. Each insertion should be 1.5-3 seconds long
3. Minimum 5 seconds gap between insertions
4. Do NOT insert B-roll during emotionally important or key message moments
5. Prefer inserting B-roll when the speaker mentions concepts that match the B-roll visuals
6. B-roll should enhance the message, not distract from it
7. Match B-roll thematically to what is being said at that moment
8. Consider the flow and pacing of the video

Return ONLY a valid JSON object in this exact format:
{{
    "insertions": [
        {{
            "start_sec": <when to start showing B-roll>,
            "duration_sec": <how long to show B-roll>,
            "broll_id": "<which B-roll clip to use>",
            "confidence": <0.0-1.0 confidence score>,
            "reason": "<brief explanation of why this B-roll fits here>"
        }}
    ]
}}

Be strategic and thoughtful about placements. The B-roll should feel natural and enhance storytelling."""

    response = model.generate_content(prompt)
    
    # Parse response
    response_text = response.text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)
    
    data = json.loads(response_text)
    
    insertions = [
        BRollInsertion(
            start_sec=ins["start_sec"],
            duration_sec=ins["duration_sec"],
            broll_id=ins["broll_id"],
            confidence=ins["confidence"],
            reason=ins["reason"]
        )
        for ins in data["insertions"]
    ]
    
    # Sort by start time
    insertions.sort(key=lambda x: x.start_sec)
    
    return insertions
