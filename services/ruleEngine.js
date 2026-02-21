const userStates = {};

function processMessage(from, text) {
    const lowerText = text.toLowerCase();

    // Initialize state if new user
    if (!userStates[from]) {
        userStates[from] = {
            isNewCustomer: Math.random() > 0.5, // Mocked classification
            step: 'idle',
            escalated: false
        };
        const type = userStates[from].isNewCustomer ? "new" : "existing";
        return `Hello! I see you are a ${type} customer. How can I help you today?`;
    }

    const state = userStates[from];

    if (state.escalated) {
        return "Your case has been escalated to a human agent. They will contact you shortly.";
    }

    // Complaints
    const complaintWords = ['angry', 'complain', 'terrible', 'bad', 'suck', 'dissatisfied', 'hate', 'issue'];
    if (complaintWords.some(word => lowerText.includes(word))) {
        state.escalated = true;
        return "I sincerely apologize for the inconvenience. A human agent will call you shortly to resolve this.";
    }

    // Workflows: Email, Draft name, Money transfer
    if (state.step !== 'idle') {
        if (state.step === 'ask_email') {
            state.email = text;
            state.step = 'idle';
            return "Thank you, I have recorded your email address.";
        } else if (state.step === 'ask_draft_name') {
            state.draftName = text;
            state.step = 'idle';
            return "Thank you, I have saved the draft name.";
        } else if (state.step === 'ask_transfer_amount') {
            state.transferAmount = text;
            state.step = 'idle';
            return "Got it. The money transfer intent has been recorded.";
        }
    }

    if (lowerText.includes('email')) {
        state.step = 'ask_email';
        return "Could you please provide your email address?";
    }
    if (lowerText.includes('draft') || lowerText.includes('name')) {
        state.step = 'ask_draft_name';
        return "What is the draft name you would like to use?";
    }
    if (lowerText.includes('money') || lowerText.includes('transfer')) {
        state.step = 'ask_transfer_amount';
        return "How much money would you like to transfer?";
    }

    // Return null to signify AI should take over
    return null;
}

module.exports = { processMessage };
