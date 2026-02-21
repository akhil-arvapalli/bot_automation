const axios = require('axios');

async function sendWhatsAppMessage(to, message) {
    const token = process.env.WHATSAPP_TOKEN;
    const phoneId = process.env.PHONE_NUMBER_ID;

    if (!token || !phoneId || token === 'your_whatsapp_access_token_here') {
        console.warn(`[Mock WhatsApp Send] To: ${to} | Message: ${message}`);
        return;
    }

    try {
        await axios({
            method: 'POST',
            url: `https://graph.facebook.com/v17.0/${phoneId}/messages`,
            data: {
                messaging_product: 'whatsapp',
                to: to,
                text: { body: message }
            },
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        console.log(`Message successfully sent to ${to}`);
    } catch (error) {
        console.error("Error sending WhatsApp message:");
        console.error(error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    }
}

module.exports = { sendWhatsAppMessage };
