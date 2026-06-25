from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from backend.schemas import (
    HookGenerationRequest, 
    HookGenerationResponse, 
    CategoryListResponse,
    CampaignHistoryItem,
    CampaignDetail
)
from backend.services.loader import get_available_categories
from backend.services.generator import generate_ad_hooks
from backend.database.db import engine, Base, get_db
from backend.database import crud
from backend.services.adset_loader import load_all_adset_references, get_available_adset_categories

app = FastAPI(
    title="AI Ad Creative Studio API",
    description="FastAPI Backend for high-converting ad copy and hook generation using Gemini and LangChain.",
    version="1.0.0"
)

# Enable CORS for frontend client communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    Triggers local storage database initializations using SQLAlchemy.
    """
    try:
        from backend.database.db import DATABASE_PATH
        Base.metadata.create_all(bind=engine)
        print("[INFO] SQLAlchemy Database initialized successfully.")
        print(f"[INFO] Database connection status: {DATABASE_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Database: {e}")

@app.get("/", tags=["Health"])
def read_root():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy", 
        "service": "AI Ad Creative Studio API",
        "version": "1.0.0"
    }

@app.get("/api/v1/categories", response_model=CategoryListResponse, tags=["Metadata"])
def get_categories():
    """
    Retrieves all available ad categories by scanning the reference_ads directory dynamically.
    """
    try:
        categories = get_available_categories()
        return CategoryListResponse(categories=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan categories: {str(e)}")

@app.post("/api/v1/generate/hooks", response_model=HookGenerationResponse, tags=["Generation"])
def generate_hooks(request: HookGenerationRequest):
    """
    Receives user brief, loads markdown reference ads dynamically,
    and returns customized hooks, headlines, body copies, and optional video scripts.
    """
    try:
        response = generate_ad_hooks(request)
        try:
            return response.model_dump()
        except AttributeError:
            return response.dict()
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        err_msg = str(e)
        if "AI generation limit reached" in err_msg:
            raise HTTPException(status_code=429, detail="AI generation limit reached. Please try again shortly.")
        elif "Gemini API key not configured" in err_msg:
            raise HTTPException(status_code=400, detail="Gemini API key not configured.")
        elif "Generation took too long" in err_msg:
            raise HTTPException(status_code=408, detail="Generation took too long. Please try again.")
        elif "Please complete all required fields" in err_msg:
            raise HTTPException(status_code=400, detail="Please complete all required fields.")
        else:
            print(f"[ERROR] Ad creative generation failed: {e}")
            raise HTTPException(status_code=500, detail="AI service is temporarily unavailable. Please try again.")

@app.get("/api/v1/campaigns", response_model=List[CampaignHistoryItem], tags=["History"])
def list_campaigns(limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieves a list of all saved campaigns from SQLite.
    Returns lightweight summary objects, ordered by created_at DESC and limited/clamped safely.
    """
    try:
        campaigns = crud.get_all_campaigns(db, limit=limit)
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query campaign history: {str(e)}")

@app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignDetail, tags=["History"])
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the complete details of a specific saved campaign.
    Triggers deferred loading for heavy text fields automatically.
    """
    campaign = crud.get_campaign_by_id(db, campaign_id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign ID {campaign_id} not found")
    return campaign

@app.delete("/api/v1/campaigns/{campaign_id}", tags=["History"])
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific campaign record from SQLite by ID.
    """
    success = crud.delete_campaign(db, campaign_id=campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Campaign ID {campaign_id} not found or already deleted")
    return {"status": "success", "message": f"Campaign ID {campaign_id} successfully deleted"}

@app.get("/api/v1/adset-references", tags=["Metadata"])
def get_adset_references():
    """
    Test endpoint retrieving count, category names, and preview of combined adset markdown references.
    """
    try:
        categories = get_available_adset_categories()
        combined_text = load_all_adset_references()
        preview = combined_text[:500] if combined_text else ""
        return {
            "count": len(categories),
            "categories": categories,
            "preview": preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load adset references: {str(e)}")
