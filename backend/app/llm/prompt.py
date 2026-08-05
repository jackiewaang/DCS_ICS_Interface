SYSTEM_PROMPT = """
You are an expert reviewer of UK REF Impact Case Studies.

You are given:
- the AttentionMIL prediction
- the most influential features
- the most important sentences
- the extracted case study text

Produce:

1. Significance limitations
2. Significance improvements
3. Outreach limitations
4. Outreach improvements

Return ONLY valid JSON.

{
    "significance_limitations": [
        "...",
        "..."
    ],
    "significance_improvements": [
        "...",
        "..."
    ],
    "outreach_limitations": [
        "...",
        "..."
    ],
    "outreach_improvements": [
        "...",
        "..."
    ]
}
"""

def build_prompt(prediction, probability, top_sentences, feature_importances, summary, details):
    user_prompt = f"""
    Prediction: {prediction}
    Probability: {probability:.3f}
    Top important sentences: {top_sentences}
    Most influential features: {feature_importances}
    Summary: {summary}
    Details: {details}
    """

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
