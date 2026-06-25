from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database import models

def create_campaign(db: Session, campaign_data: dict) -> models.Campaign:
    """
    Saves a complete generated campaign into SQLite using SQLAlchemy.
    """
    # Create the model instance using the campaign_data dict
    campaign = models.Campaign(
        product_name=campaign_data.get("product_name"),
        product_description=campaign_data.get("product_description"),
        category=campaign_data.get("category"),
        audience=campaign_data.get("audience"),
        language=campaign_data.get("language"),
        offer_angle=campaign_data.get("offer_angle"),
        campaign_objective=campaign_data.get("campaign_objective"),
        pain_point=campaign_data.get("pain_point"),
        usp=campaign_data.get("usp"),
        brand_voice=campaign_data.get("brand_voice"),
        desired_cta=campaign_data.get("desired_cta") or campaign_data.get("cta"),
        platform=campaign_data.get("platform"),
        
        # Output fields (SQLAlchemy JSON maps Python lists/dicts automatically)
        hooks=campaign_data.get("hooks", []),
        headlines=campaign_data.get("headlines", []),
        primary_texts=campaign_data.get("primary_texts", []),
        ctas=campaign_data.get("ctas", []),
        video_script=campaign_data.get("video_script"),  # Formatted text
        
        # Compliance
        compliance_status=campaign_data.get("compliance_status", "safe"),
        compliance_issues=campaign_data.get("compliance_issues", []),
        
        # Ad Set Settings
        generate_adsets=campaign_data.get("generate_adsets", False),
        adset_count=campaign_data.get("adset_count", 0),
        auto_generate_adsets=campaign_data.get("auto_generate_adsets", True),
        
        # Ad Set creatives list
        adset_creatives=campaign_data.get("adset_creatives"),
        
        # Metadata
        generation_type=campaign_data.get("generation_type", "Meta Ad Copy"),
        created_at=datetime.now(ZoneInfo("Asia/Kolkata"))
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

def get_all_campaigns(db: Session, limit: int = 50) -> List[models.Campaign]:
    """
    Queries and returns all saved campaigns, newest first.
    Enforces a strict safe limit clamp (min 1, max 100).
    Note: Heavy fields (primary_texts, video_script) are deferred and won't be queried.
    """
    # Clamp limit safely to avoid excessive payload sizes
    clamped_limit = min(max(1, limit), 100)
    
    return (
        db.query(models.Campaign)
        .order_by(models.Campaign.created_at.desc())
        .limit(clamped_limit)
        .all()
    )

def get_campaign_by_id(db: Session, campaign_id: int) -> Optional[models.Campaign]:
    """
    Retrieves a single complete campaign detail from SQLite by ID.
    Accessing the deferred fields will trigger lazy loading automatically.
    """
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def delete_campaign(db: Session, campaign_id: int) -> bool:
    """
    Deletes a campaign from the database by ID.
    Returns True if successfully deleted, False otherwise.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign:
        db.delete(campaign)
        db.commit()
        return True
    return False
