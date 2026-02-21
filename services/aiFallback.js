const { exec } = require('child_process');

function getAIResponse(text) {
    return new Promise((resolve) => {
        const prompt = `You are a professional WhatsApp assistant. The user said: "${text}". If the user is speaking Punjabi (Gurmukhi or Romanized), translate it to English and reply appropriately in English. Always reply in short, professional English.`;

        // Use base64 encoding to completely avoid Windows shell escaping issues
        const b64Prompt = Buffer.from(prompt).toString('base64');

        // This command decodes the prompt and passes it to gemini CLI using spawnSync internally
        // Using an array of arguments with child_process.spawnSync avoids shell quoting entirely for the inner call.
        const command = `node -e "const { spawnSync } = require('child_process'); const prompt = Buffer.from('${b64Prompt}', 'base64').toString('utf8'); const child = spawnSync('gemini', ['-p', prompt], { shell: true }); process.stdout.write(child.stdout || ''); process.stderr.write(child.stderr || ''); process.exit(child.status || 0);"`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error("Gemini CLI error:", error);
                console.error("Stderr:", stderr);
                return resolve("I am sorry, I am having trouble understanding you right now.");
            }
            // Remove potential markdown wrappers if the CLI outputs them
            let cleanOut = stdout.trim();
            resolve(cleanOut);
        });
    });
}

module.exports = { getAIResponse };
