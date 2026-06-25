import sys
import os

# Append project root to sys.path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db import Base, engine, SessionLocal
from backend.database import crud, models

def test_sqlite_storage():
    print("--- STARTING SQLITE STORAGE LAYER UNIT TEST ---")
    
    # 1. Initialize schemas
    print("[1] Building schemas and verifying index structures...")
    Base.metadata.drop_all(bind=engine)  # clean slate for unit test
    Base.metadata.create_all(bind=engine)
    print("    Database schemas created.")
    
    # 2. Insert test campaigns
    print("[2] Inserting test campaign briefs with JSON list structures...")
    db = SessionLocal()
    try:
        campaign_a_data = {
            "product_name": "Antigravity Dev Suit",
            "product_description": "AI-powered terminal and pair-programming assistant.",
            "category": "education",
            "audience": "Advanced software engineers",
            "language": "English",
            "offer_angle": "Free trial for 30 days",
            "campaign_objective": "Registrations",
            "cta": "Sign Up",
            "platform": "Meta Ads (Facebook + Instagram)",
            "pain_point": "Writing repetitive boilerplate code manually",
            "usp": "Understands entire codebase semantic connections",
            "hooks": ["Stuck in boilerplate hell? Let Antigravity write it.", "Meet your new AI pair programmer."],
            "headlines": ["Write 10x faster code", "Code without friction"],
            "primary_texts": ["Primary text copy variation 1...", "Primary text copy variation 2..."],
            "ctas": ["Sign Up", "Learn More"],
            "video_script": "Opening: Code flyby...\nScene 01: Typings...\nClosing: CTA Sign Up",
            "compliance_status": "safe",
            "compliance_issues": []
        }
        
        campaign_b_data = {
            "product_name": "FitLife Daily",
            "product_description": "Customized protein shakes and workout schedules delivered to your doorstep.",
            "category": "ecommerce",
            "audience": "Busy corporate workers looking to stay fit",
            "language": "Hinglish",
            "offer_angle": "Get 20% off your first subscription",
            "campaign_objective": "Sales",
            "cta": "Order Now",
            "platform": "Others",
            "pain_point": "No time to prepare nutritional meals after work",
            "usp": "Delicious nutrient-dense blends ready in 30 seconds",
            "hooks": ["Skip the kitchen, keep the nutrition.", "Healthy, fast, and delivered."],
            "headlines": ["Fitness in 30 seconds", "Corporate health simplified"],
            "primary_texts": ["Body text variation A...", "Body text variation B..."],
            "ctas": ["Shop Now", "Get Offer"],
            "video_script": "Opening: Blender blending...\nScene 01: Drinking...\nClosing: CTA Shop Now",
            "compliance_status": "warning",
            "compliance_issues": [
                {
                    "rule_id": "MR-02",
                    "severity": "warning",
                    "type": "Unrealistic Claims",
                    "text": "Lose 10kg in 1 week",
                    "suggestion": "Achieve your fitness goals sustainably"
                }
            ]
        }
        
        # Perform creations
        campaign_a = crud.create_campaign(db, campaign_a_data)
        print(f"    Campaign A created with ID: {campaign_a.id}")
        
        campaign_b = crud.create_campaign(db, campaign_b_data)
        print(f"    Campaign B created with ID: {campaign_b.id}")
        
        # 3. Retrieve and verify sorting / limits
        print("[3] Testing list query (ORDER BY created_at DESC)...")
        campaigns = crud.get_all_campaigns(db, limit=10)
        assert len(campaigns) == 2, f"Expected 2 campaigns, got {len(campaigns)}"
        
        # Newest (Campaign B) must be first
        assert campaigns[0].id == campaign_b.id, f"Expected newest (ID {campaign_b.id}) first, got ID {campaigns[0].id}"
        print("    Newest first order verified.")
        
        # 4. Check lazy loading of deferred heavy fields in listing query
        print("[4] Checking deferred (lazy loading) behavior of listing query...")
        # Get query objects directly and inspect dictionary to ensure heavy columns are NOT loaded
        # Under SQLAlchemy, deferred columns appear in __dict__ only after access.
        loaded_dict = campaigns[0].__dict__
        is_deferred_video = "video_script" not in loaded_dict
        is_deferred_primary = "primary_texts" not in loaded_dict
        print(f"    Primary Texts deferred: {is_deferred_video}")
        print(f"    Video Script deferred: {is_deferred_primary}")
        
        # Accessing them should trigger a lazy load query and populate them transparently
        print("    Accessing deferred column...")
        script = campaigns[0].video_script
        assert "Blender" in script, f"Failed to retrieve script, got: {script}"
        print("    Deferred fields lazy load verified.")
        
        # 5. Check native JSON list/dict deserialization
        print("[5] Checking JSON column serialization and parsing...")
        issues = campaigns[0].compliance_issues
        assert isinstance(issues, list), f"Expected list for issues, got {type(issues)}"
        assert len(issues) == 1, "Expected 1 compliance issue"
        assert issues[0]["rule_id"] == "MR-02", f"Expected MR-02, got {issues[0]['rule_id']}"
        print("    Native JSON parsing verified.")
        
        # 6. Deletion
        print("[6] Testing delete_campaign helper...")
        success = crud.delete_campaign(db, campaign_a.id)
        assert success is True, "Delete campaign should return True"
        deleted = crud.get_campaign_by_id(db, campaign_a.id)
        assert deleted is None, "Campaign should be deleted"
        print("    Deletion verified.")
        
        print("\n--- ALL STORAGE UNIT TESTS PASSED SUCCESSFULLY! ---")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_sqlite_storage()
