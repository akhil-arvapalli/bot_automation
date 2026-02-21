const express = require('express');
const router = express.Router();
const { processMessage } = require('../services/ruleEngine');
const { getAIResponse } = require('../services/aiFallback');
const { sendWhatsAppMessage } = require('../services/whatsapp');

// Webhook Verification
router.get('/', (req, res) => {
    const verify_token = process.env.VERIFY_TOKEN;
    let mode = req.query['hub.mode'];
    let token = req.query['hub.verify_token'];
    let challenge = req.query['hub.challenge'];

    if (mode && token) {
        if (mode === 'subscribe' && token === verify_token) {
            console.log('WEBHOOK_VERIFIED');
            res.status(200).send(challenge);
        } else {
            res.sendStatus(403);
        }
    } else {
        res.sendStatus(400);
    }
});

// Incoming Messages Handler
router.post('/', async (req, res) => {
    let body = req.body;

    // Check if this is an event from a page subscription
    if (body.object) {
        if (body.entry &&
            body.entry[0].changes &&
            body.entry[0].changes[0] &&
            body.entry[0].changes[0].value.messages &&
            body.entry[0].changes[0].value.messages[0]) {

            let msg = body.entry[0].changes[0].value.messages[0];
            let from = msg.from; // sender number
            let msg_body = msg.text ? msg.text.body : ''; // text message string

            if (msg_body) {
                console.log(`\n--- Received message from ${from} ---`);
                console.log(`Text: ${msg_body}`);

                try {
                    // Rule Engine execution First
                    let responseText = processMessage(from, msg_body);

                    // AI Fallback if rules don't match
                    if (!responseText) {
                        console.log(`-> Rules didn't match. Routing to Gemini AI...`);
                        responseText = await getAIResponse(msg_body);
                    } else {
                        console.log(`-> Rule matched! Response generated.`);
                    }

                    // Send Response
                    await sendWhatsAppMessage(from, responseText);
                } catch (err) {
                    console.error("Error processing message:", err);
                }
            }
        }
        res.sendStatus(200);
    } else {
        res.sendStatus(404);
    }
});

module.exports = router;
