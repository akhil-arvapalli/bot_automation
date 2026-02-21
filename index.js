require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const webhookRoutes = require('./routes/webhook');
const app = express();

app.use(bodyParser.json());

// Routes
app.use('/webhook', webhookRoutes);

app.get('/', (req, res) => {
    res.send('WhatsApp Bot MVP Server is running!');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is listening on port ${PORT}`);
});
