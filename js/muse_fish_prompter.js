// [2026-11-16] Muse Fish S2 Prompter: shows the tagged script (and a short report) on the node after it runs, so you
// can read it before Fish speaks it. Not saved in the workflow.
// [2026-11-16] + a model list (Andy: "a selection of models for each provider, including the ones on your system"):
// "↻ Models" asks the chosen provider which models it has; picking one fills 'model'. It lives inside the node's own
// display box, so the node's saved settings keep their order (old workflows load the same).
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const W = (node, name) => node.widgets?.find((w) => w.name === name);

app.registerExtension({
  name: "MuseCollective.FishS2Prompter",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== "MuseFishS2Prompter") return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = created?.apply(this, arguments);
      const node = this;
      const box = document.createElement("div");
      box.style.cssText = "display:flex;flex-direction:column;gap:4px;width:100%;height:100%;box-sizing:border-box;";
      for (const ev of ["keydown", "wheel", "pointerdown"]) box.addEventListener(ev, (e) => e.stopPropagation());

      // ---- the model list
      const row = document.createElement("div");
      row.style.cssText = "display:flex;gap:6px;align-items:center;";
      const btn = document.createElement("button");
      btn.type = "button"; btn.textContent = "↻ Models";
      btn.title = "Ask the chosen provider which models it has";
      btn.style.cssText = "flex:0 0 auto;background:#c34483;color:#fff;border:1px solid #f08cbc;border-radius:6px;padding:3px 9px;font:600 12px sans-serif;cursor:pointer;";
      const pick = document.createElement("select");
      pick.style.cssText = "flex:1 1 auto;min-width:0;background:#0a0a0d;color:#ddd;border:1px solid #333;border-radius:6px;padding:3px;font:12px sans-serif;";
      pick.append(new Option("Choose a model…", ""));
      row.append(btn, pick);
      const status = document.createElement("div");
      status.style.cssText = "font:11px sans-serif;color:#9aa4bf;min-height:13px;";

      const load = async (quiet = false) => {
        const provider = W(node, "provider")?.value, base = W(node, "base_url")?.value || "";
        btn.disabled = true; if (!quiet) status.textContent = "Asking for the model list…";
        try {
          const res = await api.fetchApi("/muse_fish_s2/models", { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider, base_url: base }) });
          if (res.status === 404) throw new Error("Restart ComfyUI once to turn on the model list.");
          const d = await res.json().catch(() => ({}));
          if (!res.ok || d.error) throw new Error(d.error || `Error ${res.status}`);
          const cur = W(node, "model")?.value || "";
          pick.replaceChildren(new Option(d.models.length ? "Choose a model…" : "No models found", ""), ...d.models.map((m) => new Option(m, m)));
          if (d.models.includes(cur)) pick.value = cur;
          status.textContent = d.models.length ? `${d.models.length} models on ${provider}.` : `No models found on ${provider} - type the name in 'model'.`;
        } catch (e) {
          pick.replaceChildren(new Option("Choose a model…", ""));
          status.textContent = quiet ? "" : String(e.message || e);
        } finally { btn.disabled = false; }
      };
      btn.addEventListener("click", (e) => { e.stopPropagation(); load(false); });
      pick.addEventListener("change", () => {
        const w = W(node, "model");
        if (!w || !pick.value) return;
        w.value = pick.value; w.callback?.(pick.value);
        status.textContent = `Model set to ${pick.value}.`;
        node.setDirtyCanvas?.(true, true);
      });
      const pw = W(node, "provider");
      if (pw) {   // a new provider: its own list (the old model name belongs to the old provider)
        const cb = pw.callback;
        pw.callback = (...a) => { const out = cb?.apply(pw, a); const m = W(node, "model"); if (m) m.value = ""; load(false); return out; };
      }
      setTimeout(() => load(true), 400);   // fill the list quietly once the node is loaded

      // ---- the result
      const report = document.createElement("div");
      report.style.cssText = "font:12px sans-serif;color:#fbbf24;min-height:15px;margin-top:4px;";
      report.textContent = "The tagged script shows here after a run.";
      const out = document.createElement("textarea");
      out.readOnly = true;
      out.placeholder = "Tagged script";
      out.style.cssText = "flex:1 1 auto;min-height:120px;width:100%;box-sizing:border-box;resize:none;background:#0a0a0d;color:#ddd;border:1px solid #333;border-radius:6px;font:12px monospace;padding:6px;";
      box.append(row, status, report, out);
      this.addDOMWidget("muse_fish_script_view", "muse_fish_script_view", box, { serialize: false, getMinHeight: () => 210 });
      this.__museFish = { report, out };
      return r;
    };
    const executed = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (msg) {
      executed?.apply(this, arguments);
      const v = this.__museFish;
      if (!v) return;
      if (msg?.muse_fish_script) v.out.value = msg.muse_fish_script.join("\n");
      if (msg?.muse_fish_report) v.report.textContent = msg.muse_fish_report.join(" ");
    };
  },
});
