import subprocess
import os
import tempfile
import httpx
from typing import List
from .models import BRollInsertion, BRollClip
from .config import settings

# Transition duration in seconds for smooth crossfades
TRANSITION_DURATION = 0.3

async def download_video_file(url: str, output_path: str) -> str:
    """Download video from URL to specified path."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
    return output_path

def get_video_info(file_path: str) -> dict:
    """Get video width, height, and fps using ffprobe."""
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "json",
        file_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    
    # Parse frame rate (could be "30/1" or "30000/1001")
    fps_parts = stream["r_frame_rate"].split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
    
    return {
        "width": stream["width"],
        "height": stream["height"],
        "fps": fps
    }

async def render_final_video(
    a_roll_url: str,
    b_rolls: List[BRollClip],
    insertions: List[BRollInsertion],
    output_filename: str = "final_output.mp4"
) -> str:
    """
    Render final video with B-roll overlays using FFmpeg.
    A-roll audio remains continuous throughout.
    Uses segment-based approach with crossfade transitions.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Download A-roll
        a_roll_path = os.path.join(temp_dir, "a_roll.mp4")
        await download_video_file(a_roll_url, a_roll_path)
        
        # Download all B-rolls
        b_roll_paths = {}
        for b_roll in b_rolls:
            b_roll_path = os.path.join(temp_dir, f"{b_roll.id}.mp4")
            await download_video_file(b_roll.url, b_roll_path)
            b_roll_paths[b_roll.id] = b_roll_path
        
        # Get A-roll video info
        a_roll_info = get_video_info(a_roll_path)
        width = a_roll_info["width"]
        height = a_roll_info["height"]
        fps = a_roll_info["fps"]
        
        # Sort insertions by start time
        sorted_insertions = sorted(insertions, key=lambda x: x.start_sec)
        
        # Build input list
        inputs = ["-i", a_roll_path]
        for insertion in sorted_insertions:
            b_roll_path = b_roll_paths.get(insertion.broll_id)
            if b_roll_path:
                inputs.extend(["-i", b_roll_path])
        
        # Build filter complex using a different approach:
        # 1. Prepare each B-roll: scale, trim to duration, and set proper fps
        # 2. For each B-roll insertion, create a segment that fades in/out
        # 3. Overlay the B-roll segments on top of A-roll at the correct times
        
        filter_parts = []
        
        # Prepare A-roll base with consistent fps
        filter_parts.append(f"[0:v]fps={fps},format=yuv420p[aroll]")
        
        # Prepare each B-roll with scaling, timing, and fade transitions
        for i, insertion in enumerate(sorted_insertions):
            input_idx = i + 1
            duration = insertion.duration_sec
            fade_in_start = 0
            fade_out_start = max(0, duration - TRANSITION_DURATION)
            
            # Scale B-roll to match A-roll, set fps, trim to duration, add fade in/out
            # Use setpts to reset timestamps so B-roll plays from the beginning
            filter_parts.append(
                f"[{input_idx}:v]"
                f"fps={fps},"
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setpts=PTS-STARTPTS,"
                f"trim=duration={duration},"
                f"setpts=PTS-STARTPTS,"
                f"format=yuv420p,"
                f"fade=t=in:st={fade_in_start}:d={TRANSITION_DURATION},"
                f"fade=t=out:st={fade_out_start}:d={TRANSITION_DURATION}"
                f"[b{i}]"
            )
        
        # Create overlay chain - overlay each B-roll at its start time
        # The key is to use setpts to delay the B-roll to start at the right time,
        # then use overlay with eof_action to handle when B-roll ends
        
        current_base = "[aroll]"
        for i, insertion in enumerate(sorted_insertions):
            # Delay the B-roll to start at insertion.start_sec
            # Then overlay it on the current base
            delayed_broll = f"[b{i}delayed]"
            filter_parts.append(
                f"[b{i}]setpts=PTS+{insertion.start_sec}/TB{delayed_broll}"
            )
            
            next_output = f"[v{i}]" if i < len(sorted_insertions) - 1 else "[vout]"
            
            # Overlay with shortest=0 so A-roll continues after B-roll ends
            # eof_action=pass means continue showing base when overlay ends
            filter_parts.append(
                f"{current_base}{delayed_broll}overlay=0:0:eof_action=pass{next_output}"
            )
            current_base = next_output
        
        # Handle case with no insertions
        if not sorted_insertions:
            filter_parts.append("[aroll]copy[vout]")
        
        filter_complex = ";".join(filter_parts)
        
        # Output path
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a",  # Keep A-roll audio continuous
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        
        print(f"Running FFmpeg command...")
        print(f"Filter complex: {filter_complex}")
        
        # Run FFmpeg
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            print(f"FFmpeg stderr: {process.stderr}")
            raise RuntimeError(f"FFmpeg error: {process.stderr}")
        
        return output_path
    
    finally:
        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_video_duration(file_path: str) -> float:
    """Get video duration using FFprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())
