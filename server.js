import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app  = express();
const PORT = process.env.PORT || 3457;

app.use(cors());
app.use(express.json());

// ── Anthropic proxy ───────────────────────────────────────────────────────────
app.post('/api/claude', async (req, res) => {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: { message: 'ANTHROPIC_API_KEY is not set in .env' } });
  }
  try {
    const upstream = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type':      'application/json',
        'x-api-key':         apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify(req.body),
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: { message: `Proxy error: ${err.message}` } });
  }
});

// ── ElevenLabs TTS proxy ──────────────────────────────────────────────────────
// POST /api/tts  { text: string, speed: number (0.7–1.2, default 1.0) }
// Returns: audio/mpeg
app.post('/api/tts', async (req, res) => {
  const apiKey  = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;

  if (!apiKey || !voiceId) {
    return res.status(500).json({ error: 'ElevenLabs credentials not configured in .env' });
  }

  const { text, speed: rawSpeed = 1.0, previous_text } = req.body ?? {};
  const speed = Math.min(1.2, Math.max(0.7, rawSpeed));
  if (!text?.trim()) {
    return res.status(400).json({ error: 'text is required' });
  }

  try {
    const ttsBody = {
      text,
      model_id:      'eleven_multilingual_v2',
      output_format: 'mp3_44100_128',
      enable_ssml_parsing: true,
      voice_settings: {
        stability:        0.45,
        similarity_boost: 0.80,
        speed,
      },
    };
    // previous_text provides language/prosody context without being spoken
    if (previous_text) ttsBody.previous_text = previous_text;

    const upstream = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key':   apiKey,
          'Accept':       'audio/mpeg',
        },
        body: JSON.stringify(ttsBody),
      },
    );

    if (!upstream.ok) {
      const errBody = await upstream.text();
      return res.status(upstream.status).json({ error: errBody });
    }

    const buf = await upstream.arrayBuffer();
    res.set('Content-Type', 'audio/mpeg');
    res.set('Accept-Ranges', 'bytes');
    res.set('Access-Control-Allow-Origin', '*');
    res.send(Buffer.from(buf));
  } catch (err) {
    res.status(502).json({ error: `TTS proxy error: ${err.message}` });
  }
});

// ── Static frontend ───────────────────────────────────────────────────────────
app.use(express.static(__dirname));
app.get('*', (req, res) => res.sendFile(`${__dirname}/index.html`));

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  const mask = (k) => k ? `${k.slice(0, 12)}…${k.slice(-4)}` : '✗ NOT SET';
  console.log(`\n  Oído proxy  →  http://localhost:${PORT}`);
  console.log(`  Anthropic   ${mask(process.env.ANTHROPIC_API_KEY)}`);
  console.log(`  ElevenLabs  ${mask(process.env.ELEVENLABS_API_KEY)}  voice: ${process.env.ELEVENLABS_VOICE_ID ?? '✗ NOT SET'}\n`);
});
