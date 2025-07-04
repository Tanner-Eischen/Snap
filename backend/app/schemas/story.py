"""Story schemas.

This module defines Pydantic schemas for story-related
data validation and serialization.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class StoryType(str, Enum):
    """Enum for story content types."""
    IMAGE = "image"
    VIDEO = "video"
    PLANT_SHOWCASE = "plant_showcase"  # Special plant-focused story
    PLANT_TIMELAPSE = "plant_timelapse"  # Plant growth timelapse
    GARDEN_TOUR = "garden_tour"  # Garden/collection showcase


class StoryPrivacyLevel(str, Enum):
    """Enum for story privacy levels."""
    PUBLIC = "public"
    FRIENDS = "friends"
    CLOSE_FRIENDS = "close_friends"
    PLANT_COMMUNITY = "plant_community"  # Visible to plant enthusiasts


class StoryBase(BaseModel):
    """Base story schema with common fields."""
    content_type: StoryType
    media_url: str
    caption: Optional[str] = Field(None, max_length=500)
    
    # Media metadata
    file_size: Optional[int] = Field(None, ge=0)
    duration: Optional[float] = Field(None, ge=0)  # For videos in seconds
    
    # Privacy settings
    privacy_level: StoryPrivacyLevel = StoryPrivacyLevel.FRIENDS
    
    # Plant-specific fields
    plant_data: Optional[dict] = None  # Plant identification/info
    plant_tags: Optional[List[str]] = None  # Plant-related hashtags
    care_tip: Optional[str] = Field(None, max_length=200)  # Quick care tip
    location_tag: Optional[str] = Field(None, max_length=100)  # Garden location


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    
    @validator('media_url')
    def validate_media_url(cls, v):
        if not v or not v.strip():
            raise ValueError('media_url is required')
        return v
    
    @validator('duration')
    def validate_duration(cls, v, values):
        content_type = values.get('content_type')
        if content_type == StoryType.VIDEO and v is None:
            raise ValueError('Video stories must have duration')
        if v is not None and v > 60:  # Max 60 seconds for stories
            raise ValueError('Story duration cannot exceed 60 seconds')
        return v
    
    @validator('plant_tags')
    def validate_plant_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('Maximum 10 plant tags allowed')
            for tag in v:
                if len(tag) > 30:
                    raise ValueError('Plant tags must be 30 characters or less')
        return v


class StoryUpdate(BaseModel):
    """Schema for updating a story (limited fields)."""
    caption: Optional[str] = Field(None, max_length=500)
    privacy_level: Optional[StoryPrivacyLevel] = None
    plant_tags: Optional[List[str]] = None
    care_tip: Optional[str] = Field(None, max_length=200)
    
    @validator('plant_tags')
    def validate_plant_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('Maximum 10 plant tags allowed')
            for tag in v:
                if len(tag) > 30:
                    raise ValueError('Plant tags must be 30 characters or less')
        return v


class StoryRead(StoryBase):
    """Schema for reading story data."""
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    view_count: int = 0
    
    # User information (for display)
    user_username: Optional[str] = None
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    
    # Viewer-specific data
    has_viewed: Optional[bool] = None
    viewed_at: Optional[datetime] = None
    
    # Story analytics (for owner)
    unique_viewers: Optional[int] = None
    total_screenshots: Optional[int] = None
    
    class Config:
        from_attributes = True


class StoryViewCreate(BaseModel):
    """Schema for creating a story view."""
    story_id: str
    
    # Optional metadata
    view_duration: Optional[float] = Field(None, ge=0)  # How long they viewed
    screenshot_taken: bool = False


class StoryView(BaseModel):
    """Schema for story view data."""
    id: str
    story_id: str
    viewer_id: str
    viewed_at: datetime
    view_duration: Optional[float] = None
    screenshot_taken: bool = False
    
    # Viewer information (for story owner)
    viewer_username: Optional[str] = None
    viewer_display_name: Optional[str] = None
    viewer_avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class StoryFeed(BaseModel):
    """Schema for story feed data."""
    user_id: str
    user_username: str
    user_display_name: str
    user_avatar_url: Optional[str] = None
    
    # Story ring info
    has_unviewed_stories: bool = False
    total_stories: int = 0
    latest_story_at: Optional[datetime] = None
    
    # Stories list (if expanded)
    stories: Optional[List[StoryRead]] = None
    
    class Config:
        from_attributes = True


class StoryHighlight(BaseModel):
    """Schema for story highlights (saved stories)."""
    id: str
    user_id: str
    title: str = Field(..., min_length=1, max_length=50)
    cover_image_url: Optional[str] = None
    story_ids: List[str] = Field(..., min_items=1, max_items=100)
    created_at: datetime
    updated_at: datetime
    
    # Display info
    story_count: int = 0
    
    class Config:
        from_attributes = True


class StoryHighlightCreate(BaseModel):
    """Schema for creating a story highlight."""
    title: str = Field(..., min_length=1, max_length=50)
    cover_image_url: Optional[str] = None
    story_ids: List[str] = Field(..., min_items=1, max_items=100)
    
    @validator('story_ids')
    def validate_unique_story_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('story_ids must be unique')
        return v


class StoryHighlightUpdate(BaseModel):
    """Schema for updating a story highlight."""
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    cover_image_url: Optional[str] = None
    story_ids: Optional[List[str]] = Field(None, min_items=1, max_items=100)
    
    @validator('story_ids')
    def validate_unique_story_ids(cls, v):
        if v is not None and len(v) != len(set(v)):
            raise ValueError('story_ids must be unique')
        return v


class PlantStoryData(BaseModel):
    """Schema for plant-specific story data."""
    plant_name: Optional[str] = None
    scientific_name: Optional[str] = None
    plant_age: Optional[str] = None  # "2 months", "1 year", etc.
    growth_stage: Optional[str] = Field(None, pattern=r"^(seedling|juvenile|mature|flowering|fruiting)$")
    care_difficulty: Optional[str] = Field(None, pattern=r"^(easy|moderate|difficult)$")
    
    # Care information
    watering_frequency: Optional[str] = None
    light_requirements: Optional[str] = None
    soil_type: Optional[str] = None
    
    # Progress tracking
    is_before_after: bool = False
    progress_description: Optional[str] = Field(None, max_length=200)
    
    class Config:
        from_attributes = True


class StoryAnalytics(BaseModel):
    """Schema for story analytics."""
    story_id: str
    total_views: int = 0
    unique_viewers: int = 0
    view_completion_rate: Optional[float] = None  # Percentage who watched full video
    screenshots_taken: int = 0
    shares_count: int = 0
    
    # Viewer demographics
    viewers_by_experience: dict = {}  # beginner, intermediate, advanced, expert
    viewers_by_location: dict = {}
    
    # Engagement metrics
    average_view_duration: Optional[float] = None
    peak_viewing_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StorySearch(BaseModel):
    """Schema for story search parameters."""
    query: Optional[str] = Field(None, min_length=1, max_length=100)
    content_type: Optional[StoryType] = None
    privacy_level: Optional[StoryPrivacyLevel] = None
    plant_tags: Optional[List[str]] = None
    user_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_plant_data: Optional[bool] = None
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v is not None and 'date_from' in values and values['date_from'] is not None:
            if v < values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v


class StoryBatch(BaseModel):
    """Schema for batch story operations."""
    story_ids: List[str] = Field(..., min_items=1, max_items=50)
    operation: str = Field(..., pattern=r"^(delete|archive|add_to_highlight)$")
    highlight_id: Optional[str] = None  # Required for add_to_highlight operation
    
    @validator('story_ids')
    def validate_unique_story_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('story_ids must be unique')
        return v
    
    @validator('highlight_id')
    def validate_highlight_id(cls, v, values):
        operation = values.get('operation')
        if operation == 'add_to_highlight' and not v:
            raise ValueError('highlight_id is required for add_to_highlight operation')
        return v