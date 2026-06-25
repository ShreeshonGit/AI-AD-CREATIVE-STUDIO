import re
from typing import List, Dict, Any

# Dictionary mapping flagged bad phrases to exact safer Meta-compliant examples
SUGGESTIONS_MAP = {
    # 1. Personal Attribute Violation
    "are you overweight": "Fitness-focused wellness solutions.",
    "are you depressed": "Wellness-oriented lifestyle support.",
    "are you struggling financially": "Learn financial growth strategies.",
    "do you have diabetes": "Healthy lifestyle support.",
    "are you lonely": "Wellness-focused lifestyle support.",
    "are you unemployed": "Explore better opportunities.",
    
    # 2. Unrealistic or Misleading Claims
    "guaranteed success": "Designed to help you master goals.",
    "instant results": "May improve outcomes over time.",
    "earn money instantly": "Learn income growth strategies.",
    "become rich quickly": "Income learning opportunities.",
    "guaranteed weight loss": "Designed to help support fitness.",
    "guaranteed recovery": "Wellness-focused lifestyle support.",
    
    # 3. Fake Urgency / Manipulative Scarcity
    "only 1 seat left": "Limited seats available.",
    "last chance forever": "Registrations closing soon.",
    "offer expires in 5 minutes": "Registrations closing soon.",
    "act immediately or lose forever": "Limited availability.",
    
    # 4. Medical / Health Claims
    "cure diabetes": "Healthy lifestyle support.",
    "reverse aging": "Wellness-focused aging support.",
    "permanently remove anxiety": "Wellness-oriented support.",
    "lose 10kg in 3 days": "Fitness-oriented training program.",
    
    # 5. Financial Misrepresentation
    "guaranteed income": "Income learning opportunities.",
    "guaranteed profits": "Business growth strategies.",
    "earn ₹1 lakh daily": "Learn strategies to grow your income.",
    "earn 1 lakh daily": "Learn strategies to grow your income.",
    "instant passive income": "Income learning opportunities.",
    
    # 6. Fear-Based Manipulation
    "your life will fail": "Improve your chances.",
    "don’t miss this or regret forever": "Explore better opportunities.",
    "don't miss this or regret forever": "Explore better opportunities.",
    "your future is ruined without this": "Explore better opportunities.",
    
    # 7. Sensational or Clickbait Language
    "shocking secret": "Proven strategies.",
    "unbelievable trick": "Proven strategies.",
    "doctors hate this": "Practical insights.",
    "secret loophole": "Practical insights."
}

def get_safer_suggestion(text: str) -> str:
    """
    Checks if a flagged sentence matches any specific key in our SUGGESTIONS_MAP.
    Falls back to a dynamic rephrasing if no exact match is located.
    """
    cleaned_text = text.lower().strip()
    
    # Try exact or substring key matching
    for key, suggestion in SUGGESTIONS_MAP.items():
        if key in cleaned_text:
            return suggestion
            
    # Generic, high-quality backup rewriter
    return "Focus on the product process, skills, or features in the third-person instead of promising instant results or implying user attributes."

# Standard Meta-compliance policy configurations
COMPLIANCE_RULES: List[Dict[str, Any]] = [
    {
        "id": "META_PERS_ATTR",
        "type": "Personal Attribute Violation",
        "severity": "high_risk",
        "description": "Meta restricts ads implying personal attributes, health struggles, or financial states directly to the user.",
        "patterns": [
            r"\bare\s+you\s+overweight\b",
            r"\bare\s+you\s+depressed\b",
            r"\bare\s+you\s+struggling\s+financially\b",
            r"\bdo\s+you\s+have\s+diabetes\b",
            r"\bare\s+you\s+lonely\b",
            r"\bare\s+you\s+unemployed\b"
        ]
    },
    {
        "id": "META_MISLEADING_CLAIM",
        "type": "Misleading Claims Violation",
        "severity": "high_risk",
        "description": "Meta prohibits absolute guarantees or promises of instant results, which deceive the audience.",
        "patterns": [
            r"\bguaranteed\s+success\b",
            r"\binstant\s+results\b",
            r"\bearn\s+money\s+instantly\b",
            r"\bbecome\s+rich\s+quickly\b",
            r"\bguaranteed\s+weight\s+loss\b",
            r"\bguaranteed\s+recovery\b"
        ]
    },
    {
        "id": "META_FAKE_URGENCY",
        "type": "Manipulative Scarcity Violation",
        "severity": "warning",
        "description": "Manipulative timeline thresholds or last-chance scarcity claims generate synthetic high friction and trigger policy filters.",
        "patterns": [
            r"\bonly\s+1\s+seat\s+left\b",
            r"\blast\s+chance\s+forever\b",
            r"\boffer\s+expires\s+in\s+5\s+minutes\b",
            r"\bact\s+immediately\s+or\s+lose\s+forever\b"
        ]
    },
    {
        "id": "META_HEALTH_CLAIM",
        "type": "Medical Health Claim Violation",
        "severity": "high_risk",
        "description": "Unrealistic health claims, physical age reversals, or rapid weight transformations violate Meta policy directives.",
        "patterns": [
            r"\bcure\s+diabetes\b",
            r"\breverse\s+aging\b",
            r"\bpermanently\s+remove\s+anxiety\b",
            r"\blose\s+10\s*kg\s+in\s+3\s+days\b"
        ]
    },
    {
        "id": "META_FINANCIAL_PROM",
        "type": "Financial Misrepresentation",
        "severity": "high_risk",
        "description": "Get-rich promises or guaranteed income assets are closely audited and restricted by ad networks.",
        "patterns": [
            r"\bguaranteed\s+income\b",
            r"\bguaranteed\s+profits\b",
            r"\bearn\s+₹?1\s*lakh\s+daily\b",
            r"\binstant\s+passive\s+income\b"
        ]
    },
    {
        "id": "META_FEAR_MANIP",
        "type": "Fear-Based Manipulation",
        "severity": "warning",
        "description": "Unnecessary fear triggers or threats of immediate future ruin degrade copy quality and fail policy approvals.",
        "patterns": [
            r"\byour\s+life\s+will\s+fail\b",
            r"\bdon['’]t\s+miss\s+this\s+or\s+regret\s+forever\b",
            r"\byour\s+future\s+is\s+ruined\s+without\s+this\b"
        ]
    },
    {
        "id": "META_CLICKBAIT",
        "type": "Clickbait Language Violation",
        "severity": "warning",
        "description": "Clickbait tricks or claims of shocking doctor secrets provoke artificial curiosity loops and trigger ad filters.",
        "patterns": [
            r"\bshocking\s+secret\b",
            r"\bunbelievable\s+trick\b",
            r"\bdoctors\s+hate\s+this\b",
            r"\bsecret\s+loophole\b"
        ]
    }
]
