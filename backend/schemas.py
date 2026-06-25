from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime

class AdSetInput(BaseModel):
    location: str = Field(..., description="Target location/geography")
    age_group: str = Field(..., description="Target age demographic group")
    detailed_targeting: List[str] = Field(..., description="List of detailed targeting interests or behaviors")

class HookGenerationRequest(BaseModel):
    # Core Fields
    product_name: str = Field(
        ...,
        description="Name of the product or service",
        example="Raaj Pharma eLearning"
    )
    product_description: str = Field(
        ...,
        description="Detailed description of the product or service",
        example="Practical online courses on Regulatory Affairs and GMP for healthcare professionals."
    )
    category: str = Field(
        ...,
        description="Reference category folder name",
        example="medical"
    )
    audience: Optional[str] = Field(
        "",
        description="Target audience description",
        example="Pharma college students and industry professionals looking to get jobs"
    )
    language: str = Field(
        ...,
        description="Desired copy language",
        example="Hinglish"
    )

    # Rich Campaign Inputs
    offer_angle: str = Field(
        ...,
        description="Offer, hook angle, discount, bonus, webinar, etc",
        example="Get a free 'GMP Compliance Checklist' with your first course signup"
    )
    campaign_objective: str = Field(
        ...,
        description="Campaign objective like leads, awareness, sales, registrations",
        example="Lead Generation"
    )
    platform: str = Field(
        ...,
        description="Target platform like Meta Ads, Reels, LinkedIn, Shorts",
        example="Meta Ads"
    )
    pain_point: str = Field(
        ...,
        description="Main customer pain point",
        example="Lack of practical, real-world industry experience needed to pass job interviews"
    )
    usp: str = Field(
        ...,
        description="Unique selling proposition or key benefit",
        example="ISO 20001 accredited courses designed and led by real life sciences QA experts"
    )

    
    brand_voice: str = Field(
        
        description="brand voice guidance",
        example="Professional yet highly conversational and encouraging"
    )
    cta: Optional[str] = Field(
        None,
        description="Preferred CTA",
        example="Learn More"
    )

    # Feature Toggles
    generate_video_script: bool = Field(
        False,
        description="Whether to generate a video script"
    )

    # Ad Set Fields (Phase 1)
    generate_adsets: bool = Field(
        False,
        description="Whether to generate Meta Ad Sets"
    )
    adset_count: int = Field(
        0,
        ge=0,
        description="Number of ad sets to generate"
    )
    auto_generate_adsets: bool = Field(
        True,
        description="Whether to auto generate ad set targeting"
    )

    manual_adsets: List[AdSetInput] = Field(
        default=[],
        description="User-provided manual targeting specs for each Ad Set"
    )

    @model_validator(mode='after')
    def validate_adsets(self) -> 'HookGenerationRequest':
        if not self.generate_adsets:
            self.adset_count = 0
            self.manual_adsets = []
        else:
            if self.adset_count < 1:
                raise ValueError("Please enter at least 1 Ad Set.")
            if self.adset_count > 20:
                raise ValueError("Maximum 20 Ad Sets allowed.")
            if not self.auto_generate_adsets:
                if len(self.manual_adsets) < self.adset_count:
                    raise ValueError(f"Please configure details for all {self.adset_count} Ad Sets.")
                for idx, ma in enumerate(self.manual_adsets[:self.adset_count], 1):
                    if not ma.location or not ma.location.strip():
                        raise ValueError(f"Location is required for Ad Set {idx}.")
                    if not ma.age_group or not ma.age_group.strip():
                        raise ValueError(f"Age Group is required for Ad Set {idx}.")
                    cleaned_targeting = [t.strip() for t in ma.detailed_targeting if t.strip()]
                    if not cleaned_targeting:
                        raise ValueError(f"Detailed Targeting interests are required for Ad Set {idx}.")
                    ma.detailed_targeting = cleaned_targeting
        return self

class AdSet(BaseModel):
    location: str = Field(..., description="Target location/geography")
    age_group: str = Field(..., description="Target age demographic group")
    detailed_targeting: List[str] = Field(..., description="List of detailed targeting interests or behaviors")

class VideoScene(BaseModel):
    scene: str = Field(..., description="Visual scene description and camera directions")
    voiceover: str = Field(..., description="Dialogue, speech, or narration for the voiceover")

class VideoScript(BaseModel):
    hook: str = Field(..., description="Opening attention grabber script section (0-5 seconds)")
    scenes: List[VideoScene] = Field(..., description="List of visual and narrative scene segments")
    cta: str = Field(..., description="Final Call to Action segment of the video script")

class ComplianceIssue(BaseModel):
    rule_id: str = Field(..., description="Unique code of the violated policy rule")
    severity: str = Field(..., description="Issue severity: 'warning' or 'high_risk'")
    type: str = Field(..., description="Meta policy category name (e.g. Personal Attribute Violation)")
    text: str = Field(..., description="The specific copywriting segment or phrase that triggered the violation")
    suggestion: str = Field(..., description="A safer, highly converting, policy-compliant rewrite suggestion")

class MetaComplianceReport(BaseModel):
    status: str = Field(..., description="Aggregate compliance rating: 'safe', 'warning', or 'high_risk'")
    issues: List[ComplianceIssue] = Field(..., description="List of structured policy issues identified")

class GeneratedAdSet(BaseModel):
    location: str = Field(..., description="Target location/geography")
    age_group: str = Field(..., description="Target age demographic group")
    detailed_targeting: List[str] = Field(..., description="List of detailed targeting interests or behaviors")

class GeneratedAdSetCollection(BaseModel):
    adsets: List[GeneratedAdSet] = Field(..., description="List of generated Meta Ad Sets")

class AdSetCreative(BaseModel):
    adset_number: int
    location: str
    age_group: str
    detailed_targeting: List[str]
    hooks: List[str]
    headlines: List[str]
    primary_texts: List[str]
    ctas: List[str]
    video_script: Optional[VideoScript] = None
    compliance_report: Optional[MetaComplianceReport] = None

class CampaignWithAdSets(BaseModel):
    adsets: List[AdSetCreative]

class HookGenerationResponse(BaseModel):
    category: str = Field(
        ...,
        description="Category used for reference retrieval"
    )
    hooks: List[str] = Field(
        ...,
        description="Exactly 5 high-converting ad hooks"
    )
    headlines: List[str] = Field(
        ...,
        description="Exactly 5 catchy headlines aligned with the hooks"
    )
    primary_texts: List[str] = Field(
        ...,
        description="Exactly 3 primary ad copy variations corresponding to the hooks"
    )
    ctas: List[str] = Field(
        ...,
        description="List of CTA button variations optimized for the platform and objective"
    )
    inferred_style_note: str = Field(
        ...,
        description="Explanation of inferred tone and writing style from target references"
    )
    video_script: Optional[VideoScript] = Field(
        None,
        description="Optional generated multi-scene video script"
    )
    compliance_report: Optional[MetaComplianceReport] = Field(
        None,
        description="Meta-policy compliance review report"
    )
    adsets: List[GeneratedAdSet] = Field(
        default=[],
        description="Optional list of generated Meta Ad Sets"
    )
    adset_creatives: Optional[List[AdSetCreative]] = Field(
        default=None,
        description="Optional list of generated creatives per ad set"
    )

class CategoryListResponse(BaseModel):
    categories: List[str] = Field(..., description="List of categories available on the server")

class CampaignHistoryItem(BaseModel):
    id: int = Field(..., description="Primary Key of the campaign")
    product_name: str = Field(..., description="Product or brand name")
    category: str = Field(..., description="Category group")
    compliance_status: str = Field(..., description="Aggregate compliance rating: 'safe', 'warning', or 'high_risk'")
    created_at: datetime = Field(..., description="Timestamp when the campaign was created")

class CampaignDetail(BaseModel):
    id: int
    product_name: str
    product_description: str
    category: str
    audience: Optional[str] = ""
    language: str
    offer_angle: str
    campaign_objective: str
    pain_point: str
    usp: str
    brand_voice: Optional[str] = None
    desired_cta: Optional[str] = None
    platform: str
    
    # Generated Outputs
    hooks: List[str]
    headlines: List[str]
    primary_texts: List[str]
    ctas: List[str]
    video_script: Optional[str] = None  # Formatted text script
    
    # Compliance
    compliance_status: str
    compliance_issues: List[ComplianceIssue]
    
    # Ad Set Settings
    generate_adsets: Optional[bool] = False
    adset_count: Optional[int] = 0
    auto_generate_adsets: Optional[bool] = True
    
    # Ad Set creatives list (Phase 4)
    adset_creatives: Optional[List[AdSetCreative]] = None
    
    # Metadata
    generation_type: str
    created_at: datetime
