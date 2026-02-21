def build_text_response(text: str) -> dict:
    """
    Builds a standard dictionary structure for a text response.
    """
    return {
        "type": "text",
        "content": text
    }
