from pydantic import BaseModel, Field
from typing import Optional


class PipelineRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300)
    style: str = Field(default="viral")
    duration: int = Field(default=60, ge=15, le=180)


class PipelineResponse(BaseModel):
    id: int
    topic: str
    style: str
    duration: int
    status: str
    script: Optional[str] = None
    video_url: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: str
    updated_at: str
