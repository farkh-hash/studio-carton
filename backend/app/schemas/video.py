from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2500)
    negative_prompt: str = Field(default="", max_length=2500)
    style: str = Field(default="cardboard_3d")
    duration: int = Field(default=4, ge=3, le=10)
    aspect_ratio: str = Field(default="9:16")
    model: str = Field(default="ltx-video-2b")
    enhance_prompt: bool = Field(default=True)


class VideoResponse(BaseModel):
    id: int
    task_id: str
    prompt: str
    negative_prompt: str
    style: str
    duration: int
    aspect_ratio: str
    model: str
    status: str
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: str
    updated_at: str


class PromptEnhanceRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    mood: str = Field(default="fun")
    style_variant: str = Field(default="classic")
