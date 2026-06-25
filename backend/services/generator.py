import time
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.services.config import config
from backend.services.prompt_builder import build_ad_creative_prompt_template, build_adset_generation_prompt_template
from backend.services.loader import load_ad_references, load_video_references
from backend.services.adset_loader import load_all_adset_references
from backend.services.compliance_checker import check_meta_compliance
from backend.database.db import SessionLocal
from backend.database import crud
from backend.schemas import HookGenerationRequest, HookGenerationResponse, GeneratedAdSetCollection, GeneratedAdSet, AdSetCreative
from typing import Optional, List

def serialize_video_script(vs) -> str:
    if not vs:
        return ""
    if isinstance(vs, str):
        return vs
    if hasattr(vs, 'dict'):
        d = vs.dict()
    elif isinstance(vs, dict):
        d = vs
    else:
        return str(vs)
    
    hook = d.get("hook", "")
    scenes = " ".join([s.get("scene", "") + " " + s.get("voiceover", "") for s in d.get("scenes", [])])
    cta = d.get("cta", "")
    return f"{hook} {scenes} {cta}"

def is_near_duplicate(str1: str, str2: str, threshold: float = 0.75) -> bool:
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()
    return ratio >= threshold

def video_script_matches_hook_angle(vs, hooks, targeting_keywords) -> bool:
    if not vs:
        return True
    script_text = serialize_video_script(vs).lower()
    
    search_terms = set()
    for kw in targeting_keywords:
        for term in kw.lower().split():
            clean = "".join(c for c in term if c.isalnum())
            if len(clean) > 3:
                search_terms.add(clean)
                
    for hook in hooks:
        for term in hook.lower().split():
            clean = "".join(c for c in term if c.isalnum())
            if len(clean) > 4:
                search_terms.add(clean)
                
    if not search_terms:
        return True
        
    matches = sum(1 for term in search_terms if term in script_text)
    return matches > 0

def check_creative_similarity(current_creative, previous_creatives, threshold: float = 0.75) -> bool:
    """
    Returns True if similarity is high (duplicates or near-duplicates found)
    or if the video script narrative doesn't match the hook angle,
    indicating that regeneration is needed.
    """
    # 1. Check internal duplicates in current creative
    def has_internal_duplicates(lst):
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if is_near_duplicate(lst[i], lst[j], threshold):
                    return True
        return False

    if has_internal_duplicates(current_creative.hooks):
        print("[INFO] High similarity detected: internal hooks duplication.")
        return True
    if has_internal_duplicates(current_creative.headlines):
        print("[INFO] High similarity detected: internal headlines duplication.")
        return True
    if has_internal_duplicates(current_creative.primary_texts):
        print("[INFO] High similarity detected: internal primary texts duplication.")
        return True

    # 2. Check duplicates against previous creatives
    for prev in previous_creatives:
        # Check hooks
        for h1 in current_creative.hooks:
            for h2 in prev.hooks:
                if is_near_duplicate(h1, h2, threshold):
                    print(f"[INFO] High similarity detected: hook matches previous adset hook.")
                    return True
        # Check headlines
        for hl1 in current_creative.headlines:
            for hl2 in prev.headlines:
                if is_near_duplicate(hl1, hl2, threshold):
                    print(f"[INFO] High similarity detected: headline matches previous adset headline.")
                    return True
        # Check primary texts
        for p1 in current_creative.primary_texts:
            for p2 in prev.primary_texts:
                if is_near_duplicate(p1, p2, threshold):
                    print(f"[INFO] High similarity detected: primary text matches previous adset primary text.")
                    return True

        # Check CTA intent (exact match of lists)
        if current_creative.ctas == prev.ctas:
            print("[INFO] High similarity detected: identical CTA intent matched.")
            return True

        # Check video script matching / duplication
        if current_creative.video_script and prev.video_script:
            v1 = serialize_video_script(current_creative.video_script)
            v2 = serialize_video_script(prev.video_script)
            if is_near_duplicate(v1, v2, threshold):
                print("[INFO] High similarity detected: video script matches previous adset script.")
                return True

    # 3. Verify video script narrative matches the Hook Angle / targeting keywords
    if current_creative.video_script:
        targeting_keywords = current_creative.detailed_targeting
        if not video_script_matches_hook_angle(current_creative.video_script, current_creative.hooks, targeting_keywords):
            print("[INFO] Video script narrative does not match Hook Angle / targeting profile.")
            return True

    return False

def generate_ad_hooks(request: HookGenerationRequest) -> HookGenerationResponse:
    """
    Orchestrates the entire creative ad generation pipeline using TRUE structured outputs:
    1. Validates environment configurations.
    2. Loads ad and optional screenplay references dynamically.
    3. Builds the master prompt template.
    4. Invokes the Gemini model with a rate-limit retry engine (429 exponential backoff).
    5. Performs an automated compliance policy review on output text.
    6. Stores the generation inputs and outputs in SQLite history.
    7. Returns the validated, formatted response model.
    """
    # 1. Verify credentials and API key
    config.validate()
    
    # 2. Retrieve references dynamically
    ad_references = load_ad_references(request.category)
    if not ad_references:
        # Dynamic style inference instruction
        ad_references = (
            "No specific reference copy available. Please dynamically infer the most appropriate "
            "professional marketing tone, persuasion style, emotional intensity, and formatting "
            "customized to the target audience, campaign objective, and brand voice guidelines."
        )
        
    video_references = ""
    if request.generate_video_script:
        video_references = load_video_references(request.category)
        if not video_references:
            # Dynamic screenplay formatting instruction
            video_references = (
                "No specific video script references available. Please dynamically design a highly original, "
                "cinematic short-form video script layout from scratch based on the USP and pain points."
            )
    
    # 3. Initialize Gemini model via LangChain
    llm = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.7,
    )
    
    max_attempts = 3
    backoff_times = [5, 10]
    
    # 4. Generate Ad Sets if requested (Phase 3 & Phase 4 User-controlled Targeting)
    generated_adsets = []
    if request.generate_adsets and request.adset_count > 0:
        if request.auto_generate_adsets:
            print("[INFO] Starting AI Ad Set generation")
            
            # Load ad set references
            adset_refs = load_all_adset_references()
            if not adset_refs:
                adset_refs = "No specific ad set references available. Please dynamically generate targeting."
                
            adset_prompt_template = build_adset_generation_prompt_template()
            structured_adset_llm = llm.with_structured_output(GeneratedAdSetCollection)
            adset_chain = adset_prompt_template | structured_adset_llm
            
            adset_inputs = {
                "adset_count": request.adset_count,
                "adset_references": adset_refs,
                "product_name": request.product_name,
                "product_description": request.product_description,
                "category": request.category,
                "audience": request.audience,
                "campaign_objective": request.campaign_objective,
                "pain_point": request.pain_point,
                "usp": request.usp,
                "platform": request.platform
            }
            
            adset_response = None
            for attempt in range(max_attempts):
                try:
                    adset_response = adset_chain.invoke(adset_inputs)
                    break
                except Exception as e:
                    error_str = str(e)
                    is_429 = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "ResourceExhausted" in error_str
                    is_503 = "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str
                    is_timeout = "timeout" in error_str.lower() or isinstance(e, TimeoutError)
                    if (is_429 or is_503) and attempt < len(backoff_times):
                        wait_time = backoff_times[attempt]
                        print(f"[RETRY WARNING] Gemini API busy/rate limited during AdSet generation. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    elif is_timeout:
                        print("[ERROR] Gemini generation timed out during AdSet generation")
                        raise ValueError("Generation took too long. Please try again.")
                    else:
                        if is_429 or is_503:
                            print("[ERROR] Gemini quota exceeded or unavailable during AdSet generation")
                            raise ValueError("AI generation limit reached. Please try again shortly.")
                        else:
                            print(f"[ERROR] Gemini generation failed during AdSet generation: {e}")
                            raise ValueError("AI service is temporarily unavailable. Please try again.")
                            
            if adset_response and adset_response.adsets:
                generated_adsets = adset_response.adsets
                print(f"[INFO] Generated Ad Set Count: {len(generated_adsets)}")
        else:
            print("[INFO] Using manual targeting coordinates directly")
            for idx, ma in enumerate(request.manual_adsets[:request.adset_count], 1):
                generated_adsets.append(
                    GeneratedAdSet(
                        location=ma.location,
                        age_group=ma.age_group,
                        detailed_targeting=ma.detailed_targeting
                    )
                )

    # 5. Get creative prompt template
    prompt_template = build_ad_creative_prompt_template(
        include_video_script=request.generate_video_script
    )
    
    # 6. Use LangChain's native Pydantic binding for TRUE structured JSON output mapping
    structured_llm = llm.with_structured_output(HookGenerationResponse)
    
    # 7. Assemble and invoke the creative chain
    chain = prompt_template | structured_llm
    
    # Helper to serialize Pydantic models regardless of version
    def serialize_pydantic(obj):
        if obj is None:
            return None
        try:
            return obj.model_dump()
        except AttributeError:
            return obj.dict()

    adset_creatives = []
    
    if request.generate_adsets and len(generated_adsets) > 0:
        print(f"[INFO] Generating creative packages for {len(generated_adsets)} Ad Sets...")
        for idx, adset in enumerate(generated_adsets, 1):
            
            adset_inputs = {
                "reference_ads": ad_references,
                "video_script_references": video_references,
                "product_name": request.product_name,
                "product_description": request.product_description,
                "category": request.category,
                "audience": request.audience,
                "language": request.language,
                "offer_angle": request.offer_angle,
                "campaign_objective": request.campaign_objective,
                "platform": request.platform,
                "pain_point": request.pain_point,
                "usp": request.usp,
                "brand_voice": request.brand_voice if request.brand_voice else "Standard brand voice.",
                "cta": request.cta if request.cta else "None specified",
                "location": adset.location,
                "age_group": adset.age_group,
                "detailed_targeting": ", ".join(adset.detailed_targeting) if isinstance(adset.detailed_targeting, list) else str(adset.detailed_targeting)
            }
            
            ac = None
            max_regen_attempts = 3
            for regen_attempt in range(max_regen_attempts):
                adset_creative_raw = None
                for attempt in range(max_attempts):
                    try:
                        adset_creative_raw = chain.invoke(adset_inputs)
                        break
                    except Exception as e:
                        error_str = str(e)
                        is_429 = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "ResourceExhausted" in error_str
                        is_503 = "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str
                        is_timeout = "timeout" in error_str.lower() or isinstance(e, TimeoutError)
                        if (is_429 or is_503) and attempt < len(backoff_times):
                            wait_time = backoff_times[attempt]
                            print(f"[RETRY WARNING] Gemini API busy/rate limited during Ad Set {idx} creative generation. Waiting {wait_time}s...")
                            time.sleep(wait_time)
                        elif is_timeout:
                            print(f"[ERROR] Gemini generation timed out during Ad Set {idx} creative generation")
                            raise ValueError("Generation took too long. Please try again.")
                        else:
                            if is_429 or is_503:
                                print(f"[ERROR] Gemini quota exceeded during Ad Set {idx} creative generation")
                                raise ValueError("AI generation limit reached. Please try again shortly.")
                            else:
                                print(f"[ERROR] Gemini generation failed during Ad Set {idx} creative generation: {e}")
                                raise ValueError("AI service is temporarily unavailable. Please try again.")
                
                if not adset_creative_raw:
                    raise ValueError(f"Failed to generate creative for Ad Set {idx}")
                    
                adset_compliance = check_meta_compliance(
                    hooks=adset_creative_raw.hooks,
                    headlines=adset_creative_raw.headlines,
                    primary_texts=adset_creative_raw.primary_texts,
                    ctas=adset_creative_raw.ctas,
                    video_script=adset_creative_raw.video_script
                )
                
                ac = AdSetCreative(
                    adset_number=idx,
                    location=adset.location,
                    age_group=adset.age_group,
                    detailed_targeting=adset.detailed_targeting,
                    hooks=adset_creative_raw.hooks,
                    headlines=adset_creative_raw.headlines,
                    primary_texts=adset_creative_raw.primary_texts,
                    ctas=adset_creative_raw.ctas,
                    video_script=adset_creative_raw.video_script,
                    compliance_report=adset_compliance
                )
                ac._raw_response = adset_creative_raw
                
                # Verify differentiation and absence of duplicates
                if check_creative_similarity(ac, adset_creatives, threshold=0.75):
                    print(f"[INFO] Ad Set {idx} creative copy is similar to other sets or contains duplicates. Regenerating (Attempt {regen_attempt + 1}/{max_regen_attempts})...")
                    continue
                else:
                    break
            else:
                print(f"[WARNING] Could not achieve complete differentiation for Ad Set {idx} after {max_regen_attempts} attempts. Keeping last generation.")

            adset_creatives.append(ac)
            
        first_creative = adset_creatives[0]
        first_raw = getattr(first_creative, "_raw_response", None)
        
        response = HookGenerationResponse(
            category=request.category,
            hooks=first_creative.hooks,
            headlines=first_creative.headlines,
            primary_texts=first_creative.primary_texts,
            ctas=first_creative.ctas,
            inferred_style_note=first_raw.inferred_style_note if first_raw else "Generated per Ad Set targeting.",
            video_script=first_creative.video_script,
            compliance_report=first_creative.compliance_report,
            adsets=generated_adsets,
            adset_creatives=adset_creatives
        )
    else:
        # Single creative generation flow
        inputs = {
            "reference_ads": ad_references,
            "video_script_references": video_references,
            "product_name": request.product_name,
            "product_description": request.product_description,
            "category": request.category,
            "audience": request.audience,
            "language": request.language,
            "offer_angle": request.offer_angle,
            "campaign_objective": request.campaign_objective,
            "platform": request.platform,
            "pain_point": request.pain_point,
            "usp": request.usp,
            "brand_voice": request.brand_voice if request.brand_voice else "Standard brand voice.",
            "cta": request.cta if request.cta else "None specified",
            "location": "General/Global",
            "age_group": "All ages",
            "detailed_targeting": "Broad"
        }
        
        response_raw = None
        for attempt in range(max_attempts):
            try:
                response_raw = chain.invoke(inputs)
                break
            except Exception as e:
                error_str = str(e)
                is_429 = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "ResourceExhausted" in error_str
                is_503 = "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str
                is_timeout = "timeout" in error_str.lower() or isinstance(e, TimeoutError)
                if (is_429 or is_503) and attempt < len(backoff_times):
                    wait_time = backoff_times[attempt]
                    print(f"[RETRY WARNING] Gemini API busy/rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif is_timeout:
                    print("[ERROR] Gemini generation timed out")
                    raise ValueError("Generation took too long. Please try again.")
                else:
                    if is_429 or is_503:
                        print("[ERROR] Gemini quota exceeded")
                        raise ValueError("AI generation limit reached. Please try again shortly.")
                    else:
                        print(f"[ERROR] Gemini generation failed: {e}")
                        raise ValueError("AI service is temporarily unavailable. Please try again.")
                        
        if not response_raw:
            raise ValueError("Failed to generate creative package.")
            
        compliance_result = check_meta_compliance(
            hooks=response_raw.hooks,
            headlines=response_raw.headlines,
            primary_texts=response_raw.primary_texts,
            ctas=response_raw.ctas,
            video_script=response_raw.video_script
        )
        
        response = HookGenerationResponse(
            category=request.category,
            hooks=response_raw.hooks,
            headlines=response_raw.headlines,
            primary_texts=response_raw.primary_texts,
            ctas=response_raw.ctas,
            inferred_style_note=response_raw.inferred_style_note,
            video_script=response_raw.video_script,
            compliance_report=compliance_result,
            adsets=[],
            adset_creatives=None
        )
    
    # 8. Save output and inputs to local database
    try:
        def format_video_script_as_text(video_script_data) -> Optional[str]:
            if not video_script_data:
                return None
            if isinstance(video_script_data, str):
                return video_script_data
            if hasattr(video_script_data, 'dict'):
                data = video_script_data.dict()
            elif isinstance(video_script_data, dict):
                data = video_script_data
            else:
                return str(video_script_data)
                
            hook_text = data.get("hook", "")
            scenes_list = data.get("scenes", [])
            cta_text = data.get("cta", "")
            
            text_parts = []
            text_parts.append(f"Opening Hook (0-5s):\n{hook_text}\n")
            for idx, s in enumerate(scenes_list, 1):
                text_parts.append(f"Scene {idx:02d}:\nVisual: {s.get('scene', '')}\nVoiceover: {s.get('voiceover', '')}\n")
            text_parts.append(f"Closing Screen & CTA (25-30s):\n{cta_text}")
            return "\n".join(text_parts)

        # Prepare database campaign payload
        db_campaign_data = {
            "product_name": request.product_name,
            "product_description": request.product_description,
            "category": request.category,
            "audience": request.audience,
            "language": request.language,
            "offer_angle": request.offer_angle,
            "campaign_objective": request.campaign_objective,
            "pain_point": request.pain_point,
            "usp": request.usp,
            "brand_voice": request.brand_voice,
            "cta": request.cta,
            "platform": request.platform,
            
            "hooks": response.hooks,
            "headlines": response.headlines,
            "primary_texts": response.primary_texts,
            "ctas": response.ctas,
            "video_script": format_video_script_as_text(response.video_script),
            
            "compliance_status": response.compliance_report.status if response.compliance_report else "safe",
            "compliance_issues": [serialize_pydantic(issue) for issue in response.compliance_report.issues] if response.compliance_report and response.compliance_report.issues else [],
            
            # Ad Set Settings
            "generate_adsets": request.generate_adsets,
            "adset_count": request.adset_count,
            "auto_generate_adsets": request.auto_generate_adsets,
            
            # Ad Set creatives list
            "adset_creatives": [serialize_pydantic(ac) for ac in response.adset_creatives] if response.adset_creatives else None
        }
        
        # Insert using standard database SessionLocal
        with SessionLocal() as db:
            crud.create_campaign(db, db_campaign_data)
        print("[INFO] Campaign generated successfully")
    except Exception as db_err:
        print(f"[ERROR] Non-blocking database error: Failed to save generation log via SQLAlchemy. Details: {db_err}")
        
    return response
