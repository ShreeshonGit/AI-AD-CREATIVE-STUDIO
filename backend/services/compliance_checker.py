import re
from typing import List, Optional, Any
from backend.schemas import ComplianceIssue, MetaComplianceReport
from backend.services.compliance_rules import COMPLIANCE_RULES, get_safer_suggestion

def check_meta_compliance(
    hooks: List[str],
    headlines: List[str],
    primary_texts: List[str],
    ctas: List[str],
    video_script: Optional[Any] = None
) -> MetaComplianceReport:
    """
    Analyzes Hooks, Headlines, Primary Texts, CTAs, and optional Video Scripts
    for potential Meta advertising policy violations, outputting structured issues
    and actionable safe rewrite suggestions.
    """
    issues = []
    
    # Bundle all outputs with labels to identify where issues occur
    all_elements = []
    for item in hooks:
        all_elements.append(("Hook", item))
    for item in headlines:
        all_elements.append(("Headline", item))
    for item in primary_texts:
        all_elements.append(("Primary Text", item))
    for item in ctas:
        all_elements.append(("CTA Variation", item))
        
    # Append video script components if present
    if video_script:
        # Check main hook
        v_hook = getattr(video_script, "hook", "") or ""
        if isinstance(v_hook, str) and v_hook:
            all_elements.append(("Video Script Hook", v_hook))
            
        # Check scene segments
        v_scenes = getattr(video_script, "scenes", []) or []
        for s_idx, scene in enumerate(v_scenes, 1):
            s_scene = getattr(scene, "scene", "") or ""
            s_vo = getattr(scene, "voiceover", "") or ""
            if isinstance(s_scene, str) and s_scene:
                all_elements.append((f"Video Scene {s_idx} Visual", s_scene))
            if isinstance(s_vo, str) and s_vo:
                all_elements.append((f"Video Scene {s_idx} Voiceover", s_vo))
                
        # Check closing CTA
        v_cta = getattr(video_script, "cta", "") or ""
        if isinstance(v_cta, str) and v_cta:
            all_elements.append(("Video Script CTA", v_cta))
        
    for label, text in all_elements:
        if not text:
            continue
            
        # Inspect text against all modular rules
        for rule in COMPLIANCE_RULES:
            rule_id = rule["id"]
            rule_type = rule["type"]
            severity = rule["severity"]
            description = rule["description"]
            patterns = rule["patterns"]
            
            for pattern in patterns:
                # Check for regex match in the text segment
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    matched_str = match.group(0)
                    # Trigger the suggester to create a safer rewrite
                    suggestion = get_safer_suggestion(matched_str)
                    
                    # Create and append the structured issue finding
                    issues.append(
                        ComplianceIssue(
                            rule_id=rule_id,
                            severity=severity,
                            type=rule_type,
                            text=f"[{label}] \"{text}\"",
                            suggestion=suggestion
                        )
                    )
                    # Break to prevent duplicate issue triggers for the same rule on the same text
                    break
                    
    # Resolve aggregate status rating in lowercase exactly as requested
    status = "safe"
    for issue in issues:
        if issue.severity == "high_risk":
            status = "high_risk"
            break
        elif issue.severity == "warning":
            status = "warning"
            
    return MetaComplianceReport(status=status, issues=issues)
