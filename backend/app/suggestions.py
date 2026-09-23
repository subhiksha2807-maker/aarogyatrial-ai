from __future__ import annotations

DEMO_TERMINOLOGY = {
    "Gastrointestinal discomfort": ["nausea", "vomit", "stomach", "abdominal", "diarrhea", "loose stool"],
    "Headache or dizziness": ["headache", "dizzy", "dizziness", "lightheaded", "vertigo"],
    "Skin irritation": ["rash", "itch", "redness", "hives", "skin irritation"],
    "Fatigue or weakness": ["fatigue", "tired", "weakness", "weak", "exhausted"],
}


def suggest_category(narrative: str) -> tuple[str, str]:
    lowered = narrative.lower()
    matches: list[tuple[str, list[str]]] = []
    for category, terms in DEMO_TERMINOLOGY.items():
        found = [term for term in terms if term in lowered]
        if found:
            matches.append((category, found))
    if len(matches) != 1:
        reason = "No demo terminology keywords matched." if not matches else "Keywords matched more than one demo category."
        return "Needs manual review", reason
    category, found = matches[0]
    return category, f"Matched demo keyword(s): {', '.join(found)}."

