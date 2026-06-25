from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import deferred
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database.db import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    
    # Input Brief Fields (Indexed for fast search and filter queries)
    product_name = Column(String, index=True, nullable=False)
    product_description = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=False)
    audience = Column(String, nullable=False)
    language = Column(String, nullable=False)
    offer_angle = Column(String, nullable=False)
    campaign_objective = Column(String, nullable=False)
    pain_point = Column(String, nullable=False)
    usp = Column(String, nullable=False)
    brand_voice = Column(String, nullable=True)
    desired_cta = Column(String, nullable=True)
    platform = Column(String, nullable=False)

    # Generated Output Fields
    hooks = Column(JSON, nullable=False)
    headlines = Column(JSON, nullable=False)
    
    # Optimized deferred columns: These heavy fields will NOT load during lightweight history queries
    primary_texts = deferred(Column(JSON, nullable=False))
    video_script = deferred(Column(Text, nullable=True))
    
    ctas = Column(JSON, nullable=False)

    # Compliance Fields
    compliance_status = Column(String, nullable=False)
    compliance_issues = Column(JSON, nullable=False)
    
    # Ad Set Settings
    generate_adsets = Column(Boolean, default=False, nullable=True)
    adset_count = Column(Integer, default=0, nullable=True)
    auto_generate_adsets = Column(Boolean, default=True, nullable=True)

    # Campaign adset creative packages list (Deferred lazy loaded JSON field)
    adset_creatives = deferred(Column(JSON, nullable=True))

    # Metadata (Indexed created_at for fast ORDER BY created_at DESC)
    generation_type = Column(String, default="Meta Ad Copy", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")), index=True, nullable=False)
