#!/usr/bin/env node

const https = require('https');

const args = process.argv.slice(2);

// Handle flags
if (args[0] === '--version' || args[0] === '-v') {
  console.log('paisa-cli 0.1.2');
  process.exit(0);
}

if (args[0] === '--help' || args[0] === '-h') {
  console.log(`
  Paisa CLI - Smart LLM Routing That Saves You Money
  
  Usage:
    paisa-cli "your prompt here"
    paisa-cli --version
    paisa-cli --help
    
  Example:
    paisa-cli "What is 2+2?"
    paisa-cli "Write a Python binary search function"
    
  Powered by paisa-api.vercel.app
  `);
  process.exit(0);
}

if (args.length === 0) {
  console.error('Error: Please provide a prompt.');
  console.log('Usage: paisa-cli "your prompt here"');
  process.exit(1);
}

const prompt = args.join(' ');
const body = JSON.stringify({ prompt });

const options = {
  hostname: 'paisa-api.vercel.app',
  path: '/route',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  }
};

console.log('⏳ Routing your prompt...\n');

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    try {
      const json = JSON.parse(data);
      
      if (json.error) {
        console.error(`Error: ${json.error}`);
        process.exit(1);
      }

      const saved = json.json_tokens - json.toon_tokens;
      const savedPct = json.json_tokens > 0 
        ? Math.round((saved / json.json_tokens) * 100) 
        : 0;

      console.log('┌─────────────────────────────────────┐');
      console.log('│  Paisa CLI                          │');
      console.log('└─────────────────────────────────────┘');
      console.log(`✦ Prompt    : ${prompt.substring(0, 50)}${prompt.length > 50 ? '...' : ''}`);
      console.log(`✦ Label     : ${json.label} (confidence: ${json.confidence})`);
      console.log(`✦ Model     : ${json.model_used}`);
      console.log(`✦ Latency   : ${Math.round(json.latency_ms)}ms`);
      console.log(`✦ Tokens    : TOON ${json.toon_tokens} vs JSON ${json.json_tokens} (saved ${savedPct}%)`);
      console.log(`✦ Tier Blur : ${json.tier_blurred ? 'Yes' : 'No'}`);
      console.log('');
      console.log('── Response ──────────────────────────');
      console.log(json.response);
      console.log('──────────────────────────────────────');

    } catch (e) {
      console.error('Error parsing response:', e.message);
      process.exit(1);
    }
  });
});

req.on('error', (e) => {
  if (e.code === 'ENOTFOUND' || e.code === 'ECONNREFUSED') {
    console.error('Paisa server unreachable. Try again later.');
  } else {
    console.error(`Error: ${e.message}`);
  }
  process.exit(1);
});

req.write(body);
req.end();
