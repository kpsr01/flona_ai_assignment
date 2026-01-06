from pydantic import BaseModel
from typing import List, Optional

class TranscriptSegment(BaseModel):
    start_sec: float
    end_sec: float
    text: str

class BRollClip(BaseModel):
    id: str
    url: str
    metadata: str
    duration_sec: Optional[float] = None
    enhanced_description: Optional[str] = None

class ARollVideo(BaseModel):
    url: str
    metadata: str
    duration_sec: Optional[float] = None
    transcript: Optional[List[TranscriptSegment]] = None

class BRollInsertion(BaseModel):
    start_sec: float
    duration_sec: float
    broll_id: str
    confidence: float
    reason: str

class TimelinePlan(BaseModel):
    a_roll_duration: float
    transcript: List[TranscriptSegment]
    insertions: List[BRollInsertion]
    b_rolls: List[BRollClip]

class VideoUrls(BaseModel):
    a_roll: dict
    b_rolls: List[dict]

class PlanRequest(BaseModel):
    video_urls: Optional[VideoUrls] = None
    use_sample_data: bool = False
