import subprocess
import base64
import logging

logger = logging.getLogger(__name__)


def get_ai_response(text: str) -> str:
    """
    Calls the Gemini CLI as a subprocess.
    Uses base64 encoding to avoid shell escaping issues (same approach as original JS bot).
    """
    prompt = (
        f'You are a strict business customer support assistant. '
        f'You ONLY answer questions related to: account services, money transfers, payments, '
        f'KYC/ID verification, email registration, complaints, rates, and general support. '
        f'If the user asks about ANYTHING else (food, entertainment, general knowledge, jokes, etc.), '
        f'you MUST respond with exactly: '
        f'"I\'m sorry, I can only assist with business-related queries. Please type \'help\' to see what I can help you with." '
        f'Do NOT answer off-topic questions under any circumstances. '
        f'The user said: "{text}". '
        f'If they are speaking Punjabi, translate and reply in professional English. '
        f'Keep your reply under 3 sentences.'
    )

    b64_prompt = base64.b64encode(prompt.encode('utf-8')).decode('utf-8')

    # Inline python script that decodes the prompt and calls gemini CLI
    inline_script = (
        "import subprocess, base64, sys\n"
        f"prompt = base64.b64decode('{b64_prompt}').decode('utf-8')\n"
        "result = subprocess.run(['gemini', '-p', prompt], capture_output=True, text=True, shell=True)\n"
        "sys.stdout.write(result.stdout)\n"
        "sys.stderr.write(result.stderr)\n"
        "sys.exit(result.returncode)\n"
    )

    try:
        process = subprocess.run(
            ['python', '-c', inline_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        if process.returncode != 0:
            logger.error(f"Gemini CLI error: {process.stderr}")
            return "I'm sorry, I'm having trouble understanding you right now. Please try again."

        output = process.stdout.strip()
        if not output:
            return "I'm sorry, I couldn't generate a response. Please try rephrasing your message."
        return output

    except subprocess.TimeoutExpired:
        logger.error("Gemini CLI timed out.")
        return "I'm sorry, the request timed out. Please try again."
    except Exception as e:
        logger.error(f"Exception running AI: {e}")
        return "I'm sorry, I'm having trouble understanding you right now."
