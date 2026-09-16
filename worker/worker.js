/**
 * Odin backend: a Cloudflare Worker that holds every secret so the public web page never does.
 *
 * Endpoints (all require header  X-Odin-Pin: <ODIN_PIN>):
 *   GET  /config    -> { picovoiceKey, modelUrl, keywordUrl, userName, voice }
 *   POST /session   -> mints a short-lived OpenAI Realtime client secret bound to the persona + tools
 *   POST /research  -> { question, context } -> Claude + web search -> { answer }
 *   POST /action    -> { action: "queue_business" | "save_note", ... } -> writes data/*.json in the GitHub repo
 *
 * Paste this file into a Worker in the Cloudflare dashboard (no build step), then add the secrets listed in
 * worker/README.md. Raw fetch() is used for every API on purpose: dashboard-pasted Workers cannot import npm SDKs.
 */

const REALTIME_MODEL_DEFAULT = "gpt-realtime";
const CLAUDE_MODEL_DEFAULT = "claude-opus-5";
const PORCUPINE_MODEL_DEFAULT = "https://cdn.jsdelivr.net/gh/Picovoice/porcupine@master/lib/common/porcupine_params.pv";

export default {
  async fetch(request, env) {
    const cors = corsHeaders(env, request.headers.get("Origin") || "");
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    try {
      if (!authorized(request, env)) return json({ error: "bad or missing PIN" }, 401, cors);

      if (url.pathname === "/config" && request.method === "GET") {
        return json({
          picovoiceKey: env.PICOVOICE_ACCESS_KEY || "",
          modelUrl: env.PORCUPINE_MODEL_URL || PORCUPINE_MODEL_DEFAULT,
          keywordUrl: env.PORCUPINE_KEYWORD_URL || "",      // optional custom "Hey Odin" .ppn
          userName: env.USER_NAME || "sir",
          voice: env.REALTIME_VOICE || "cedar",
        }, 200, cors);
      }
      if (url.pathname === "/session" && request.method === "POST") {
        return json(await createSession(env, await request.json()), 200, cors);
      }
      if (url.pathname === "/research" && request.method === "POST") {
        return json(await research(env, await request.json()), 200, cors);
      }
      if (url.pathname === "/action" && request.method === "POST") {
        return json(await action(env, await request.json()), 200, cors);
      }
      return json({ error: "not found" }, 404, cors);
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500, cors);
    }
  },
};

// ---------------------------------------------------------------- auth / cors / helpers

function authorized(request, env) {
  if (!env.ODIN_PIN) return false;
  const pin = request.headers.get("X-Odin-Pin") || "";
  return pin.length === env.ODIN_PIN.length && pin === env.ODIN_PIN;
}

function corsHeaders(env, origin) {
  const allowed = (env.ALLOWED_ORIGIN || "*").split(",").map(s => s.trim());
  const ok = allowed.includes("*") || allowed.includes(origin);
  return {
    "Access-Control-Allow-Origin": ok ? (origin || "*") : allowed[0],
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Odin-Pin",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });
}

function b64encode(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

function b64decode(b64) {
  const bin = atob(b64.replace(/\n/g, ""));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

// ---------------------------------------------------------------- OpenAI Realtime session

async function createSession(env, body) {
  if (!env.OPENAI_API_KEY) throw new Error("OPENAI_API_KEY not set on the Worker");
  const base = {
    type: "realtime",
    model: env.REALTIME_MODEL || REALTIME_MODEL_DEFAULT,
    instructions: body.instructions || "You are Odin.",
    tools: body.tools || [],
    tool_choice: "auto",
    audio: {
      input: {
        turn_detection: {
          type: "server_vad", threshold: 0.55, prefix_padding_ms: 300, silence_duration_ms: 650,
          create_response: true, interrupt_response: true,
        },
        transcription: { model: env.TRANSCRIBE_MODEL || "gpt-4o-mini-transcribe" },
      },
      output: { voice: body.voice || env.REALTIME_VOICE || "cedar" },
    },
  };

  let r = await mint(env, base);
  if (!r.ok) {
    // Transcription is only used for on-screen captions; never let it block the session.
    const noTranscribe = structuredClone(base);
    delete noTranscribe.audio.input.transcription;
    r = await mint(env, noTranscribe);
  }
  if (!r.ok) throw new Error(`client_secrets ${r.status}: ${await r.text()}`);
  const data = await r.json();
  if (!data.value) throw new Error("no client secret in response: " + JSON.stringify(data).slice(0, 300));
  return { value: data.value, expires_at: data.expires_at || null };
}

function mint(env, session) {
  return fetch("https://api.openai.com/v1/realtime/client_secrets", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.OPENAI_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ session }),
  });
}

// ---------------------------------------------------------------- Claude research (web search)

async function research(env, body) {
  if (!env.ANTHROPIC_API_KEY) return { answer: "Research is not configured. Add ANTHROPIC_API_KEY to the Worker." };
  const system = "You answer a follow-up question for someone listening to a business teardown while driving. " +
    "Search the web, then answer in at most three spoken sentences: plain words, numbers said naturally, " +
    "name the source in passing (e.g. 'per TechCrunch this June'). No markdown, no URLs, no lists. " +
    "If you cannot verify it, say so in one sentence rather than guessing.";
  const user = `CONTEXT (today's teardown, for reference):\n${JSON.stringify(body.context || {}).slice(0, 6000)}\n\nQUESTION: ${body.question}`;
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json" },
    body: JSON.stringify({
      model: env.CLAUDE_MODEL || CLAUDE_MODEL_DEFAULT,
      max_tokens: 1500,
      system,
      output_config: { effort: "low" },
      tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 4 }],
      messages: [{ role: "user", content: user }],
    }),
  });
  if (!r.ok) throw new Error(`anthropic ${r.status}: ${(await r.text()).slice(0, 300)}`);
  const data = await r.json();
  const answer = (data.content || []).filter(b => b.type === "text").map(b => b.text).join(" ").trim();
  return { answer: answer || "I couldn't find anything solid on that." };
}

// ---------------------------------------------------------------- repo writes (queue + notes)

async function action(env, body) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) return { ok: false, error: "GITHUB_TOKEN / GITHUB_REPO not set on the Worker" };
  const now = new Date().toISOString();
  if (body.action === "queue_business") {
    const request = String(body.request || "").trim();
    if (!request) return { ok: false, error: "empty request" };
    await updateJson(env, "data/queue.json", list => {
      list.push({ request, note: body.note || "", received: now, source: "odin" });
      return list;
    }, `Odin: queue ${request}`);
    return { ok: true, queued: request, position: "next non-Sunday edition" };
  }
  if (body.action === "save_note") {
    const text = String(body.text || "").trim();
    if (!text) return { ok: false, error: "empty note" };
    await updateJson(env, "data/notes.json", list => {
      list.push({ text, url: body.url || "", edition: body.edition || "", created: now, included: false });
      return list;
    }, "Odin: save note");
    return { ok: true, saved: text, delivery: "included in tomorrow morning's email" };
  }
  return { ok: false, error: `unknown action ${body.action}` };
}

async function updateJson(env, path, mutate, message) {
  const api = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`;
  const headers = {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json",
    "User-Agent": "odin-worker", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json",
  };
  let sha, list = [];
  const get = await fetch(api, { headers });
  if (get.ok) {
    const j = await get.json();
    sha = j.sha;
    try { list = JSON.parse(b64decode(j.content) || "[]"); } catch { list = []; }
  } else if (get.status !== 404) {
    throw new Error(`github GET ${get.status}: ${(await get.text()).slice(0, 200)}`);
  }
  const updated = mutate(Array.isArray(list) ? list : []);
  const put = await fetch(api, {
    method: "PUT", headers,
    body: JSON.stringify({ message, content: b64encode(JSON.stringify(updated, null, 2) + "\n"), ...(sha ? { sha } : {}) }),
  });
  if (!put.ok) throw new Error(`github PUT ${put.status}: ${(await put.text()).slice(0, 200)}`);
}
