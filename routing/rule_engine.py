import logging
import random
import re

logger = logging.getLogger(__name__)

sessions = {}

START                    = "START"
COLLECT_FIRST_NAME       = "COLLECT_FIRST_NAME"
COLLECT_LAST_NAME        = "COLLECT_LAST_NAME"
COLLECT_PHONE            = "COLLECT_PHONE"
CONFIRM_PHONE            = "CONFIRM_PHONE"
COLLECT_AMOUNT           = "COLLECT_AMOUNT"
CONFIRM_AMOUNT           = "CONFIRM_AMOUNT"
PAYMENT_SELECTION        = "PAYMENT_SELECTION"
FIRST_TIME_CHECK         = "FIRST_TIME_CHECK"
KYC_FULL_NAME            = "KYC_FULL_NAME"
KYC_PHONE                = "KYC_PHONE"
KYC_EMAIL                = "KYC_EMAIL"
KYC_COMPANY              = "KYC_COMPANY"
KYC_POSITION             = "KYC_POSITION"
KYC_ID_PHOTO             = "KYC_ID_PHOTO"
RECEIVER_NAME            = "RECEIVER_NAME"
RECEIVER_PHONE           = "RECEIVER_PHONE"
RECEIVER_COMPANY         = "RECEIVER_COMPANY"
RECEIVER_POSITION        = "RECEIVER_POSITION"
RECEIVER_ID_PHOTO        = "RECEIVER_ID_PHOTO"
RECV_DELIVERY_METHOD     = "RECV_DELIVERY_METHOD"
RECV_BANK_NAME           = "RECV_BANK_NAME"
RECV_BANK_ACCOUNT        = "RECV_BANK_ACCOUNT"
RECV_BANK_IFSC           = "RECV_BANK_IFSC"
RECV_BANK_CONFIRM        = "RECV_BANK_CONFIRM"
REFERRAL                 = "REFERRAL"
REFERRAL_NAME            = "REFERRAL_NAME"
ORDER_SUMMARY            = "ORDER_SUMMARY"
ETRANSFER_INSTRUCTIONS   = "ETRANSFER_INSTRUCTIONS"
AWAITING_SCREENSHOT      = "AWAITING_SCREENSHOT"
COMPLETED                = "COMPLETED"
ESCALATED                = "ESCALATED"

EXCHANGE_RATE  = 66.76
ETRANSFER_FEE  = 6
DEBIT_FEE      = 4
OFFICE_ADDRESS = "1900 Clarke Blvd Unit 7"
OFFICE_HOURS   = "6pm today"

# ── Punjabi keyword mappings ──────────────────────────
PUNJABI_YES = {
    'ਹਾਂ', 'ਹਾਂਜੀ', 'ਜੀ', 'ਜੀ ਹਾਂ', 'ਬਿਲਕੁਲ', 'ਜ਼ਰੂਰ',
    'haanji', 'haan', 'hanji', 'ji', 'ji haan', 'bilkul', 'zaroor',
}

PUNJABI_NO = {
    'ਨਹੀਂ', 'ਨਹੀਂ ਜੀ', 'ਨਾ',
    'nahi', 'nahin', 'nahi ji', 'na',
}

PUNJABI_ACK = {
    'ਠੀਕ', 'ਠੀਕ ਹੈ', 'ਚੰਗਾ', 'ਅੱਛਾ', 'ਸ਼ੁਕਰੀਆ', 'ਧੰਨਵਾਦ',
    'theek', 'theek hai', 'thik', 'thik hai', 'changa', 'accha',
    'shukriya', 'dhannvaad', 'mehrbani',
}

PUNJABI_COMPLAINT = {
    'ਗੁੱਸਾ', 'ਸ਼ਿਕਾਇਤ', 'ਮਾੜਾ', 'ਧੋਖਾ', 'ਫਰਾਡ',
    'gussa', 'shikayat', 'maada', 'dhokha',
}

PUNJABI_RESET = {
    'ਨਵਾਂ', 'ਦੁਬਾਰਾ', 'ਸ਼ੁਰੂ',
    'nava', 'dubara', 'shuru', 'navi transaction',
}

PUNJABI_HELP = {
    'ਮਦਦ', 'ਸਹਾਇਤਾ',
    'madad', 'sahaita',
}

PUNJABI_SEND_MONEY = {
    'ਪੈਸੇ ਭੇਜਣੇ', 'ਪੈਸੇ ਭੇਜਣਾ', 'ਪੈਸੇ', 'ਭੇਜਣੇ',
    'paise bhejna', 'paise bhejne', 'paisa bhejo',
}

ACKNOWLEDGEMENTS = {
    'ok', 'okay', 'yes', 'yeah', 'sure', 'yep', 'alright',
    'got it', 'thanks', 'thank you', 'thankyou', 'thx',
    'cool', 'fine', 'great', 'perfect', 'done', 'noted',
    'good', 'right', 'correct', 'hmm', 'k', 'kk', 'yea',
} | PUNJABI_ACK

COMPLAINT_WORDS = {'angry', 'complain', 'terrible', 'worst', 'suck',
                   'dissatisfied', 'hate', 'fraud', 'scam', 'cheat'} | PUNJABI_COMPLAINT

RESET_WORDS = {'restart', 'start over', 'new transaction', 'reset', 'begin again'} | PUNJABI_RESET

EMAIL_REQUEST_WORDS = {
    'email', 'e-transfer email', 'etransfer email', 'send an email',
    'email for e-transfer', 'email for etransfer', 'what email',
    'which email', 'payment email', 'where to send',
}


def _is_ack(text: str) -> bool:
    return text.strip().lower() in ACKNOWLEDGEMENTS


def _is_yes(text: str) -> bool:
    t = text.strip().lower()
    return t in {'yes', 'yeah', 'yep', 'sure', 'yea', 'y', 'ok', 'okay'} or t in PUNJABI_YES


def _is_no(text: str) -> bool:
    t = text.strip().lower()
    return t in {'no', 'nah', 'nope', 'n'} or t in PUNJABI_NO


def _is_punjabi(text: str) -> bool:
    """Detect if the text contains Punjabi (Gurmukhi) script characters."""
    return bool(re.search(r'[\u0A00-\u0A7F]', text))


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
        'kyc_name': None,
        'kyc_phone': None,
        'kyc_email': None,
        'kyc_company': None,
        'kyc_position': None,
        'kyc_id_photo': False,
        'recv_name': None,
        'recv_phone': None,
        'recv_company': None,
        'recv_position': None,
        'recv_id_photo': False,
        'recv_bank': None,
        'recv_account': None,
        'recv_ifsc': None,
        'referral': None,
        'ref_number': None,
        'etransfer_sent': False,
    }


def _build_rate_breakdown(amount: float) -> str:
    etransfer_recv = (amount - ETRANSFER_FEE) * EXCHANGE_RATE
    debit_recv     = (amount - DEBIT_FEE) * EXCHANGE_RATE
    cash_recv      = amount * EXCHANGE_RATE
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


def _build_etransfer_instructions(amount: float, ref_number: str, phone: str) -> str:
    return (
        f"Send ${amount:,.2f} by e-transfer to:\n"
        f"payments@rndtraders.com\n\n"
        f"Please send from your personal account. If you are sending the payment "
        f"from a business account, we will need the Articles of Incorporation.\n\n"
        f"Name - Remit Payment\n"
        f"Put this reference number in e-transfer message box\n"
        f"Message : {ref_number}- RND TRADERS INC\n\n"
        f"And keep this as security question and answer\n"
        f"Question- Remit\n"
        f"Answer - APL7458RND\n\n"
        f"Send screenshot once done- $6 Charge for each e-transfer\n\n"
        f"Put your phone number in the message so we can match it up. "
        f"Once you've sent it, just let me know!\n\n"
        f"Type *I've Sent* when done, or *Cancel* to change payment method."
    )


def _clean_phone(text: str) -> str:
    return text.strip().replace(' ', '').replace('-', '').replace('+', '').replace('(', '').replace(')', '')


def _validate_phone(text: str) -> bool:
    cleaned = _clean_phone(text)
    return cleaned.isdigit() and len(cleaned) >= 7


def _build_order_summary(s: dict) -> str:
    """Build a full order recap before proceeding to payment."""
    amount = s.get('amount_num', 0)
    method = s.get('payment_method', 'N/A')

    # Calculate INR based on payment method
    if method == 'E-Transfer':
        fee = ETRANSFER_FEE
    elif method == 'Debit Card':
        fee = DEBIT_FEE
    else:
        fee = 0
    inr_amount = (amount - fee) * EXCHANGE_RATE

    summary = (
        f"📋 *Order Summary*\n"
        f"{'─' * 28}\n\n"
        f"👤 *Sender*\n"
        f"• Name: {s.get('first_name', '')} {s.get('last_name', '')}\n"
        f"• Phone: {s.get('phone', 'N/A')}\n\n"
    )

    if s.get('recv_name'):
        summary += (
            f"📩 *Receiver*\n"
            f"• Name: {s.get('recv_name', '')}\n"
            f"• Phone: {s.get('recv_phone', 'N/A')}\n"
        )
        if s.get('recv_bank'):
            summary += (
                f"• Bank: {s.get('recv_bank', '')}\n"
                f"• Account: {s.get('recv_account', '')}\n"
                f"• IFSC: {s.get('recv_ifsc', '')}\n"
            )
        summary += "\n"

    summary += (
        f"💰 *Transfer Details*\n"
        f"• Amount: ${amount:,.2f} CAD\n"
        f"• Payment: {method}\n"
    )
    if fee > 0:
        summary += f"• Fee: ${fee}\n"
    summary += (
        f"• They receive: ₹{inr_amount:,.0f} INR\n"
        f"• Rate: {EXCHANGE_RATE}\n\n"
    )

    if s.get('referral'):
        summary += f"🤝 Referred by: {s['referral']}\n\n"

    summary += (
        f"{'─' * 28}\n"
        f"Does everything look correct? (yes/no)"
    )
    return summary


def _finalize(s: dict) -> str:
    if s.get('payment_method') == 'E-Transfer':
        s['state'] = ETRANSFER_INSTRUCTIONS
        return _build_etransfer_instructions(s['amount_num'], s['ref_number'], s.get('phone', ''))

    s['state'] = COMPLETED
    return (
        f"✅ Transfer Created!\n\n"
        f"Reference Number: {s['ref_number']}\n"
        f"Amount: ${s['amount_num']:,.2f} CAD\n"
        f"Status: Processing ⏳\n\n"
        f"We are processing your transfer and will notify you once it's complete.\n\n"
        f"Is there anything else I can help with?"
    )


def process_message(chat_id: str, text: str) -> str:
    lower = text.strip().lower()
    is_punjabi_msg = _is_punjabi(text)

    # Detect Punjabi send-money intent at any point
    if any(w in lower for w in PUNJABI_SEND_MONEY):
        if chat_id not in sessions or sessions[chat_id]['state'] in (START, COMPLETED):
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = COLLECT_FIRST_NAME
            return (
                "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
                "I'm here to help you send money to India - fast and easy.\n\n"
                "What's your first name?"
            )

    # Detect Punjabi help intent
    if any(w in lower for w in PUNJABI_HELP):
        return (
            "I can help you with:\n"
            "• Sending money to India\n"
            "• Exchange rates\n"
            "• KYC / ID verification\n"
            "• Payment options\n\n"
            "Let's continue where we left off, or type 'restart' to start over."
        )

    if any(w in lower for w in RESET_WORDS):
        sessions[chat_id] = _new_session()
        sessions[chat_id]['state'] = COLLECT_FIRST_NAME
        return (
            "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
            "I'm here to help you send money to India - fast and easy.\n\n"
            "What's your first name?"
        )

    if chat_id not in sessions:
        sessions[chat_id] = _new_session()
        sessions[chat_id]['state'] = COLLECT_FIRST_NAME
        return (
            "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
            "I'm here to help you send money to India - fast and easy.\n\n"
            "What's your first name?"
        )

    s = sessions[chat_id]

    if any(w in lower for w in EMAIL_REQUEST_WORDS):
        if not s.get('ref_number'):
            s['ref_number'] = _gen_ref()
        amount = s.get('amount_num', 0) or 500
        return (
            "RND Traders INC.: Send E-transfer to:\n"
            "payments@rndtraders.com\n\n"
            "Please send from your personal account. If you are sending the payment "
            "from a business account, we will need the Articles of Incorporation.\n\n"
            "Name - Remit Payment\n"
            f"Put this reference number in e-transfer message box\n"
            f"Message : {s['ref_number']}- RND TRADERS INC\n\n"
            "And keep this as security question and answer\n"
            "Question- Remit\n"
            "Answer - APL7458RND\n\n"
            "Send screenshot once done- $6 Charge for each e-transfer"
        )

    if any(w in lower for w in COMPLAINT_WORDS):
        s['state'] = ESCALATED
        return (
            "I'm really sorry to hear that. Your case has been escalated to our team.\n"
            "A human agent will reach out to you shortly."
        )

    state = s['state']

    if state == ESCALATED:
        if _is_ack(lower):
            return "Thank you for your patience. An agent will contact you soon."
        if any(w in lower for w in ['new', 'another', 'send', 'transfer']):
            sessions[chat_id] = _new_session()
            sessions[chat_id]['state'] = COLLECT_FIRST_NAME
            return "Sure! Let's start fresh.\nWhat's your first name?"
        return "Your case is with our team. Would you like to start a new transaction instead?"

    if lower == 'help':
        return (
            "I can help you with:\n"
            "• Sending money to India\n"
            "• Exchange rates\n"
            "• KYC / ID verification\n"
            "• Payment options\n\n"
            "Let's continue where we left off, or type 'restart' to start over."
        )

    # ── STEP 2: Sender identity ────────────────────────

    if state == COLLECT_FIRST_NAME:
        s['first_name'] = text.strip().title()
        s['state'] = COLLECT_LAST_NAME
        return f"Nice to meet you, {s['first_name']}! What's your last name?"

    if state == COLLECT_LAST_NAME:
        s['last_name'] = text.strip().title()
        s['state'] = COLLECT_PHONE
        return (
            f"Great, {s['first_name']} {s['last_name']}! "
            f"What's your Canadian phone number? (10 digits)"
        )

    if state == COLLECT_PHONE:
        if not _validate_phone(text):
            return "That doesn't look right. Please enter your phone number (digits only, at least 10 digits)."
        s['phone'] = text.strip()
        s['state'] = CONFIRM_PHONE
        return (
            f"Thanks! Is {s['phone']} the number you'll be using to send the e-transfer from? (yes/no)"
        )

    if state == CONFIRM_PHONE:
        if _is_yes(lower) or _is_ack(lower):
            s['state'] = COLLECT_AMOUNT
            return "Perfect! How much CAD are you planning to send to India today?"
        if _is_no(lower):
            s['state'] = COLLECT_PHONE
            return "No problem! Please enter the correct Canadian phone number (10 digits)."
        if _validate_phone(text):
            s['phone'] = text.strip()
            return f"Got it, updated to {s['phone']}. Is this correct? (yes/no)"
        s['state'] = COLLECT_AMOUNT
        return "Perfect! How much CAD are you planning to send to India today?"

    # ── STEP 3: Amount entry ───────────────────────────

    if state == COLLECT_AMOUNT:
        amount_str = text.strip().replace('$', '').replace(',', '').replace('CAD', '').replace('cad', '').strip()
        try:
            amount = float(amount_str)
        except ValueError:
            return "Please enter a valid amount in CAD (e.g., 1000 or 500.50)."
        s['amount'] = text.strip()
        s['amount_num'] = amount
        s['state'] = CONFIRM_AMOUNT
        return _build_rate_breakdown(amount)

    if state == CONFIRM_AMOUNT:
        if _is_yes(lower) or _is_ack(lower):
            s['state'] = PAYMENT_SELECTION
            return "How would you like to pay?\n\n• E-Transfer\n• Debit Card\n• Cash\n• Bank Draft"
        if _is_no(lower):
            s['state'] = COLLECT_AMOUNT
            return "No worries! How much CAD would you like to send instead?"
        amount_str = text.strip().replace('$', '').replace(',', '').replace('CAD', '').replace('cad', '').strip()
        try:
            amount = float(amount_str)
            s['amount'] = text.strip()
            s['amount_num'] = amount
            return _build_rate_breakdown(amount)
        except ValueError:
            pass
        s['state'] = PAYMENT_SELECTION
        return "How would you like to pay?\n\n• E-Transfer\n• Debit Card\n• Cash\n• Bank Draft"

    # ── STEP 4: Payment method ─────────────────────────

    if state == PAYMENT_SELECTION:
        if any(w in lower for w in ['e-transfer', 'etransfer', 'e transfer', 'interac']):
            s['payment_method'] = 'E-Transfer'
            s['state'] = FIRST_TIME_CHECK
            return "Sure! Have you sent money with us before, or is this your first time?"

        if any(w in lower for w in ['debit', 'card']):
            s['payment_method'] = 'Debit Card'
            s['state'] = FIRST_TIME_CHECK
            return "Sure! Have you sent money with us before, or is this your first time?"

        if any(w in lower for w in ['cash', 'bank draft', 'draft']):
            s['payment_method'] = 'Cash/Bank Draft'
            s['state'] = FIRST_TIME_CHECK
            return (
                f"Great! Make the bank draft payable to \"RND TRADERS INC.\" and bring it to:\n"
                f"{OFFICE_ADDRESS}\n"
                f"We're open till {OFFICE_HOURS}!\n\n"
                f"Have you sent money with us before, or is this your first time?"
            )

        return "Please choose a payment method: E-Transfer, Debit Card, Cash, or Bank Draft."

    # ── STEP 5: First-time vs returning ───────────────

    if state == FIRST_TIME_CHECK:
        if any(w in lower for w in ['first', 'new', 'never', 'no', 'nope']) or _is_no(lower):
            s['is_first_time'] = True
            s['state'] = KYC_FULL_NAME
            return (
                "No problem! We just need a few details to get you set up.\n\n"
                "What's your full legal name?"
            )
        if any(w in lower for w in ['yes', 'yeah', 'before', 'returning', 'existing', 'yep', 'yea']) or _is_yes(lower):
            s['is_first_time'] = False
            s['state'] = RECEIVER_NAME
            return (
                "Welcome back! ✅\n\n"
                "Now let's set up the receiver. What's their full name in India?"
            )
        return "Just to confirm — have you sent money with us before? (yes / no)"

    # ── STEP 5 cont: KYC for first-time ───────────────

    if state == KYC_FULL_NAME:
        s['kyc_name'] = text.strip().title()
        first = s['kyc_name'].split()[0] if s['kyc_name'] else s['first_name']
        s['state'] = KYC_PHONE
        return f"Thanks, {first}! What's your Canadian phone number? (10 digits)"

    if state == KYC_PHONE:
        if not _validate_phone(text):
            return "That doesn't look right. Please enter your phone number (digits only, at least 10 digits)."
        s['kyc_phone'] = text.strip()
        s['state'] = KYC_EMAIL
        return "Got it! What's your email address? We'll send confirmations there."

    if state == KYC_EMAIL:
        if '@' not in text or '.' not in text:
            return "That doesn't look like a valid email. Please enter your email address."
        s['kyc_email'] = text.strip()
        s['state'] = KYC_COMPANY
        return "What company do you work for? (or type \"Self-employed\" or \"Student\")"

    if state == KYC_COMPANY:
        s['kyc_company'] = text.strip()
        s['state'] = KYC_POSITION
        return "And what's your position or job title?"

    if state == KYC_POSITION:
        s['kyc_position'] = text.strip()
        s['state'] = KYC_ID_PHOTO
        return (
            "Almost there! Please send a photo of your Canadian government-issued ID.\n"
            "(Passport, Driver's License, etc.)\n\n"
            "We cannot proceed until the photo is received."
        )

    if state == KYC_ID_PHOTO:
        s['kyc_id_photo'] = True
        s['state'] = RECEIVER_NAME
        return (
            "✅ ID photo received! Our team will verify it shortly.\n\n"
            "Now let's set up the receiver details.\n"
            "What's the receiver's full name in India?"
        )

    # ── STEP 6: Receiver details ───────────────────────

    if state == RECEIVER_NAME:
        s['recv_name'] = text.strip().title()
        s['state'] = RECEIVER_PHONE
        return "What's their phone number in India? (10 digits)"

    if state == RECEIVER_PHONE:
        if not _validate_phone(text):
            return "That doesn't look right. Please enter their Indian phone number (digits only)."
        s['recv_phone'] = text.strip()
        s['state'] = RECEIVER_COMPANY
        return "What company do they work for? (or type \"N/A\" if not applicable)"

    if state == RECEIVER_COMPANY:
        s['recv_company'] = text.strip()
        s['state'] = RECEIVER_POSITION
        return "And what's their position or job title?"

    if state == RECEIVER_POSITION:
        s['recv_position'] = text.strip()
        s['state'] = RECEIVER_ID_PHOTO
        return (
            "Please send a photo of the receiver's Aadhaar card or Passport.\n"
            "(If Aadhaar, please send both front and back.)\n\n"
            "We cannot proceed until the photo is received."
        )

    if state == RECEIVER_ID_PHOTO:
        s['recv_id_photo'] = True
        s['state'] = RECV_DELIVERY_METHOD
        return (
            "✅ Receiver ID received!\n\n"
            "How should the money reach them?\n\n"
            "• Type **bank** for Bank Transfer\n"
            "• Type **home** for Home Delivery"
        )

    # ── STEP 7: Delivery method ────────────────────────

    if state == RECV_DELIVERY_METHOD:
        if any(w in lower for w in ['bank', 'transfer', 'account']):
            s['state'] = RECV_BANK_NAME
            return "What is the receiver's bank name? (e.g. SBI, HDFC, PNB)"
        if any(w in lower for w in ['home', 'delivery', 'cash']):
            s['state'] = REFERRAL
            return (
                "✅ Home delivery selected!\n"
                "We'll arrange delivery to the receiver's address.\n\n"
                "Did someone refer you to RND Traders?\n"
                "Type their name, or \"no\"."
            )
        return "Please type **bank** for Bank Transfer or **home** for Home Delivery."

    if state == RECV_BANK_NAME:
        s['recv_bank'] = text.strip().upper()
        s['state'] = RECV_BANK_ACCOUNT
        return "What is the receiver's account number?"

    if state == RECV_BANK_ACCOUNT:
        s['recv_account'] = text.strip()
        s['state'] = RECV_BANK_IFSC
        return "What is the IFSC code for their branch?"

    if state == RECV_BANK_IFSC:
        s['recv_ifsc'] = text.strip().upper()
        s['state'] = RECV_BANK_CONFIRM
        return (
            f"Here are the bank details I've saved:\n\n"
            f"🏦 Bank: {s['recv_bank']}\n"
            f"🔢 Account: {s['recv_account']}\n"
            f"🏛 IFSC: {s['recv_ifsc']}\n\n"
            f"Is everything correct? (yes/no)"
        )

    if state == RECV_BANK_CONFIRM:
        if _is_yes(lower) or _is_ack(lower):
            s['state'] = REFERRAL
            return (
                "✅ Bank details confirmed!\n\n"
                "Did someone refer you to RND Traders?\n"
                "Type their name, or \"no\"."
            )
        if _is_no(lower):
            s['state'] = RECV_BANK_NAME
            return "No problem! Let's re-enter the bank details.\nWhat is the receiver's bank name?"
        s['state'] = REFERRAL
        return (
            "✅ Bank details confirmed!\n\n"
            "Did someone refer you to RND Traders?\n"
            "Type their name, or \"no\"."
        )

    # ── STEP 8: Referral ───────────────────────────────

    if state == REFERRAL:
        if _is_no(lower):
            s['referral'] = None
        else:
            s['referral'] = text.strip()
        s['ref_number'] = _gen_ref()
        s['state'] = ORDER_SUMMARY
        return _build_order_summary(s)

    # ── STEP 8b: Order Summary ────────────────────────

    if state == ORDER_SUMMARY:
        if _is_yes(lower) or _is_ack(lower):
            return _finalize(s)
        if _is_no(lower):
            # Let them restart from amount
            s['state'] = COLLECT_AMOUNT
            return "No problem! Let's redo this. How much CAD would you like to send?"
        # If they typed something else, treat as confirmation
        return _finalize(s)

    # ── STEP 9: E-Transfer instructions ───────────────

    if state == ETRANSFER_INSTRUCTIONS:
        if any(w in lower for w in ["i've sent", 'ive sent', 'i sent', 'sent', 'done', 'i have sent']):
            s['etransfer_sent'] = True
            s['state'] = AWAITING_SCREENSHOT
            return (
                "Great! Please send a screenshot of the e-transfer confirmation "
                "so we can verify and process your transfer."
            )
        if any(w in lower for w in ['cancel', 'back', 'change']):
            s['state'] = PAYMENT_SELECTION
            return "No problem! How would you like to pay instead?\n\n• E-Transfer\n• Debit Card\n• Cash\n• Bank Draft"
        return _build_etransfer_instructions(s['amount_num'], s['ref_number'], s.get('phone', ''))

    if state == AWAITING_SCREENSHOT:
        inr_amount = (s['amount_num'] - ETRANSFER_FEE) * EXCHANGE_RATE
        s['state'] = COMPLETED
        return (
            f"✅ Transfer created!\n\n"
            f"Reference Number: {s['ref_number']}\n"
            f"${s['amount_num']:,.2f} CAD → ₹{inr_amount:,.0f} INR\n\n"
            f"We'll keep you posted on the progress!\n\n"
            f"Is there anything else I can help with?"
        )

    if state == COMPLETED:
        if _is_ack(lower) or _is_no(lower) or 'nothing' in lower or 'bye' in lower:
            return "Thank you for choosing RND Traders! Have a great day! 😊"
        if any(w in lower for w in ['yes', 'another', 'new', 'send', 'transfer', 'more']):
            prev = {k: s[k] for k in ('first_name', 'last_name', 'phone')}
            sessions[chat_id] = _new_session()
            sessions[chat_id].update(prev)
            sessions[chat_id]['state'] = COLLECT_AMOUNT
            return f"Let's go, {prev['first_name']}! How much CAD would you like to send this time?"
        if any(w in lower for w in ['track', 'tracking', 'status']):
            return (
                f"Your transfer reference: {s['ref_number']}\n"
                f"Status: Processing ⏳\n\n"
                f"We'll notify you once it's delivered!"
            )
        return "Would you like to send another transfer? Type 'restart' for a fresh start."

    logger.warning(f"Unknown state '{state}' for {chat_id}, resetting.")
    sessions[chat_id] = _new_session()
    sessions[chat_id]['state'] = COLLECT_FIRST_NAME
    return (
        "Hey there! Welcome to RND Traders 🇨🇦🇮🇳\n\n"
        "I'm here to help you send money to India - fast and easy.\n\n"
        "What's your first name?"
    )
