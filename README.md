# Muse Fish S2 Pro Voice Clone

A free ComfyUI workflow and two small nodes by **Muse Collective**.

You give it a short sample of a voice and a plain-text script. It adds the emotion and delivery tags for you, then
**Fish Audio S2 Pro** reads your script in that voice.

**Built with Fish Audio.**

## What's in this pack

| | What it does |
|---|---|
| **Muse Fish S2 Prompter** (node) | Adds Fish S2 Pro tags such as `[excited]`, `[with gentle warmth]`, `[pause]` and `[emphasis]` to your script, using a language model you choose. Your words stay exactly as you wrote them; only the tags are added. It can also write a short script from an idea. |
| **Muse Whisper Transcribe** (node) | Writes down the words spoken in your voice sample. Fish S2 uses these as the `reference_text`, which helps the cloned voice. It works with current ComfyUI. |
| **Muse Fish S2 Pro Voice Clone** (workflow) | Everything wired up, in `example_workflows/`. |

## Install

1. **This pack:** ComfyUI Manager → *Install via Git URL* →
   `https://github.com/muse-collective-26/Muse-Fish-S2-Pro-Voice-Clone`
   Or clone it into `ComfyUI/custom_nodes/`. It needs no extra Python installs.
2. **The other node packs the workflow uses.** Open the workflow, then use ComfyUI Manager → *Install Missing Custom Nodes*:
   - [ComfyUI-fish-audio-s2](https://github.com/Saganaki22/ComfyUI-FishAudioS2): the Fish S2 Pro nodes
   - [ComfyUI_Fill-Nodes](https://github.com/filliptm/ComfyUI_Fill-Nodes): *FL Audio Separation*
   - [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite): *Load Audio (Upload)*
3. Restart ComfyUI.

## Models

| Model | Where it comes from | Licence |
|---|---|---|
| Fish S2 Pro: [`fishaudio/s2-pro`](https://huggingface.co/fishaudio/s2-pro), or the smaller [`drbaph/s2-pro-fp8`](https://huggingface.co/drbaph/s2-pro-fp8) used in the workflow | The Fish S2 node pack (see its README) | Fish Audio Research License: **non-commercial only** (see below) |
| Whisper large-v3: [`openai/whisper-large-v3`](https://huggingface.co/openai/whisper-large-v3) | Downloads by itself the first time Muse Whisper Transcribe runs (about 3 GB) | Apache-2.0 |
| HDemucs (vocal split) | Downloads by itself the first time FL Audio Separation runs | See ComfyUI_Fill-Nodes |

## How to use the workflow

1. **Your voice sample:** upload 5–15 seconds of clear speech in the voice you want. You need the right to use that voice.
2. **Your script:** type it as plain text, in paragraphs.
3. **Muse Fish S2 Prompter:** pick a **provider** and a **model**:
   - **Ollama (local)** or **LM Studio (local)**: free, and runs on your own computer. Type the name of a model you have, for example `qwen3:8b`.
   - **ChatGPT (OpenAI)**: needs `OPENAI_API_KEY` set in the ComfyUI environment. Leave **model** empty to use the default.
   - **Gemini**: needs `GEMINI_API_KEY` set in the ComfyUI environment.
   - **Custom**: any OpenAI-compatible server. Put its address in `base_url`.

   Keys are only read from the environment. They are never typed into the node or saved in your workflow. Restart
   ComfyUI after you set one.
4. Press **Run**. The tagged script appears on the Prompter node, and Fish S2 reads it in your voice. The audio is
   saved in `output/Muse/Audio/`.

Tips:
- Not happy with the tags? Change **variation** on the Prompter and run it again for a different version.
- The Prompter's **report** tells you how many tags were added. It also warns you if the language model changed any
  of your words.
- If your sample has no music, you can skip FL Audio Separation and connect the sample straight to Muse Whisper
  Transcribe.

## Licences, please read

- **The Muse nodes in this repo** (`fish_prompter.py`, `whisper_transcribe.py`, `js/`) and the workflow file are
  **MIT**. See [LICENSE](LICENSE).
- **Fish Audio S2 Pro** is not part of this repo. It is under the **Fish Audio Research License**, included here as
  [LICENSE-FISH-AUDIO.md](LICENSE-FISH-AUDIO.md):
  - It's free for **research and non-commercial use**, such as personal or hobby projects, evaluation and testing.
  - **Any commercial use needs a separate written licence from Fish Audio**, at business@fish.audio. Commercial
    means anything aimed at earning money, such as client work, paid products or services, or content you earn from.
  - If you share something that uses it, you must include that licence and the notice in [NOTICE](NOTICE), and show
    "Built with Fish Audio".
- The other node packs and models have their own licences. See [NOTICE](NOTICE).
- Only clone voices you have permission to use.

## Credits

- [Fish Audio](https://fish.audio) for S2 Pro, and Saganaki22 for the ComfyUI Fish S2 nodes.
- OpenAI for Whisper; filliptm for ComfyUI_Fill-Nodes; Kosinkadink for VideoHelperSuite.

© 2026 Muse Collective
