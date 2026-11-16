"""[2026-11-16] Muse Fish S2 Prompter - free community node by Muse Collective.

Turns plain text into a Fish Audio S2 Pro script: the emotion / delivery tags in square brackets, placed right before
the words they change ([excited], [with gentle warmth], [pause], [emphasis]...). Your words are kept exactly; only the
tags are added. Or, with "Write it for me", it writes a short script from your idea.

Uses a language model you choose - the same kinds as Muse Director's Analyze: Ollama or LM Studio on your own machine,
ChatGPT (OPENAI_API_KEY), Gemini (GEMINI_API_KEY) or any OpenAI-compatible server. Keys are read from the ComfyUI
environment only - never typed into the node or saved in the workflow.

Own code. Standard library only (no extra installs).
"""
import json
import logging
import os
import re
import urllib.error
import urllib.request

log = logging.getLogger(__name__)
TAG = "[Muse Fish S2 Prompter]"

PROVIDERS = {
    "Ollama (local)": {"kind": "ollama", "url": "http://127.0.0.1:11434", "model": ""},
    "LM Studio (local)": {"kind": "openai_like", "url": "http://127.0.0.1:1234/v1", "model": ""},
    "ChatGPT (OpenAI)": {"kind": "openai", "url": "https://api.openai.com/v1", "model": "gpt-5.4", "key": "OPENAI_API_KEY"},
    "Gemini": {"kind": "openai_like", "url": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-2.5-flash",
               "key": "GEMINI_API_KEY"},
    "Custom (OpenAI-compatible)": {"kind": "openai_like", "url": "", "model": "", "key": "MUSE_LLM_API_KEY"},
}
MODES = ["Add tags (keep my words)", "Write it for me"]

TAG_RULES = (
    "How Fish Audio S2 Pro tags work: free-form plain words in square brackets, placed right BEFORE the words they "
    "change. They set emotion and delivery, e.g. [warm, slightly amused], [excited], [with gentle warmth], [sad], "
    "[whispering], [laughing], [chuckles], [sighs], [pause], [short pause], [emphasis], [clearing throat].\n")

TAG_PROMPT = (
    "You add emotion and delivery tags to a script for Fish Audio S2 Pro, a text-to-speech model that reads the "
    "script in a cloned voice.\n" + TAG_RULES +
    "Rules:\n"
    "- Keep every word of the script exactly as written: same words, same order, same punctuation. Only add tags. "
    "Never rewrite, add or remove words.\n"
    "- Start each paragraph with one delivery tag that fits it, e.g. [warm and chatty, natural pace].\n"
    "- Inside the speech, add a few short tags only where the feeling changes, a beat is needed, or a word should "
    "land: [pause], [emphasis], a laugh or a sigh. Never two tags in a row.\n"
    "- Keep the paragraph breaks.\n"
    "- Never put an accent in a tag; the voice clip decides the accent.\n"
    "- Reply with the tagged script only - nothing before or after it, no quotation marks, no notes.")

WRITE_PROMPT = (
    "You write a short spoken script for Fish Audio S2 Pro, a text-to-speech model that reads the script in a cloned "
    "voice.\n" + TAG_RULES +
    "Rules:\n"
    "- Start each paragraph with one delivery tag, e.g. [warm and chatty, natural pace].\n"
    "- Inside the speech, use a few short tags only where the feeling changes or a sound happens (a laugh, a sigh, "
    "a pause). Never two tags in a row.\n"
    "- Natural, conversational speech. Short sentences. No stage directions outside the brackets, no narrator, no "
    "speaker names.\n"
    "- Never put an accent in a tag; the voice clip decides the accent.\n"
    "- If the user gives exact lines to say, keep their words exactly as they are and only add the tags.\n"
    "- Reply with the script only - nothing before or after it, no quotation marks around it.")


def clean(text):
    """The script only: no thinking, code fences, lead-in or wrapping quotes. Paragraph breaks are kept."""
    t = str(text or "").strip()
    if "</think>" in t:
        t = t.split("</think>", 1)[1].strip()
    t = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", t).strip()
    for lead in ("here is the tagged script:", "here's the tagged script:", "here is the script:", "here's the script:",
                 "tagged script:", "the script:", "script:"):
        if t.lower().startswith(lead):
            t = t[len(lead):].strip()
    if len(t) > 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1].strip()
    lines = [" ".join(x.split()) for x in t.replace("\r", "").split("\n")]
    out = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def words_only(text):
    """The spoken words without tags, for the 'did it keep my words?' check."""
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", str(text or ""))).strip().lower()


def _post(url, payload, headers=None, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:   # the body is not shown (it can echo things back)
        raise RuntimeError(f"The model server answered HTTP {e.code}. Check the model name, the key and that the server is running.") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Couldn't reach the model server at {url.split('/v1')[0].split('/api/')[0]} ({e.reason}). "
                           "Is it running?") from None


def ask(provider, model, system, user, base_url=""):
    """-> the model's reply text."""
    p = PROVIDERS.get(provider) or PROVIDERS["Ollama (local)"]
    model = (model or "").strip() or p["model"]
    if not model:
        raise ValueError(f"Type the model name for {provider} (e.g. the name of the model you loaded).")
    if p["kind"] == "openai":   # the OpenAI key only ever goes to OpenAI
        key = os.environ.get(p["key"], "").strip()
        if not key:
            raise RuntimeError("ChatGPT needs OPENAI_API_KEY set in the ComfyUI environment (then restart ComfyUI).")
        d = _post(f"{p['url']}/chat/completions", {"model": model, "stream": False, "max_completion_tokens": 8192,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                  {"Authorization": f"Bearer {key}"})
        return ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    url = (base_url or "").strip().rstrip("/") or p["url"]
    if not url:
        raise ValueError(f"{provider} needs a base_url (the server's address, e.g. http://127.0.0.1:8000/v1).")
    if p["kind"] == "ollama":
        url = re.sub(r"/(api|v1)$", "", url)
        d = _post(f"{url}/api/chat", {"model": model, "stream": False, "think": False, "keep_alive": 0,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        return (d.get("message") or {}).get("content") or ""
    headers = {}
    key_name = p.get("key")
    if key_name and os.environ.get(key_name, "").strip():
        if provider == "Gemini" and "googleapis.com" not in url:
            raise ValueError("Gemini's key is only sent to Google's address - leave base_url empty for Gemini.")
        headers["Authorization"] = f"Bearer {os.environ[key_name].strip()}"
    elif provider == "Gemini":
        raise RuntimeError("Gemini needs GEMINI_API_KEY set in the ComfyUI environment (then restart ComfyUI).")
    if not url.endswith("/v1") and "/v1" not in url and provider == "LM Studio (local)":
        url += "/v1"
    d = _post(f"{url}/chat/completions", {"model": model, "stream": False, "temperature": 0.4,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, headers)
    return ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def _get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"The server answered HTTP {e.code}" + (" - check the API key." if e.code in (401, 403) else ".")) from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Couldn't reach {url.split('/api/')[0].split('/v1')[0]} ({e.reason}). Is it running?") from None


def list_models(provider, base_url=""):
    """[2026-11-16] Andy: "a selection of models for each provider, including the ones on your system" (like Muse
    Director 2.1's Refresh models). Asks the provider which models it has. -> sorted list of model names."""
    p = PROVIDERS.get(provider) or PROVIDERS["Ollama (local)"]
    if p["kind"] == "openai":   # the OpenAI key only ever goes to OpenAI
        key = os.environ.get(p["key"], "").strip()
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY in the ComfyUI environment (then restart ComfyUI) to list ChatGPT models.")
        d = _get(f"{p['url']}/models", {"Authorization": f"Bearer {key}"})
        names = [m.get("id", "") for m in d.get("data") or []]
        # chat models only (not image, audio, embedding or moderation models)
        names = [n for n in names if re.match(r"^(gpt-|o\d|chatgpt-)", n)
                 and not re.search(r"image|audio|realtime|transcribe|tts|search|embedding|moderation|instruct", n)]
        return sorted(set(names), reverse=True)
    url = (base_url or "").strip().rstrip("/") or p["url"]
    if not url:
        raise ValueError(f"{provider} needs a base_url first.")
    if p["kind"] == "ollama":
        d = _get(re.sub(r"/(api|v1)$", "", url) + "/api/tags")
        return sorted({m.get("name", "") for m in d.get("models") or []} - {""})
    headers = {}
    key_name = p.get("key")
    if provider == "Gemini":
        key = os.environ.get(key_name, "").strip()
        if not key:
            raise RuntimeError("Set GEMINI_API_KEY in the ComfyUI environment (then restart ComfyUI) to list Gemini models.")
        if "googleapis.com" not in url:
            raise ValueError("Gemini's key is only sent to Google's address - leave base_url empty for Gemini.")
        headers["Authorization"] = f"Bearer {key}"
    elif key_name and os.environ.get(key_name, "").strip():
        headers["Authorization"] = f"Bearer {os.environ[key_name].strip()}"
    if provider == "LM Studio (local)" and "/v1" not in url:
        url += "/v1"
    d = _get(f"{url}/models", headers)
    names = [str(m.get("id", "")).removeprefix("models/") for m in d.get("data") or []]
    if provider == "Gemini":
        names = [n for n in names if n.startswith("gemini") and not re.search(r"embedding|image|tts|live|audio", n)]
    return sorted(set(names) - {""})


def _register_routes():
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return
    if getattr(PromptServer, "instance", None) is None:
        return

    @PromptServer.instance.routes.post("/muse_fish_s2/models")
    async def _models_route(request):
        import asyncio
        try:
            body = await request.json()
            models = await asyncio.to_thread(list_models, str(body.get("provider") or ""), str(body.get("base_url") or ""))
            return web.json_response({"models": models})
        except Exception as e:   # the message only (never a key or a server body)
            return web.json_response({"error": str(e)}, status=400)


class MuseFishS2Prompter:
    CATEGORY = "Muse Collective/Audio"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("script", "report")
    OUTPUT_NODE = True
    DESCRIPTION = ("Adds Fish Audio S2 Pro emotion tags to your text (your words are kept exactly), or writes a short "
                   "script from your idea. Connect 'script' to the Fish S2 node's text.")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (list(PROVIDERS), {"default": "Ollama (local)", "tooltip":
                             "Which language model writes the tags. Ollama / LM Studio run on your own computer. "
                             "ChatGPT needs OPENAI_API_KEY, Gemini needs GEMINI_API_KEY in the ComfyUI environment."}),
                "model": ("STRING", {"default": "", "tooltip":
                          "The model's exact name, e.g. qwen3:8b (Ollama) or gpt-5.4 (ChatGPT). Empty = ChatGPT/Gemini default."}),
                "text": ("STRING", {"multiline": True, "default": "", "tooltip":
                         "Your script. Plain text is fine - the tags are added for you."}),
            },
            "optional": {
                "mode": (MODES, {"default": MODES[0], "tooltip":
                         "Add tags (keep my words): only adds tags. Write it for me: writes a short script from your idea."}),
                "base_url": ("STRING", {"default": "", "tooltip":
                             "Only for a local or custom server on another address. Empty = the usual address."}),
                "variation": ("INT", {"default": 0, "min": 0, "max": 9999, "tooltip":
                              "Change this number to get a different version for the same text."}),
            },
        }

    def run(self, provider, model, text, mode=MODES[0], base_url="", variation=0):
        text = str(text or "").strip()
        if not text:
            raise ValueError("Type your script (or your idea) into 'text' first.")
        keep = mode != MODES[1]
        system = TAG_PROMPT if keep else WRITE_PROMPT
        user = (f"The script:\n{text}" if keep else f"What the user wants:\n{text}") + (
            f"\n\n(Version {variation}.)" if variation else "")
        log.info("%s %s, %s, %s.", TAG, provider, (model or "default model").strip(), mode)
        script = clean(ask(provider, model, system, user, base_url))
        if not script:
            raise RuntimeError("The model sent back nothing. Try again, or pick another model.")
        tags = len(re.findall(r"\[[^\]]*\]", script))
        report = f"{tags} tags, {len(words_only(script).split())} words."
        if keep and words_only(script) != words_only(text):
            report += " Note: the model changed some of your words - read it through, or press again (change 'variation')."
        log.info("%s done: %s", TAG, report)
        return {"ui": {"muse_fish_script": [script], "muse_fish_report": [report]}, "result": (script, report)}


_register_routes()

NODE_CLASS_MAPPINGS = {"MuseFishS2Prompter": MuseFishS2Prompter}
NODE_DISPLAY_NAME_MAPPINGS = {"MuseFishS2Prompter": "Muse Fish S2 Prompter"}
