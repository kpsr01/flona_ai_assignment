import json
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import asyncio

from .models import (
    TimelinePlan, PlanRequest, BRollClip, 
    TranscriptSegment, BRollInsertion
)
from .gemini_service import (
    transcribe_a_roll, analyze_b_roll, generate_insertion_plan
)
from .video_renderer import render_final_video
from .config import settings

app = FastAPI(
    title="Flona AI - B-Roll Insertion System",
    description="Automatically plan B-roll insertions for A-roll videos",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for processing status
processing_status = {}

def load_sample_data():
    """Load sample video URLs from JSON file."""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "video_urls.json")
    with open(json_path, 'r') as f:
        return json.load(f)

@app.get("/")
async def root():
    return {"message": "Flona AI B-Roll Insertion API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "gemini_configured": bool(settings.GEMINI_API_KEY)}

@app.get("/sample-data")
async def get_sample_data():
    """Get sample video URLs for testing."""
    try:
        data = load_sample_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-plan", response_model=TimelinePlan)
async def generate_plan(request: PlanRequest):
    """
    Generate a B-roll insertion plan for the given videos.
    """
    try:
        # Get video URLs
        if request.use_sample_data:
            data = load_sample_data()
        elif request.video_urls:
            data = request.video_urls.dict()
        else:
            raise HTTPException(status_code=400, detail="No video URLs provided")
        
        a_roll_data = data["a_roll"]
        b_rolls_data = data["b_rolls"]
        
        # Step 1: Transcribe A-roll
        print("Transcribing A-roll...")
        transcript, a_roll_duration = await transcribe_a_roll(a_roll_data["url"])
        print(f"Transcription complete. Duration: {a_roll_duration}s, Segments: {len(transcript)}")
        
        # Step 2: Analyze B-rolls (with rate limiting)
        print("Analyzing B-roll clips...")
        analyzed_b_rolls = []
        for b_roll in b_rolls_data:
            print(f"  Analyzing {b_roll['id']}...")
            analyzed = await analyze_b_roll(b_roll)
            analyzed_b_rolls.append(analyzed)
            await asyncio.sleep(1)  # Rate limiting
        print(f"B-roll analysis complete. Analyzed: {len(analyzed_b_rolls)} clips")
        
        # Step 3: Generate insertion plan
        print("Generating insertion plan...")
        insertions = await generate_insertion_plan(
            transcript=transcript,
            a_roll_duration=a_roll_duration,
            b_rolls=analyzed_b_rolls
        )
        print(f"Plan generated. Insertions: {len(insertions)}")
        
        # Build response
        timeline_plan = TimelinePlan(
            a_roll_duration=a_roll_duration,
            transcript=transcript,
            insertions=insertions,
            b_rolls=analyzed_b_rolls
        )
        
        # Save to file
        output_path = os.path.join(settings.OUTPUT_DIR, "timeline_plan.json")
        with open(output_path, 'w') as f:
            f.write(timeline_plan.model_dump_json(indent=2))
        
        return timeline_plan
    
    except Exception as e:
        print(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/render-video")
async def render_video(plan: TimelinePlan, background_tasks: BackgroundTasks):
    """
    Render the final video with B-roll insertions.
    This runs in the background and returns a job ID.
    """
    job_id = f"render_{int(asyncio.get_event_loop().time() * 1000)}"
    processing_status[job_id] = {"status": "processing", "progress": 0}
    
    async def do_render():
        try:
            # Load sample data to get URLs
            data = load_sample_data()
            
            output_path = await render_final_video(
                a_roll_url=data["a_roll"]["url"],
                b_rolls=plan.b_rolls,
                insertions=plan.insertions,
                output_filename=f"{job_id}.mp4"
            )
            processing_status[job_id] = {
                "status": "completed",
                "output_path": output_path,
                "download_url": f"/download/{job_id}.mp4"
            }
        except Exception as e:
            processing_status[job_id] = {"status": "failed", "error": str(e)}
    
    background_tasks.add_task(do_render)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/render-status/{job_id}")
async def get_render_status(job_id: str):
    """Check the status of a render job."""
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return processing_status[job_id]

@app.get("/download/{filename}")
async def download_video(filename: str):
    """Download a rendered video."""
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

@app.get("/timeline-plan")
async def get_saved_plan():
    """Get the last saved timeline plan."""
    plan_path = os.path.join(settings.OUTPUT_DIR, "timeline_plan.json")
    if not os.path.exists(plan_path):
        raise HTTPException(status_code=404, detail="No saved plan found")
    
    with open(plan_path, 'r') as f:
        return json.load(f)
