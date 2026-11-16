"""[2026-11-16] Muse Whisper Transcribe - what is said in an audio clip, as text (for Fish S2's reference_text).

Some transcribe nodes now fail with "Input type (float) and bias type (Half) should be the same": they load Whisper in
half precision but feed the audio in as full precision (newer transformers refuses that). Here the model and the audio
always use the same type.

Model: openai/whisper-large-v3 from Hugging Face (the same one the VRGDG node uses, so most people already have it;
otherwise it downloads once, about 3 GB). The model is freed after each run by default, so Fish has the graphics card.
Own code; uses transformers and torchaudio, which ComfyUI already has.
"""
import gc
import logging

import torch

log = logging.getLogger(__name__)
TAG = "[Muse Whisper Transcribe]"
MODELS = ["openai/whisper-large-v3", "openai/whisper-large-v3-turbo", "openai/whisper-small"]
LANGUAGES = ["english", "auto", "spanish", "french", "german", "italian", "portuguese", "dutch", "polish", "russian",
             "japanese", "korean", "chinese", "arabic", "hindi", "turkish"]
_CACHE = {}


def _load(name, dev, dtype):
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    key = (name, dev, str(dtype))
    if key in _CACHE:
        return _CACHE[key]
    proc = WhisperProcessor.from_pretrained(name)
    try:
        model = WhisperForConditionalGeneration.from_pretrained(name, dtype=dtype)
    except TypeError:   # older transformers
        model = WhisperForConditionalGeneration.from_pretrained(name, torch_dtype=dtype)
    model = model.to(dev).eval()
    _CACHE[key] = (proc, model)
    return proc, model


def _free():
    _CACHE.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def transcribe(audio, model_name=MODELS[0], language="english"):
    """AUDIO {waveform [B, C, N], sample_rate} -> the words, in 30 s windows."""
    import torchaudio
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if dev == "cuda" else torch.float32
    wav = audio["waveform"][0].float().mean(0).cpu()
    rate = int(audio["sample_rate"])
    if rate != 16000:
        wav = torchaudio.functional.resample(wav, rate, 16000)
    proc, model = _load(model_name, dev, dtype)
    texts = []
    step = 30 * 16000
    for i in range(0, wav.shape[-1], step):
        chunk = wav[i:i + step]
        if chunk.shape[-1] < 1600:   # under 0.1 s: nothing to hear
            continue
        feats = proc(chunk.numpy(), sampling_rate=16000, return_tensors="pt").input_features.to(dev, dtype)   # the fix
        kw = {"task": "transcribe"} if language == "auto" else {"language": language, "task": "transcribe"}
        with torch.inference_mode():
            ids = model.generate(feats, **kw)
        texts.append(proc.batch_decode(ids, skip_special_tokens=True)[0].strip())
    return " ".join(" ".join(texts).split())


class MuseWhisperTranscribe:
    CATEGORY = "Muse Collective/Audio"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    DESCRIPTION = ("What is said in an audio clip, as text - e.g. the words in your Fish S2 reference voice, for its "
                   "reference_text. Works with current ComfyUI (no half/float error).")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO", {"tooltip": "The clip to transcribe. A voice on its own works best (split off music first)."}),
                "language": (LANGUAGES, {"default": "english", "tooltip": "The language spoken. 'auto' lets Whisper guess."}),
            },
            "optional": {
                "model": (MODELS, {"default": MODELS[0], "tooltip":
                          "large-v3: most accurate. large-v3-turbo: faster, nearly as good. small: quickest, least accurate. "
                          "A model you haven't used before downloads once."}),
                "keep_model_loaded": ("BOOLEAN", {"default": False, "tooltip":
                                      "Off = Whisper is unloaded after each run, so Fish S2 gets the whole graphics card."}),
            },
        }

    def run(self, audio, language="english", model=MODELS[0], keep_model_loaded=False):
        try:
            text = transcribe(audio, model, language)
        finally:
            if not keep_model_loaded:
                _free()
        log.info("%s %s, %s: %d words.", TAG, model, language, len(text.split()))
        if not text:
            log.warning("%s no words heard - is there speech in the clip?", TAG)
        return (text,)


NODE_CLASS_MAPPINGS = {"MuseWhisperTranscribe": MuseWhisperTranscribe}
NODE_DISPLAY_NAME_MAPPINGS = {"MuseWhisperTranscribe": "Muse Whisper Transcribe"}
