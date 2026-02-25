# WhatsApp AI Bot MVP

This repository contains an MVP of a WhatsApp bot leveraging the WhatsApp Cloud API, custom business rules, and the Gemini CLI for AI fallbacks.

## Project Structure
- `index.js` - The main Express application entry point.
- `.env` - Environment variables (ensure you fill this out based on `.env.example`).
- `routes/webhook.js` - Verification route (`GET`) and message handler route (`POST`).
- `services/ruleEngine.js` - Top-level business rule processor before any AI interactions.
- `services/whatsapp.js` - Outbound WhatsApp messaging API wrapper.
- `services/aiFallback.js` - Outbound shell execution of the Gemini CLI for natural language AI processing.

## Prerequisites
Before running the bot, ensure the following are met:
1. Node.js (v24+) is installed.
2. The `gemini` CLI is logged in and functioning.
3. You have run `npm install`.

## Configuration
Before running the application, make sure your `.env` file is properly populated:

```env
WHATSAPP_TOKEN=your_whatsapp_access_token
PHONE_NUMBER_ID=your_whatsapp_phone_number_id
VERIFY_TOKEN=my_secure_token_123
PORT=3000
```

## How to Run Locally

You must run both the Express backend server and a secure forwarding tunnel so the Meta Developer Platform can reach your local machine.

### Terminals Needed:
You will need to open **two** separate command prompts / terminals to run the system correctly.

#### 1: Start the Local API Server
In your first terminal, run:
```bash
cd /path/to/whatsap_bot
node index.js
```
*Wait for it to say `Server is listening on port 3000`.*

#### 2: Start the Webhook Tunnel
In your second terminal, run:
```bash
cd /path/to/whatsap_bot
ssh -o StrictHostKeyChecking=accept-new -R 80:localhost:3000 nokey@localhost.run
```
*Wait for the URL (e.g. `https://1a2b3c...lhr.life`). Look out for the domain name in the text printout output.*

### Updating WhatsApp Cloud Settings
Once the tunnel outputs a URL (e.g., `https://example-domain.lhr.life`), configure WhatsApp Cloud Webhook:
- **Callback URL**: `https://example-domain.lhr.life/webhook`
- **Verify Token**: Must exactly match your `VERIFY_TOKEN` (default: `my_secure_token_123`)

Send a message from WhatsApp to verify that everything works.
