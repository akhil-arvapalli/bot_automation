import logging
import random

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# SESSION STORE (in-memory, keyed by Telegram chat_id)
# ──────────────────────────────────────────────────────────
sessions = {}

# ──────────────────────────────────────────────────────────
# STATES
# ──────────────────────────────────────────────────────────
START               = "START"
COLLECT_FIRST_NAME  = "COLLECT_FIRST_NAME"
COLLECT_LAST_NAME   = "COLLECT_LAST_NAME"
COLLECT_PHONE       = "COLLECT_PHONE"
CONFIRM_PHONE       = "CONFIRM_PHONE"
COLLECT_AMOUNT      = "COLLECT_AMOUNT"
CONFIRM_AMOUNT      = "CONFIRM_AMOUNT"
PAYMENT_SELECTION   = "PAYMENT_SELECTION"
FIRST_TIME_CHECK    = "FIRST_TIME_CHECK"
# KYC states
KYC_FULL_NAME       = "KYC_FULL_NAME"
KYC_PHONE           = "KYC_PHONE"
KYC_EMAIL           = "KYC_EMAIL"
KYC_COMPANY         = "KYC_COMPANY"
KYC_POSITION        = "KYC_POSITION"
KYC_ID_PHOTO        = "KYC_ID_PHOTO"
# Receiver states
RECEIVER_NAME       = "RECEIVER_NAME"
RECEIVER_PHONE      = "RECEIVER_PHONE"
RECEIVER_COMPANY    = "RECEIVER_COMPANY"
RECEIVER_POSITION   = "RECEIVER_POSITION"
RECEIVER_BANK_NAME  = "RECEIVER_BANK_NAME"
RECEIVER_ACCOUNT    = "RECEIVER_ACCOUNT"
RECEIVER_IFSC       = "RECEIVER_IFSC"
RECV_DELIVERY_METHOD = "RECV_DELIVERY_METHOD"
RECV_BANK_DETAILS   = "RECV_BANK_DETAILS"
REFERRAL            = "REFERRAL"
COMPLETED           = "COMPLETED"
ESCALATED           = "ESCALATED"

# ──────────────────────────────────────────────────────────
# CONFIG (exchange rate, fees — easy to update)
# ──────────────────────────────────────────────────────────
EXCHANGE_RATE = 66.76
ETRANSFER_FEE = 6
DEBIT_FEE = 4
OFFICE_ADDRESS = '1900 Clarke Blvd Unit 7'
OFFICE_HOURS = '6pm today'

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


def _is_yes(text: str) -> bool:
    return text.strip().lower() in {'yes', 'yeah', 'yep', 'sure', 'yea', 'y', 'ok', 'okay'}


def _is_no(text: str) -> bool:
    return text.strip().lower() in {'no', 'nah', 'nope', 'n'}


def _new_session() -> dict:
    return {
        'state': START,
        'first_name': None,
        'last_name': None,
        'phone': None,
        'amount': None,
        'amount_num': 0,
        'payment_method': None,
        'is_first_time': None,
        # KYC
        'kyc_name': None,
        'kyc_phone': None,
        'kyc_email': None,
        'kyc_company': None,
        'kyc_position': None,
        'kyc_id_photo': False,
        # Receiver
        'recv_name': None,
        'recv_phone': None,
        'recv_company': None,
        'recv_position': None,
        'recv_bank': None,
        'recv_account': None,
        'recv_ifsc': None,
        'referral': None,
        'ref_number': None,
    }


def _build_rate_breakdown(amount: float) -> str:
    """Build the payment options breakdown like the professional bot."""
    etransfer_recv = (amount - ETRANSFER_FEE) * EXCHANGE_RATE
    debit_recv = (amount - DEBIT_FEE) * EXCHANGE_RATE
    cash_recv = amount * EXCHANGE_RATE

    return (
        f"💰 You want to send: ${amount:,.2f} CAD\n\n"
        f"🏦 Payment Options:\n\n"
        f"E-Transfer:\n"
        f"• You pay: ${amount:,.1f} CAD\n"
        f"• Fee: ${ETRANSFER_FEE} (deducted internally)\n"
        f"• They receive: ₹{etransfer_recv:,.0f} INR\n"
        f"• Rate: {EXCHANGE_RATE}\n\n"
        f"Debit Card:\n"
        f"• You pay: ${amount:,.1f} CAD\n"
        f"• Fee: ${DEBIT_FEE} (deducted internally)\n"
        f"• They receive: ₹{debit_recv:,.0f} INR\n"
        f"• Rate: {EXCHANGE_RATE}\n\n"
        f"Cash/Bank Draft:\n"
        f"• You pay: ${amount:,.1f} CAD\n"
        f"• NO FEE - They receive: ₹{cash_recv:,.0f} INR\n"
        f"• Rate: {EXCHANGE_RATE}\n\n"
        f"Want to send this amount?"
    )


def _gen_ref() -> str:
    return f"RND{random.randint(2000000, 2999999)}"


# ──────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────────────────
def process_message(chat_id: str, text: str) -> str:
    lower = text.strip().lower()

    # ── Reset ──────────────────────────────────────────
    if any(w in lower for w in RESET_WORDS):
        sessions.pop(chat_id, None)
        sessions[chat_id] = _new_session()
        sessions[chat_id]['state'] = COLLECT_FIRST_NAME
        return (
            "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
            "I'm here to help you send money to India - fast and easy.\n\n"
            "What's your name?"
        )

    # ── New user ───────────────────────────────────────
    if chat_id not in sessions:
        sessions[chat_id] = _new_session()
        sessions[chat_id]['state'] = COLLECT_FIRST_NAME
        return (
            "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
            "I'm here to help you send money to India - fast and easy.\n\n"
            "What's your name?"
        )

    s = sessions[chat_id]
    state = s['state']

    # ── Complaint escalation (always check) ────────────
    if any(w in lower for w in COMPLAINT_WORDS):
        s['state'] = ESCALATED
        return (
            "I'm really sorry to hear that. Your case has been escalated to our team.\n"
            "A human agent will reach out to you shortly."
        )

    if state == ESCALATED:
        if _is_ack(lower):
            return "Thank you for your patience. An agent will contact you soon."
        if any(w in lower for w in ['new', 'another', 'send', 'transfer']):
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = COLLECT_FIRST_NAME
            return "Sure! Let's start fresh.\nWhat's your name?"
        return "Your case is with our team. Would you like to start a new transaction instead?"

    # ── Help ───────────────────────────────────────────
    if lower == 'help':
        return (
            "I can help you with:\n"
            "• Sending money to India\n"
            "• Exchange rates\n"
            "• KYC / ID verification\n"
            "• Payment options\n\n"
            "Let's continue where we left off, or type 'restart' to start over."
        )

    # ══════════════════════════════════════════════════
    #  STATE MACHINE
    # ══════════════════════════════════════════════════

    # ── COLLECT_FIRST_NAME ─────────────────────────────
    if state == COLLECT_FIRST_NAME:
        s['first_name'] = text.strip().title()
        s['state'] = COLLECT_LAST_NAME
        return f"Okay {s['first_name']}, and what's your last name?"

    # ── COLLECT_LAST_NAME ──────────────────────────────
    if state == COLLECT_LAST_NAME:
        s['last_name'] = text.strip().title()
        s['state'] = COLLECT_PHONE
        return f"Got it, {s['first_name']} {s['last_name']}! And what's your Canadian phone number? (10 digits)"

    # ── COLLECT_PHONE ──────────────────────────────────
    if state == COLLECT_PHONE:
        cleaned = text.strip().replace(' ', '').replace('-', '').replace('+', '').replace('(', '').replace(')', '')
        if not cleaned.isdigit() or len(cleaned) < 7:
            return "That doesn't look right. Please enter your phone number (digits only, 10 digits)."
        s['phone'] = text.strip()
        s['state'] = CONFIRM_PHONE
        return f"Thanks {s['first_name']}! Is that the number you'll be using to send the e-transfer from?"

    # ── CONFIRM_PHONE ──────────────────────────────────
    if state == CONFIRM_PHONE:
        if _is_yes(lower) or _is_ack(lower):
            s['state'] = COLLECT_AMOUNT
            return f"Perfect! And how much CAD are you planning to send to India today?"
        if _is_no(lower):
            s['state'] = COLLECT_PHONE
            return "No problem! Please enter the correct phone number (10 digits)."
        # They might have typed a new number directly
        cleaned = text.strip().replace(' ', '').replace('-', '').replace('+', '').replace('(', '').replace(')', '')
        if cleaned.isdigit() and len(cleaned) >= 7:
            s['phone'] = text.strip()
            return f"Got it, updated to {text.strip()}. Is this correct?"
        s['state'] = COLLECT_AMOUNT
        return f"Perfect! And how much CAD are you planning to send to India today?"

    # ── COLLECT_AMOUNT ─────────────────────────────────
    if state == COLLECT_AMOUNT:
        # Try to parse amount
        amount_str = text.strip().replace('$', '').replace(',', '').replace('CAD', '').replace('cad', '').strip()
        try:
            amount = float(amount_str)
        except ValueError:
            return "Please enter a valid amount in CAD (e.g., 1000 or 500.50)."
        s['amount'] = text.strip()
        s['amount_num'] = amount
        s['state'] = CONFIRM_AMOUNT
        return _build_rate_breakdown(amount)

    # ── CONFIRM_AMOUNT ─────────────────────────────────
    if state == CONFIRM_AMOUNT:
        if _is_yes(lower) or _is_ack(lower):
            s['state'] = PAYMENT_SELECTION
            return "Awesome! How would you like to pay - e-transfer, debit, cash, or bank draft?"
        if _is_no(lower):
            s['state'] = COLLECT_AMOUNT
            return "No worries! How much CAD would you like to send instead?"
        # They might be adjusting the amount
        amount_str = text.strip().replace('$', '').replace(',', '').replace('CAD', '').replace('cad', '').strip()
        try:
            amount = float(amount_str)
            s['amount'] = text.strip()
            s['amount_num'] = amount
            return _build_rate_breakdown(amount)
        except ValueError:
            pass
        s['state'] = PAYMENT_SELECTION
        return "Awesome! How would you like to pay - e-transfer, debit, cash, or bank draft?"

    # ── PAYMENT_SELECTION ──────────────────────────────
    if state == PAYMENT_SELECTION:
        if any(w in lower for w in ['e-transfer', 'etransfer', 'e transfer', 'interac']):
            s['payment_method'] = 'E-Transfer'
            s['state'] = FIRST_TIME_CHECK
            return "Sure, let's get that started! Have you sent money with us before, or is this your first time?"

        if any(w in lower for w in ['debit', 'card']):
            s['payment_method'] = 'Debit Card'
            s['state'] = FIRST_TIME_CHECK
            return "Sure, let's get that started! Have you sent money with us before, or is this your first time?"

        if any(w in lower for w in ['cash', 'bank draft', 'draft', 'bank']):
            s['payment_method'] = 'Cash/Bank Draft'
            s['state'] = FIRST_TIME_CHECK
            return (
                f"Okay great, so you'll be paying by bank draft! "
                f"Just make it payable to \"RND TRADERS INC.\" and bring it to our office "
                f"at {OFFICE_ADDRESS}. We're open till {OFFICE_HOURS}!\n\n"
                f"Have you sent money with us before, or is this your first time?"
            )

        return "Please choose a payment method: e-transfer, debit, cash, or bank draft?"

    # ── FIRST_TIME_CHECK ───────────────────────────────
    if state == FIRST_TIME_CHECK:
        if any(w in lower for w in ['first', 'new', 'never', 'no', 'nope']):
            s['is_first_time'] = True
            s['state'] = KYC_FULL_NAME
            return "Let's get started! What's your full name?"
        if any(w in lower for w in ['yes', 'yeah', 'before', 'returning', 'existing']):
            s['is_first_time'] = False
            s['state'] = RECEIVER_NAME
            return (
                "Welcome back! ✅\n\n"
                "Let's set up the receiver. What's their full name in India?"
            )
        return "Just to clarify - have you sent money with us before? (yes/no)"

    # ══════════════════════════════════════════════════
    #  KYC FLOW (first-time customers)
    # ══════════════════════════════════════════════════

    # ── KYC_FULL_NAME ──────────────────────────────────
    if state == KYC_FULL_NAME:
        s['kyc_name'] = text.strip().title()
        first = s['kyc_name'].split()[0] if s['kyc_name'] else s['first_name']
        s['state'] = KYC_PHONE
        return f"Thanks, {first}! What's your Canadian phone number? (10 digits)"

    # ── KYC_PHONE ──────────────────────────────────────
    if state == KYC_PHONE:
        s['kyc_phone'] = text.strip()
        s['state'] = KYC_EMAIL
        return "Got it! What's your email? We'll send confirmations there."

    # ── KYC_EMAIL ──────────────────────────────────────
    if state == KYC_EMAIL:
        s['kyc_email'] = text.strip()
        s['state'] = KYC_COMPANY
        return "What company do you work for? (or type \"Self-employed\" / \"Student\")"

    # ── KYC_COMPANY ────────────────────────────────────
    if state == KYC_COMPANY:
        s['kyc_company'] = text.strip()
        s['state'] = KYC_POSITION
        return "And what's your position/job title?"

    # ── KYC_POSITION ───────────────────────────────────
    if state == KYC_POSITION:
        s['kyc_position'] = text.strip()
        s['state'] = KYC_ID_PHOTO
        return "Almost there! Please send a photo of your government-issued ID (Passport, Driver's License, etc.)"

    # ── KYC_ID_PHOTO ───────────────────────────────────
    if state == KYC_ID_PHOTO:
        # Accept photo marker or any text reply
        s['kyc_id_photo'] = True
        s['state'] = RECEIVER_NAME
        return (
            "Got your ID photo! Our team will verify it shortly.\n\n"
            "Let's continue - \u2705 Your details are done! "
            "Now for the person in India - what's their full name?"
        )

    # ══════════════════════════════════════════════════
    #  RECEIVER DETAILS
    # ══════════════════════════════════════════════════

    # ── RECEIVER_NAME ──────────────────────────────────
    if state == RECEIVER_NAME:
        s['recv_name'] = text.strip().title()
        s['state'] = RECEIVER_PHONE
        return "Their phone number in India? (10 digits)"

    # ── RECEIVER_PHONE ─────────────────────────────────
    if state == RECEIVER_PHONE:
        s['recv_phone'] = text.strip()
        s['state'] = RECEIVER_COMPANY
        return "What company do they work for?"

    # ── RECEIVER_COMPANY ───────────────────────────────
    if state == RECEIVER_COMPANY:
        s['recv_company'] = text.strip()
        s['state'] = RECEIVER_POSITION
        return "And what's their position/job title?"

    # ── RECEIVER_POSITION ──────────────────────────────
    if state == RECEIVER_POSITION:
        s['recv_position'] = text.strip()
        s['state'] = RECV_DELIVERY_METHOD
        return (
            "How should the money reach them?\n\n"
            "Type **bank** for Bank Transfer or **home** for Home Delivery."
        )

    # ── RECV_DELIVERY_METHOD ────────────────────────────
    if state == RECV_DELIVERY_METHOD:
        if any(w in lower for w in ['bank', 'transfer', 'account']):
            s['state'] = RECV_BANK_DETAILS
            return (
                "Please share the receiver's bank details in one message:\n\n"
                "\u2022 Bank Name (e.g. SBI, PNB, HDFC)\n"
                "\u2022 Account Number\n"
                "\u2022 IFSC Code"
            )
        if any(w in lower for w in ['home', 'delivery', 'cash']):
            s['state'] = REFERRAL
            return (
                "\u2705 Home delivery selected!\n"
                "We'll arrange delivery to the receiver's address.\n\n"
                "Almost done! Did someone refer you?\n"
                "Type their name or \"no\"."
            )
        return "Please type **bank** for Bank Transfer or **home** for Home Delivery."

    # ── RECV_BANK_DETAILS (one message) ───────────────
    if state == RECV_BANK_DETAILS:
        # Parse bank details from one message
        lines = text.strip().split('\n')
        bank_name = ''
        account = ''
        ifsc = ''
        for line in lines:
            line_clean = line.strip()
            low_line = line_clean.lower()
            if 'bank' in low_line and ':' in low_line:
                bank_name = line_clean.split(':', 1)[1].strip()
            elif 'account' in low_line and ':' in low_line:
                account = line_clean.split(':', 1)[1].strip()
            elif 'ifsc' in low_line and ':' in low_line:
                ifsc = line_clean.split(':', 1)[1].strip()

        # If user didn't follow format, try splitting by lines
        if not bank_name and len(lines) >= 1:
            bank_name = lines[0].strip()
        if not account and len(lines) >= 2:
            account = lines[1].strip()
        if not ifsc and len(lines) >= 3:
            ifsc = lines[2].strip()

        s['recv_bank'] = bank_name.upper() if bank_name else 'N/A'
        s['recv_account'] = account if account else 'N/A'
        s['recv_ifsc'] = ifsc.upper() if ifsc else 'N/A'
        s['state'] = REFERRAL
        return (
            f"\u2705 Bank details saved: \U0001f3e6 {s['recv_bank']},\n"
            f"\U0001f522 {s['recv_account']}, \U0001f3db {s['recv_ifsc']}\n\n"
            "Almost done! Did someone refer you?\n"
            "Type their name or \"no\"."
        )

    # ── REFERRAL ───────────────────────────────────────
    if state == REFERRAL:
        if _is_no(lower):
            s['referral'] = None
        else:
            s['referral'] = text.strip()
        s['ref_number'] = _gen_ref()
        s['state'] = COMPLETED
        return (
            f"Thank you for using our service!\n"
            f"Your reference no: {s['ref_number']}\n"
            f"We are processing your transfer...\n\n"
            f"You'll receive a confirmation shortly. Is there anything else I can help with?"
        )

    # ── COMPLETED ──────────────────────────────────────
    if state == COMPLETED:
        if _is_ack(lower) or _is_no(lower) or 'nothing' in lower or 'bye' in lower:
            return "Thank you for choosing RND Traders! Have a great day! 😊"
        if any(w in lower for w in ['yes', 'another', 'new', 'send', 'transfer', 'more']):
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = COLLECT_AMOUNT
            sessions[chat_id]['first_name'] = s['first_name']
            sessions[chat_id]['last_name'] = s['last_name']
            sessions[chat_id]['phone'] = s['phone']
            return f"Let's go, {s['first_name']}! How much CAD would you like to send this time?"
        return "Would you like to send another transfer or is there anything else? Type 'restart' for a fresh start."

    # ── Fallback (should not happen) ───────────────────
    logger.warning(f"Unknown state '{state}' for {chat_id}, resetting.")
    sessions[chat_id] = _new_session()
    sessions[chat_id]['state'] = COLLECT_FIRST_NAME
    return (
        "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
        "I'm here to help you send money to India - fast and easy.\n\n"
        "What's your name?"
    )
