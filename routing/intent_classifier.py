def classify_intent(text: str) -> str:
    \"\"\"
    Classify the user intent using simple keyword matching or an LLM.
    Currently returns the raw text to be consumed by the Rule Engine.
    \"\"\"
    return text.strip().lower()
