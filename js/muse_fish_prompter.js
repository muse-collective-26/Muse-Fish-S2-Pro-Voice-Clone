// [2026-11-16] Muse Fish S2 Prompter: shows the tagged script (and a short report) on the node after it runs, so you
// can read it before Fish speaks it. Not saved in the workflow.
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MuseCollective.FishS2Prompter",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== "MuseFishS2Prompter") return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = created?.apply(this, arguments);
      const box = document.createElement("div");
      box.style.cssText = "display:flex;flex-direction:column;gap:4px;width:100%;height:100%;box-sizing:border-box;";
      const report = document.createElement("div");
      report.style.cssText = "font:12px sans-serif;color:#fbbf24;min-height:15px;";
      report.textContent = "The tagged script shows here after a run.";
      const out = document.createElement("textarea");
      out.readOnly = true;
      out.placeholder = "Tagged script";
      out.style.cssText = "flex:1 1 auto;min-height:120px;width:100%;box-sizing:border-box;resize:none;background:#0a0a0d;color:#ddd;border:1px solid #333;border-radius:6px;font:12px monospace;padding:6px;";
      for (const ev of ["keydown", "wheel", "pointerdown"]) out.addEventListener(ev, (e) => e.stopPropagation());
      box.append(report, out);
      this.addDOMWidget("muse_fish_script_view", "muse_fish_script_view", box, { serialize: false, getMinHeight: () => 160 });
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
