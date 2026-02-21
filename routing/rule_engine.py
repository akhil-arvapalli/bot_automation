import random

# In-memory store for user states, keyed by Telegram chat_id
user_states = {}

# Keywords that are within the bot's scope (business-related)
IN_SCOPE_KEYWORDS = [
    'email', 'draft', 'money', 'transfer', 'send', 'kyc', 'verify', 'verification',
    'phone', 'contact', 'number', 'help', 'hello', 'hi', 'hey', 'bye', 'goodbye',
    'rate', 'price', 'cost', 'status', 'update', 'cancel', 'reset', 'restart',
    'account', 'payment', 'deposit', 'withdraw', 'transaction', 'reference',
    'support', 'agent', 'complain', 'issue', 'problem', 'angry', 'bad', 'refund',
    'register', 'sign up', 'login', 'password', 'id', 'document', 'card',
    'bank', 'balance', 'invoice', 'receipt', 'service', 'start', 'info',
]

OUT_OF_SCOPE_REPLY = (
    "I'm sorry, I can only assist with business-related queries such as "
    "account services, transfers, KYC, and support. "
    "Please type 'help' to see what I can help you with."
)


def process_message(chat_id: str, text: str):
    """
    Process the incoming message using predefined business rules.
    Returns a string response if a rule matches, otherwise returns None.
    """
    lower_text = text.lower()

    # --- New user: greet and classify ---
    if chat_id not in user_states:
        user_states[chat_id] = {
            'isNewCustomer': random.random() > 0.5,  # Mocked classification
            'step': 'idle',
            'escalated': False,
            'data': {}
        }
        customer_type = "new" if user_states[chat_id]['isNewCustomer'] else "existing"
        return f"Hello! I see you are a {customer_type} customer. How can I help you today?"

    state = user_states[chat_id]

    # --- Escalated: hand off to human agent ---
    if state.get('escalated'):
        return "Your case has been escalated to a human agent. They will contact you shortly."

    # --- Detect complaints and escalate ---
    complaint_words = ['angry', 'complain', 'terrible', 'bad', 'suck', 'dissatisfied', 'hate', 'issue', 'problem', 'worst']
    if any(word in lower_text for word in complaint_words):
        state['escalated'] = True
        return "I sincerely apologize for the inconvenience. A human agent will call you shortly to resolve this."

    # --- Multi-step workflows: collect data step by step ---
    current_step = state.get('step', 'idle')
    if current_step != 'idle':
        if current_step == 'ask_email':
            if '@' not in text:
                return "That doesn't look like a valid email address. Please provide a valid email (e.g., you@example.com)."
            state['data']['email'] = text
            state['step'] = 'idle'
            return f"Thank you! I have recorded your email: {text}"

        elif current_step == 'ask_draft_name':
            state['data']['draftName'] = text
            state['step'] = 'idle'
            return f"Got it! Draft name '{text}' has been saved."

        elif current_step == 'ask_transfer_amount':
            state['data']['transferAmount'] = text
            state['step'] = 'idle'
            return f"Understood. Transfer of {text} has been recorded. Our team will process it shortly."

        elif current_step == 'ask_kyc_id':
            state['data']['kycId'] = text
            state['step'] = 'idle'
            return "Your ID has been submitted for verification. We will get back to you soon."

        elif current_step == 'ask_phone':
            state['data']['phone'] = text
            state['step'] = 'idle'
            return f"Phone number {text} has been recorded."

    # --- Intent detection for starting new workflows ---
    if 'email' in lower_text:
        state['step'] = 'ask_email'
        return "Sure! Could you please provide your email address?"

    if 'draft' in lower_text:
        state['step'] = 'ask_draft_name'
        return "What is the draft name you would like to use?"

    if 'money' in lower_text or 'transfer' in lower_text or 'send' in lower_text:
        state['step'] = 'ask_transfer_amount'
        return "How much money would you like to transfer?"

    if 'kyc' in lower_text or 'verify' in lower_text or 'verification' in lower_text:
        state['step'] = 'ask_kyc_id'
        return "Please provide your ID number for verification."

    if 'phone' in lower_text or 'number' in lower_text or 'contact' in lower_text:
        state['step'] = 'ask_phone'
        return "Please share your phone number."

    # --- FAQ / static responses ---
    if 'hello' in lower_text or 'hi' in lower_text or 'hey' in lower_text:
        return "Hello! How can I assist you today?"

    if 'bye' in lower_text or 'goodbye' in lower_text:
        return "Goodbye! Feel free to reach out if you need anything else."

    if 'help' in lower_text:
        return (
            "I can help you with:\n"
            "• Email registration\n"
            "• Draft name setup\n"
            "• Money transfers\n"
            "• KYC / ID verification\n"
            "• Complaints & support\n\n"
            "Just tell me what you need!"
        )

    if 'rate' in lower_text or 'price' in lower_text or 'cost' in lower_text:
        return "Please visit our website or contact our support team for the latest rates and pricing."

    if 'status' in lower_text or 'update' in lower_text:
        return "Could you share your reference number so I can look up the status for you?"

    if 'cancel' in lower_text:
        state['step'] = 'idle'
        return "No problem! Your current request has been cancelled. What else can I help you with?"

    if 'reset' in lower_text or 'start over' in lower_text or 'restart' in lower_text:
        user_states.pop(chat_id, None)
        return "Your session has been reset. Hello again! How can I help you today?"

    # --- Scope guard: reject out-of-context messages before calling AI ---
    if not any(kw in lower_text for kw in IN_SCOPE_KEYWORDS):
        return OUT_OF_SCOPE_REPLY

    # --- No rule matched but topic seems business-related -> signal AI fallback ---
    return None
