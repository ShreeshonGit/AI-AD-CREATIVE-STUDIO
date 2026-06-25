import re
from typing import List
from backend.schemas import ComplianceResult

# Banned terms and their specific descriptions to trigger clear warning prompts
BANNED_PATTERNS = [
    (r"\bguaranteed\b", "Manipulative claim using the absolute term 'guaranteed' which violates ad policy guidelines."),
    (r"\binstant cure\b", "High-risk medical assertion suggesting an 'instant cure'."),
    (r"\b100%\s*(result|correct|success|guarantee)\b", "Suspicious claim promising a '100%' outcome."),
    (r"\blose\s*\d+\s*kg\b", "Unrealistic weight-loss promise violating standard wellness ad policy."),
    (r"\bovernight\b", "Timeframe manipulation claiming results 'overnight'."),
    (r"\bmake\s*money\s*(quick|fast|easy)\b", "Get-rich-quick claims which are flagged by ad compliance filters."),
    (r"\bpassive\s*income\b", "Potential policy violation related to unsolicited financial opportunities ('passive income').")
]

def check_ad_compliance(
    hooks: List[str],
    headlines: List[str],
    primary_texts: List[str],
    ctas: List[str]
) -> ComplianceResult:
    """
    Scans generated ad materials (hooks, headlines, primary texts, CTAs) for banned terminology,
    ad network policy risks, or manipulative phrasing.
    """
    warnings = []
    
    # Consolidate all generated text for inspection
    all_texts = []
    all_texts.extend(hooks)
    all_texts.extend(headlines)
    all_texts.extend(primary_texts)
    all_texts.extend(ctas)
    
    for text in all_texts:
        if not text:
            continue
        # Case insensitive regex match for each pattern
        for pattern, warning_msg in BANNED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Ensure each warning is unique in the list
                if warning_msg not in warnings:
                    warnings.append(warning_msg)
                    
    status = "WARNING" if warnings else "PASSED"
    return ComplianceResult(status=status, warnings=warnings)
