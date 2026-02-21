import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# SESSION STORE  (in-memory, keyed by Telegram chat_id)
# ──────────────────────────────────────────────────────────
sessions = {}

# ──────────────────────────────────────────────────────────
# STATE CONSTANTS
# ──────────────────────────────────────────────────────────
START              = "START"
COLLECT_NAME       = "COLLECT_NAME"
COLLECT_PHONE      = "COLLECT_PHONE"
COLLECT_EMAIL      = "COLLECT_EMAIL"
SERVICE_SELECTION   = "SERVICE_SELECTION"
COLLECT_AMOUNT     = "COLLECT_AMOUNT"
PAYMENT_SELECTION  = "PAYMENT_SELECTION"
RECEIVER_DETAILS   = "RECEIVER_DETAILS"
KYC_PENDING        = "KYC_PENDING"
KYC_SUBMITTED      = "KYC_SUBMITTED"
PROCESSING         = "PROCESSING"
COMPLETED          = "COMPLETED"
ESCALATED          = "ESCALATED"
AWAITING_FOLLOWUP  = "AWAITING_FOLLOWUP"

# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
ACKNOWLEDGEMENTS = {'ok', 'okay', 'yes', 'yeah', 'sure', 'yep', 'alright',
                     'got it', 'thanks', 'thank you', 'thankyou', 'thx',
                     'cool', 'fine', 'great', 'perfect', 'done', 'noted',
                     'good', 'right', 'correct', 'hmm', 'k', 'kk', 'yea'}

COMPLAINT_WORDS = {'angry', 'complain', 'terrible', 'worst', 'suck',
                   'dissatisfied', 'hate', 'fraud', 'scam', 'cheat'}

RESET_WORDS = {'restart', 'start over', 'new transaction', 'reset', 'begin again'}

def _is_ack(text: str) -> bool:
    return text.strip().lower() in ACKNOWLEDGEMENTS

def _new_session() -> dict:
    return {
        'state': START,
        'name': None,
        'phone': None,
        'email': None,
        'service': None,
        'amount': None,
        'payment_method': None,
        'receiver': None,
        'kyc_id': None,
    }

def _summary(s: dict) -> str:
    """Build a quick summary of collected info."""
    parts = []
    if s.get('name'):    parts.append(f"Name: {s['name']}")
    if s.get('phone'):   parts.append(f"Phone: {s['phone']}")
    if s.get('email'):   parts.append(f"Email: {s['email']}")
    if s.get('service'): parts.append(f"Service: {s['service']}")
    if s.get('amount'):  parts.append(f"Amount: {s['amount']}")
    return "\n".join(parts) if parts else ""


# ──────────────────────────────────────────────────────────
# MAIN ENTRY POINT  (called from main.py)
# ──────────────────────────────────────────────────────────
def process_message(chat_id: str, text: str) -> str:
    """
    Stateful conversation handler.
    Always returns a string — never returns None.
    One question at a time, acknowledges input, then moves forward.
    """
    lower = text.strip().lower()

    # ── Reset ──────────────────────────────────────────
    if any(w in lower for w in RESET_WORDS):
        sessions.pop(chat_id, None)
        return "No problem! Starting fresh.\n\nHi there! I'm your remittance assistant. What's your name?"

    # ── New user / first message ───────────────────────
    if chat_id not in sessions:
        sessions[chat_id] = _new_session()
        sessions[chat_id]['state'] = COLLECT_NAME
        return (
            "Welcome! I'm your personal remittance assistant.\n"
            "I can help you with money transfers, KYC verification, account services, and more.\n\n"
            "To get started, may I know your name?"
        )

    s = sessions[chat_id]
    state = s['state']

    # ── Escalation (always check first) ────────────────
    if any(w in lower for w in COMPLAINT_WORDS):
        s['state'] = ESCALATED
        return (
            "I'm really sorry to hear that. Your case has been escalated to our support team.\n"
            "A human agent will reach out to you shortly. Thank you for your patience."
        )

    if state == ESCALATED:
        if _is_ack(lower):
            return "Thank you for your patience. An agent will contact you soon. Is there anything else I can help with?"
        if 'new' in lower or 'another' in lower or 'else' in lower:
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = COLLECT_NAME
            return "Sure! Let's start fresh.\nMay I know your name?"
        return "Your case is with our support team. They'll reach out shortly. Would you like to start a new transaction instead?"

    # ── Help at any point ──────────────────────────────
    if lower == 'help':
        return (
            "Here's what I can help you with:\n"
            "• Money transfers & remittances\n"
            "• KYC / ID verification\n"
            "• Account registration\n"
            "• Rate enquiries\n"
            "• Complaints & support\n\n"
            "Just tell me what you need, or we can continue where we left off."
        )

    # ══════════════════════════════════════════════════
    #  STATE MACHINE
    # ══════════════════════════════════════════════════

    # ── COLLECT_NAME ───────────────────────────────────
    if state == COLLECT_NAME:
        s['name'] = text.strip().title()
        s['state'] = COLLECT_PHONE
        return f"Nice to meet you, {s['name']}! Could you share your phone number?"

    # ── COLLECT_PHONE ──────────────────────────────────
    if state == COLLECT_PHONE:
        cleaned = text.strip().replace(' ', '').replace('-', '').replace('+', '')
        if not cleaned.isdigit() or len(cleaned) < 7:
            return "That doesn't look like a valid phone number. Please enter your phone number (digits only)."
        s['phone'] = text.strip()
        s['state'] = SERVICE_SELECTION
        return (
            f"Got it, {s['name']}! Phone number recorded.\n\n"
            "What would you like to do today?\n"
            "1. Send money / Transfer\n"
            "2. KYC / ID Verification\n"
            "3. Check rates\n"
            "4. Account inquiry\n"
            "5. Something else"
        )

    # ── SERVICE_SELECTION ──────────────────────────────
    if state == SERVICE_SELECTION:
        if any(w in lower for w in ['1', 'send', 'money', 'transfer', 'remit']):
            s['service'] = 'money_transfer'
            s['state'] = COLLECT_AMOUNT
            return "Sure! How much would you like to send? (Please enter the amount)"

        if any(w in lower for w in ['2', 'kyc', 'verify', 'verification', 'id']):
            s['service'] = 'kyc'
            s['state'] = KYC_PENDING
            return "Let's get your identity verified.\nPlease provide your ID number (e.g., Aadhaar, Passport, or PAN)."

        if any(w in lower for w in ['3', 'rate', 'rates', 'price', 'cost', 'exchange']):
            s['service'] = 'rates'
            s['state'] = AWAITING_FOLLOWUP
            return (
                "Here are today's indicative rates:\n"
                "• USD → INR: 83.20\n"
                "• GBP → INR: 105.50\n"
                "• EUR → INR: 90.10\n\n"
                "Would you like to proceed with a transfer, or is there anything else?"
            )

        if any(w in lower for w in ['4', 'account', 'balance', 'inquiry']):
            s['service'] = 'account'
            s['state'] = COLLECT_EMAIL
            return "Sure! Could you share the email address linked to your account?"

        if any(w in lower for w in ['5', 'else', 'other', 'something']):
            s['state'] = AWAITING_FOLLOWUP
            return "No problem! Just tell me what you need and I'll do my best to help."

        # Didn't match a numbered option — gentle nudge
        if _is_ack(lower):
            return (
                "Great! So what would you like to do?\n"
                "1. Send money\n"
                "2. KYC / Verification\n"
                "3. Check rates\n"
                "4. Account inquiry\n"
                "5. Something else"
            )

        return (
            "I didn't quite catch that. Could you pick one of these?\n"
            "1. Send money\n"
            "2. KYC / Verification\n"
            "3. Check rates\n"
            "4. Account inquiry\n"
            "5. Something else"
        )

    # ── COLLECT_EMAIL ──────────────────────────────────
    if state == COLLECT_EMAIL:
        if '@' not in text:
            return "That doesn't look like a valid email. Could you please enter your email address?"
        s['email'] = text.strip()
        s['state'] = AWAITING_FOLLOWUP
        return (
            f"Thank you! Email {s['email']} has been recorded.\n"
            "Is there anything else you'd like me to help with?"
        )

    # ── COLLECT_AMOUNT ─────────────────────────────────
    if state == COLLECT_AMOUNT:
        s['amount'] = text.strip()
        s['state'] = PAYMENT_SELECTION
        return (
            f"Got it — {s['amount']}.\n\n"
            "How would you like to pay?\n"
            "1. Bank transfer\n"
            "2. UPI\n"
            "3. Card payment\n"
            "4. Cash deposit"
        )

    # ── PAYMENT_SELECTION ──────────────────────────────
    if state == PAYMENT_SELECTION:
        methods = {
            '1': 'Bank Transfer', 'bank': 'Bank Transfer',
            '2': 'UPI', 'upi': 'UPI',
            '3': 'Card', 'card': 'Card Payment',
            '4': 'Cash', 'cash': 'Cash Deposit',
        }
        matched = None
        for key, val in methods.items():
            if key in lower:
                matched = val
                break

        if not matched:
            if _is_ack(lower):
                return "Which payment method would you prefer?\n1. Bank transfer\n2. UPI\n3. Card\n4. Cash deposit"
            return "Please select a payment method:\n1. Bank transfer\n2. UPI\n3. Card\n4. Cash deposit"

        s['payment_method'] = matched
        s['state'] = RECEIVER_DETAILS
        return (
            f"Payment via {matched} — noted!\n\n"
            "Now, please share the receiver's name or account details."
        )

    # ── RECEIVER_DETAILS ───────────────────────────────
    if state == RECEIVER_DETAILS:
        s['receiver'] = text.strip()
        s['state'] = PROCESSING
        summary = _summary(s)
        return (
            f"Here's a summary of your transaction:\n"
            f"{summary}\n"
            f"Receiver: {s['receiver']}\n"
            f"Payment: {s['payment_method']}\n\n"
            "Everything look correct? Type 'yes' to confirm or 'cancel' to start over."
        )

    # ── PROCESSING (confirmation step) ─────────────────
    if state == PROCESSING:
        if 'cancel' in lower or 'no' in lower:
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = SERVICE_SELECTION
            return "Transaction cancelled. What would you like to do instead?\n1. Send money\n2. KYC\n3. Check rates\n4. Account inquiry"

        if _is_ack(lower) or 'yes' in lower or 'confirm' in lower:
            s['state'] = COMPLETED
            return (
                "Your transaction has been submitted successfully! 🎉\n"
                "Reference: #TXN" + str(hash(chat_id))[-6:] + "\n\n"
                "We'll send you a confirmation shortly.\n"
                "Is there anything else I can help you with?"
            )

        return "Just to confirm — shall I go ahead and process this transaction? (yes/no)"

    # ── KYC_PENDING ────────────────────────────────────
    if state == KYC_PENDING:
        s['kyc_id'] = text.strip()
        s['state'] = KYC_SUBMITTED
        return (
            f"Thanks! I've submitted your ID ({s['kyc_id']}) for verification.\n"
            "We'll notify you once it's approved.\n"
            "Is there anything else you'd like help with?"
        )

    # ── KYC_SUBMITTED ──────────────────────────────────
    if state == KYC_SUBMITTED:
        if _is_ack(lower):
            s['state'] = AWAITING_FOLLOWUP
            return "You're all set! We're processing your verification now. I'll update you shortly.\nAnything else I can help with?"
        if any(w in lower for w in ['send', 'money', 'transfer']):
            s['state'] = COLLECT_AMOUNT
            s['service'] = 'money_transfer'
            return "Sure! How much would you like to send?"
        if 'status' in lower:
            return "Your KYC is being reviewed. We'll notify you as soon as it's approved. Hang tight!"
        s['state'] = AWAITING_FOLLOWUP
        return "Your verification is being processed. Would you like to start a money transfer while you wait, or something else?"

    # ── COMPLETED ──────────────────────────────────────
    if state == COMPLETED:
        if _is_ack(lower) or 'no' in lower or 'nothing' in lower or 'bye' in lower:
            s['state'] = AWAITING_FOLLOWUP
            return "Thank you for using our service! Feel free to message me anytime you need help. Have a great day! 😊"
        if any(w in lower for w in ['yes', 'another', 'new', 'more', 'send', 'transfer']):
            s['state'] = SERVICE_SELECTION
            return (
                "Let's go! What would you like to do?\n"
                "1. Send money\n"
                "2. KYC / Verification\n"
                "3. Check rates\n"
                "4. Account inquiry"
            )
        s['state'] = SERVICE_SELECTION
        return (
            "What else can I help you with?\n"
            "1. Send money\n"
            "2. KYC / Verification\n"
            "3. Check rates\n"
            "4. Account inquiry"
        )

    # ── AWAITING_FOLLOWUP ──────────────────────────────
    if state == AWAITING_FOLLOWUP:
        if _is_ack(lower) or 'no' in lower or 'nothing' in lower or 'bye' in lower:
            return "No worries! I'm here whenever you need. Have a great day! 😊"
        if any(w in lower for w in ['yes', 'send', 'money', 'transfer', 'remit']):
            s['state'] = COLLECT_AMOUNT
            s['service'] = 'money_transfer'
            return "Sure! How much would you like to send?"
        if any(w in lower for w in ['kyc', 'verify', 'id', 'verification']):
            s['state'] = KYC_PENDING
            s['service'] = 'kyc'
            return "Let's get you verified. Please share your ID number."
        if any(w in lower for w in ['rate', 'rates', 'exchange', 'price']):
            return (
                "Today's indicative rates:\n"
                "• USD → INR: 83.20\n"
                "• GBP → INR: 105.50\n"
                "• EUR → INR: 90.10\n\n"
                "Shall I start a transfer for you?"
            )
        if any(w in lower for w in ['account', 'balance', 'email']):
            s['state'] = COLLECT_EMAIL
            return "Sure! Could you share the email linked to your account?"
        # Generic follow-up — stay in state, don't dump disclaimers
        s['state'] = SERVICE_SELECTION
        return (
            "I'd love to help! What would you like to do?\n"
            "1. Send money\n"
            "2. KYC / Verification\n"
            "3. Check rates\n"
            "4. Account inquiry\n"
            "5. Something else"
        )

    # ── Fallback (should rarely be reached) ────────────
    logger.warning(f"Unknown state '{state}' for chat {chat_id}, resetting to service selection.")
    s['state'] = SERVICE_SELECTION
    return (
        "Let me help you! What would you like to do?\n"
        "1. Send money\n"
        "2. KYC / Verification\n"
        "3. Check rates\n"
        "4. Account inquiry"
    )
