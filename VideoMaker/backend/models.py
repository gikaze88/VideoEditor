from pydantic import BaseModel
from typing import Optional


class JobCreate(BaseModel):
    style: str
    title: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    style: str
    title: Optional[str]
    status: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    output_video_path: Optional[str]
    output_dir: Optional[str]
    log_file: Optional[str]
    error_message: Optional[str]


class JobLogsResponse(BaseModel):
    id: str
    status: str
    logs: str
    output_video_path: Optional[str]
