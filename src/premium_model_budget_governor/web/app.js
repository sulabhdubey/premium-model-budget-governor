"use strict";
const $ = id => document.getElementById(id);
$("task-form").insertAdjacentHTML("afterbegin", `<details id="first-task-guide"><summary>First task</summary>
<p>Check setup, choose a non-sensitive project folder, preview a task, then approve only when ready to spend model capacity. Installation does not change existing chats.</p>
<p>The sample uses only invented numbers. The runner still has read access to the selected project; use a safe folder. This button fills the task only, not approval.</p>
<button type="button" id="sample-task">Use sample task</button></details>`);
$("sample-task").addEventListener("click",()=>{
  if ($("task").value.trim() || $("evidence").value.trim() || $("images").value.trim()) {
    notice("Your task and attachments were preserved. Clear them before loading the sample."); return;
  }
  $("task").value = "Using only these invented figures, review this claim: a baseline cost 10 estimated credits. A candidate cost 7 plus 2 preparation and 3 for a failed attempt. Explain the complete cost and whether this proves savings. Do not inspect project files or use external sources.";
  $("task").dispatchEvent(new Event("input",{bubbles:true})); $("task").focus();
});
$("result-section").insertAdjacentHTML("beforeend", `<section id="what-changed" hidden><h3>What changed?</h3><p>Saved choices, reported observations and unknowns. A smaller estimate alone is not a benefit.</p><dl id="change-facts" class="receipt"></dl></section>`);
$("usage-status").insertAdjacentHTML("afterend", `<section id="usage-empty" hidden><h2 id="usage-empty-title"></h2><p id="usage-empty-detail"></p><button id="usage-work">Return to Work</button></section>`);
$("warnings").insertAdjacentHTML("afterend", '<div id="document-previews" hidden></div>');
$("usage-view").insertAdjacentHTML("beforeend", `
<section class="settings-band" id="digest-section"><div class="section-heading"><h2>Seven-day observation digest</h2><button id="refresh-digest">Refresh digest</button></div>
<p id="digest-status" role="status">Digest is off until enabled in Settings.</p>
<div id="digest-result" hidden><p id="digest-window" class="muted"></p>
<dl id="digest-summary" class="receipt"></dl>
<p class="muted">Latest saved counters below are not weekly totals. Imports can describe older work; other chats and missing receipts are not covered.</p>
<div class="table-scroll"><table><thead><tr><th>Source</th><th>Recorded model (unverified)</th><th>Counter kind</th><th>Input</th><th>Cached subset</th><th>Output</th></tr></thead><tbody id="digest-sources"></tbody></table></div></div></section>`);
$("settings-view").insertAdjacentHTML("beforeend", `
<section class="settings-band"><h2>Usage digest</h2><label class="consent"><input id="digest-enabled" type="checkbox" disabled>Enable the local seven-day observation digest.</label>
<p class="muted">Local display only. No background collection, email, upload or model call. Disabling leaves existing receipts intact.</p>
<p id="digest-preference-status" role="status"></p></section>`);
$("usage-view").insertAdjacentHTML("beforeend", `
<section class="settings-band"><h2>Observation journal</h2>
<label for="observation-file">Receipt packet (JSON, up to 60 KB)</label><input id="observation-file" type="file" accept="application/json,.json">
<p id="observation-status" role="status">No observation loaded.</p>
<details id="observation-preview" hidden><summary>Review local record</summary><pre id="observation-content"></pre></details>
<label class="consent"><input id="observation-consent" type="checkbox" disabled>Save this reviewed observation locally.</label>
<button id="save-observation" disabled>Save observation</button>
<p id="observation-list-status" role="status"></p><div class="table-scroll"><table><thead><tr><th>Observation</th><th>Recorded</th><th>Coverage</th><th>Receipts</th><th>Estimated credits</th></tr></thead><tbody id="observation-list"></tbody></table></div>
</section>`);
$("settings-view").insertAdjacentHTML("beforeend", `
<section class="settings-band"><h2>Observation retention</h2>
<label for="retention-before">Recorded before (local date)</label><input id="retention-before" type="date">
<button id="preview-retention">Preview cleanup</button><p id="retention-status" role="status"></p>
<p class="muted">Observation journal only. Budget leases and project files are excluded. A retained backup still contains removed records; this is not secure erasure.</p>
<pre id="retention-preview" hidden></pre><label class="consent"><input id="retention-consent" type="checkbox" disabled>Remove the previewed observations after a verified backup.</label>
<button id="apply-retention" disabled>Back up and remove observations</button></section>`);
let token = new URLSearchParams(location.hash.slice(1)).get("session") || "";
history.replaceState(null, "", location.pathname);
let preview = null, running = false, projects = [], revision = 0;
let activeId = null, watching = false;
let hostModels = [], hostRevision = 0;
let previewCleanup = Promise.resolve();
function discardPreview(identifier) {
  if (!identifier) return;
  previewCleanup = previewCleanup.then(() => api("/api/preview/discard", {id:identifier})).catch(() => {});
}
const money = value => typeof value === "number" ? value.toFixed(3) : "Unknown";
const lines = value => value.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
async function api(path, payload) {
  const response = await fetch(path, {method: payload === undefined ? "GET" : "POST", cache:"no-store", headers:{Authorization:`Bearer ${token}`, ...(payload === undefined ? {} : {"Content-Type":"application/json"})}, ...(payload === undefined ? {} : {body:JSON.stringify(payload)})});
  let data;
  try { data=await response.json(); } catch { throw new Error("Local response was incomplete. Reconnect to check the task."); }
  if (!response.ok || !data.ok) { const error=new Error(data.error || "Local service unavailable."); error.status=response.status; error.field=data.field; throw error; }
  return data.result;
}
function notice(text) { $("notice").textContent = text; }
const errorFields = ["project", "task", "budget", "evidence", "images", "context", "output", "effort", "context-profile"];
for (const id of errorFields) {
  const message = document.createElement("p"); message.id = `${id}-error`; message.className = "field-error"; message.hidden = true;
  $(id).insertAdjacentElement("afterend", message);
  $(id).setAttribute("aria-describedby", `${id}-error${id === "effort" ? " effort-status" : ""}`);
}
function clearFieldErrors() {
  for (const id of errorFields) { $(id).removeAttribute("aria-invalid"); $(`${id}-error`).hidden = true; $(`${id}-error`).textContent = ""; }
}
function showFieldError(error) {
  notice(error.message);
  if (!errorFields.includes(error.field)) return;
  const field = $(error.field), message = $(`${error.field}-error`);
  message.textContent = error.message; message.hidden = false; field.setAttribute("aria-invalid", "true");
  const details = field.closest("details"); if (details) details.open = true;
  field.focus();
}
function invalidate() { revision++; clearFieldErrors(); if (!running) discardPreview(preview?.id); preview = null; $("preview").hidden = true; $("document-previews").replaceChildren(); $("document-previews").hidden = true; $("approval").checked = false; $("run").disabled = true; $("plan-status").textContent = "Preview required"; }
function projectPath() { $("project-path").textContent = projects.find(p=>p.id === $("project").value)?.path || ""; }
async function loadProjects(selected) {
  const previous = $("project").value;
  projects = await api("/api/projects");
  $("project").replaceChildren(...projects.filter(row => row.available !== false && row.selectable !== false).map(row => {
    const option = document.createElement("option"); option.value = row.id; option.textContent = row.name || row.id; return option;
  }));
  if (projects.some(row => row.id === selected && row.available !== false && row.selectable !== false)) $("project").value = selected;
  if (previous !== $("project").value) { $("evidence").value = ""; $("images").value = ""; }
  projectPath();
}
function renderProjects() {
  $("saved-projects").replaceChildren(...projects.map(row => {
    const item = document.createElement("div"), label = document.createElement("p");
    label.className = "path"; label.textContent = row.path; item.append(label);
    if (row.available === false) {
      const status = document.createElement("p"); status.className = "warning";
      status.textContent = "Unavailable folder. Remove this registration or restore the folder and restart."; item.append(status);
    }
    if (row.removable) {
      if (row.configured_at_launch) {
        const scope = document.createElement("p"); scope.className = "warning";
        scope.textContent = "Also configured at launch. Removing this saved registration does not remove launch access.";
        item.append(scope);
      }
      const button = document.createElement("button"); button.textContent = `Remove ${row.name || row.id}`;
      button.disabled = running;
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          const result = await api("/api/projects/remove", {id:row.id, approved:true});
          invalidate(); await loadProjects($("project").value); renderProjects(); await refreshHostOptions();
          $("project-message").textContent = result.launch_access_remains
            ? "Saved registration removed. Launch access remains until you change the launch command. Files and history were not deleted."
            : "Project removed from the list. Files and usage history were not deleted.";
        } catch (error) { $("project-message").textContent = error.message; button.disabled = running; }
      });
      item.append(button);
    } else {
      const source = document.createElement("p"); source.className = "muted"; source.textContent = "Configured at launch"; item.append(source);
    }
    return item;
  }));
}
$("manage-projects").addEventListener("click", async () => {
  $("project-message").textContent = ""; $("project-consent").checked = false;
  $("projects-dialog").showModal();
  try {
    const previous = $("project").value;
    await loadProjects(previous); renderProjects();
    if (previous !== $("project").value) await refreshHostOptions();
  } catch (error) { $("project-message").textContent = error.message; }
});
$("close-projects").addEventListener("click", () => $("projects-dialog").close());
$("new-project-path").addEventListener("input", () => { $("project-consent").checked = false; });
$("choose-project").addEventListener("click", async () => {
  const original = $("new-project-path").value;
  $("choose-project").disabled = true; $("project-consent").checked = false;
  $("project-message").textContent = "Choose a folder on this computer. No project access has been granted.";
  try {
    const result = await api("/api/projects/choose", {open:true});
    if (result.status === "selected") {
      if (!$("projects-dialog").open || $("new-project-path").value !== original) return;
      $("new-project-path").value = result.path; $("project-consent").checked = false;
      $("project-message").textContent = "Folder selected. Review and approve access before adding it.";
    } else {
      $("project-message").textContent = result.status === "canceled" ? "Selection canceled. Nothing added." : result.status === "busy" ? "A folder chooser is already open on this computer." : "Folder chooser unavailable. Enter the absolute folder path instead.";
    }
  } catch (error) { $("project-message").textContent = "Folder chooser unavailable. Enter the absolute folder path instead."; }
  finally { $("choose-project").disabled = false; }
});
$("project-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!$("project-consent").checked) return;
  $("save-project").disabled = true;
  try {
    const row = await api("/api/projects/add", {path:$("new-project-path").value, approved:true});
    invalidate(); await loadProjects(row.id); await refreshHostOptions();
    $("project-consent").checked = false; renderProjects();
    $("project-message").textContent = "Project saved and selected. No model run started.";
  } catch (error) { $("project-message").textContent = error.message; }
  finally { $("save-project").disabled = false; }
});
$("task-form").addEventListener("input", invalidate);
$("project").addEventListener("change", projectPath);
function renderEfforts() {
  const select = $("effort"), previous = select.value || "low";
  const astraOnly = document.querySelector('input[name="mode"]:checked').value === "astra_preferred";
  const images = lines($("images").value).length > 0;
  const multi = $("strategy").value !== "direct";
  const models = hostModels.filter(row => (multi || !astraOnly || row.model === "gpt-6-astra") && (!images || row.input_modalities.includes("image")));
  const values = multi ? (models.length === 2 ? models[0].reasoning_efforts.filter(value=>models[1].reasoning_efforts.includes(value)) : []) : [...new Set(models.flatMap(row => row.reasoning_efforts))];
  select.replaceChildren(...values.map(value => {
    const option = document.createElement("option"); option.value = value;
    option.textContent = value.replaceAll("_", " ").replace(/^./, s => s.toUpperCase());
    return option;
  }));
  if (!values.includes(previous)) {
    const option = document.createElement("option"); option.value = previous;
    option.textContent = `${previous} (unavailable)`; option.disabled = true; select.prepend(option);
  }
  select.value = previous; select.disabled = false;
  select.setCustomValidity(values.includes(previous) ? "" : "Choose an available reasoning level; the previous choice was not changed.");
  $("effort-status").textContent = values.length ? (values.includes(previous) ? "Host-supported options" : "Previous choice unavailable. Select a supported level.") : "No compatible host options. Check setup.";
  renderContextProfile();
}
function renderContextProfile() {
  const focused = $("context-profile").value === "focused_catalog";
  const compatible = $("strategy").value === "direct" && $("effort").value === "low" && document.querySelector('input[name="mode"]:checked').value === "astra_preferred";
  $("context-profile").setCustomValidity(focused && !compatible ? "Focused catalog requires Direct, Astra Preferred and Low reasoning." : "");
  $("catalog-status").textContent = focused ? (compatible ? "Reduced skill discovery may omit useful guidance. Tools and safety rules remain enabled." : "Requires Direct, Astra Preferred and Low reasoning. Your selection has not been changed.") : "Inherited host configuration.";
  $("workflow-summary").textContent = `${$("strategy").selectedOptions[0].textContent} · ${document.querySelector('input[name="mode"]:checked').value === "astra_preferred" ? "Astra Preferred" : "Economy"} · ${$("effort").value} reasoning · ${focused ? "Focused discovery" : "Inherited discovery"}`;
}
$("context-profile").addEventListener("change", renderContextProfile);
async function refreshHostOptions() {
  const version = ++hostRevision;
  hostModels = []; invalidate(); $("effort").disabled = true; $("preview-button").disabled = true;
  $("effort-status").textContent = "Checking host...";
  try {
    const row = await api("/api/host-options", {project:$("project").value});
    if (version !== hostRevision) return;
    hostModels = row.models; renderEfforts();
  } catch (error) {
    if (version !== hostRevision) return;
    renderEfforts(); notice(error.message);
  } finally { if (version === hostRevision) $("preview-button").disabled = running; }
}
$("project").addEventListener("change", () => { $("evidence").value = ""; $("images").value = ""; refreshHostOptions(); });
document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener("change", renderEfforts));
$("images").addEventListener("input", renderEfforts);
$("strategy").addEventListener("change", renderEfforts);
$("effort").addEventListener("change", renderEfforts);
$("approval").addEventListener("change", () => { $("run").disabled = !preview || preview.execution_disabled === true || !$("approval").checked || running; });
$("task-form").addEventListener("submit", async event => {
  event.preventDefault(); if(running) return; invalidate(); $("preview-button").disabled = true; notice("Checking host and preparing preview...");
  const requestedRevision = revision;
  try {
    await previewCleanup;
    if (requestedRevision !== revision) return;
    const row = await api("/api/preview", {project:$("project").value, task:$("task").value, family:$("family").value, strategy:$("strategy").value, context_profile:$("context-profile").value, mode:document.querySelector('input[name="mode"]:checked').value, budget_credits:Number($("budget").value), effort:$("effort").value, evidence:lines($("evidence").value), images:lines($("images").value), context_allowance_tokens:Number($("context").value), output_allowance_tokens:Number($("output").value)});
    if (requestedRevision !== revision) { discardPreview(row.id); notice("Task changed while previewing. Review the updated task again."); return; }
    if ($("context-profile").value !== "inherit" && row.context_profile !== $("context-profile").value) {
      discardPreview(row.id);
      throw new Error("This server does not support the selected context profile. Restart with the matching release before running.");
    }
    if (!row.plan.selected) { discardPreview(row.id); $("plan-status").textContent="Needs a new plan: requested participation does not fit this budget."; notice("No run started. Review the budget and allowances."); return; }
    preview = row; $("preview").hidden = false; $("plan-status").textContent = "Ready for your approval";
    $("approval").disabled = row.execution_disabled === true;
    $("run").textContent = row.execution_disabled === true ? "Execution disabled" : "Approve and run";
    if (row.execution_disabled === true) $("plan-status").textContent = "Preview-only session. Model execution is disabled.";
    $("document-previews").replaceChildren(...(row.documents || []).map(document => {
      const section = window.document.createElement("section"), title = window.document.createElement("h3"), note = window.document.createElement("p"), text = window.document.createElement("pre");
      section.className = "document-excerpt"; title.textContent = document.name;
      note.textContent = `Extracted text, not the original layout. ${document.parser}. Review before approving.`;
      note.className = "muted"; text.textContent = document.text;
      section.append(title,note,text); return section;
    }));
    $("document-previews").hidden = !(row.documents || []).length;
    $("model").textContent = row.plan.selected.stages.map(stage=>stage.model).join(" then ");
    let breakdown = $("stage-breakdown");
    if (!breakdown) { breakdown = document.createElement("ol"); breakdown.id = "stage-breakdown"; $("model").after(breakdown); }
    breakdown.replaceChildren(...row.plan.selected.stages.map(stage=>{const li=document.createElement("li");li.textContent=`${stage.role}: ${stage.model}, ${money(stage.estimated_credits)} projected credits`;return li;}));
    const ceiling=row.plan.budget_credits, reserve=row.plan.reserve_credits, work=row.plan.selected.estimated_total_credits-reserve;
    $("work-cost").textContent=money(work); $("reserve-cost").textContent=money(reserve); $("ceiling").textContent=money(ceiling);
    const canvas=$("cost-chart"), context=canvas.getContext("2d"); context.clearRect(0,0,800,40); context.fillStyle="#edf0f1";context.fillRect(0,0,800,40);context.fillStyle="#176747";context.fillRect(0,0,800*work/ceiling,40);context.fillStyle="#aeb7bc";context.fillRect(800*work/ceiling,0,800*reserve/ceiling,40);
    canvas.setAttribute("aria-label",`Estimated work ${money(work)}, contingency ${money(reserve)}, task ceiling ${money(ceiling)} estimated credits`);
    $("warnings").replaceChildren(...row.warnings.slice(1).map(text=>{const li=document.createElement("li");li.textContent=text;return li;})); notice("Preview prepared. No model run has started.");
  } catch(error) { if (requestedRevision === revision) showFieldError(error); } finally { $("preview-button").disabled=running; }
});
function showReceipt(row) {
  $("receipt").replaceChildren(); $("receipt").hidden=false;
  const stages = row.stages || [], usage = {...(row.usage || {})};
  if (!row.usage && stages.length) {
    for (const key of ["input_tokens", "cached_tokens", "output_tokens"]) {
      const counts = stages.map(stage => stage.usage?.[key]);
      const total = counts.reduce((sum, value) => sum + value, 0);
      if (counts.every(value => Number.isSafeInteger(value) && value >= 0) && Number.isSafeInteger(total)) usage[key] = total;
    }
  }
  const partial = row.status === "unknown_usage" || row.cost_complete === false;
  const fields = [[partial ? "Known input tokens" : "Input tokens",usage.input_tokens],[partial ? "Known cached tokens" : "Cached tokens",usage.cached_tokens],[partial ? "Known output tokens" : "Output tokens",usage.output_tokens],["Projected credits",partial ? "Unknown" : money(row.estimated_credits)],["Still reserved",money(row.budget?.reserved_credits)],["Weekly remaining","Unavailable"]];
  fields.push(["Skill discovery",row.context_profile === "focused_catalog" ? "Focused catalog (experimental)" : row.context_profile === "inherit" ? "Inherited" : "Unknown (not recorded)"]);
  const choice = row.what_changed;
  const facts = [
    ["Preview estimate (including reserve)", choice?.preview_estimated_credits == null ? "Unknown (not recorded)" : `${money(choice.preview_estimated_credits)} estimated credits`],
    ["Receipt-based estimate", partial ? "Unknown: incomplete accounting" : `${money(row.estimated_credits)} estimated credits; not a provider bill`],
    ["Forecast basis", choice?.estimate_basis === "provisional_allowances_not_measured" ? "Provisional allowances, not host-calibrated" : "Unknown (not recorded)"],
    ["Quality assessment", "Not independently assessed. Completion is not proof of answer quality."],
    ["Requested model", row.requested_model ?? "Unknown (not recorded)"],
    ["Host-configured model", row.host_configured_model ?? "See stage receipts; otherwise unknown"],
    ["Saved reasoning choice", choice?.reasoning ?? "Unknown (not recorded)"],
    ["Saved workflow", choice?.strategy ?? "Unknown (not recorded)"],
    ["Attached evidence", choice ? `${choice.attached_text_count} text documents; ${choice.attached_image_count} images` : "Unknown (not recorded)"],
    ["Evidence actually used", "Not verified. Attachment counts do not prove the model used every source."],
    ["Savings", "Unknown. No matched baseline is linked to this receipt."],
    ["Model identity", "Host configuration is not independent provider attestation."]
  ];
  $("what-changed").hidden = false;
  $("change-facts").replaceChildren(...facts.map(([name,value]) => {
    const item=document.createElement("div"), dt=document.createElement("dt"), dd=document.createElement("dd");
    dt.textContent=name; dd.textContent=value; item.append(dt,dd); return item;
  }));
  if (partial) {
    fields.push(["Known projected credits",money(row.known_estimated_credits)]);
    fields.push(["Accounting status","Incomplete. Additional usage may be unrecorded; reservations remain until reconciliation."]);
  }
  for(const [name,value] of fields) {const item=document.createElement("div"), dt=document.createElement("dt"), dd=document.createElement("dd");dt.textContent=name;dd.textContent=value ?? "Unknown";item.append(dt,dd);$("receipt").append(item);}
  for (const [index, stage] of (row.stages || []).entries()) {
    const item=document.createElement("div"), dt=document.createElement("dt"), dd=document.createElement("dd");
    item.className="stage-receipt"; dt.textContent=`Stage ${index+1}: ${stage.actual_model}`;
    dd.textContent=`Input ${stage.usage?.input_tokens ?? "Unknown"}; cached ${stage.usage?.cached_tokens ?? "Unknown"}; output ${stage.usage?.output_tokens ?? "Unknown"}; projected credits ${money(stage.credits)}`;
    item.append(dt,dd); $("receipt").append(item);
  }
}
async function watchTask(id) {
  if (watching) return;
  watching = true; activeId = id; running = true;
  $("run").disabled = true; $("preview-button").disabled = true;
  $("stop").hidden = false; $("reconnect").hidden = true;
  try {
    while (true) {
      const job = await api(`/api/jobs/${id}`);
      $("run-status").textContent = job.status.replaceAll("_", " ");
      if (job.stage_progress?.total) $("run-status").textContent += `: ${job.stage_progress.started} of ${job.stage_progress.total} stages started`;
      if (!["queued", "running", "stop_requested"].includes(job.status)) {
        if (job.result) {
          $("answer").textContent = job.result.answer || "No answer available; inspect the usage state before retrying.";
          showReceipt(job.result);
        } else {
          $("answer").textContent = job.error || "Task needs attention.";
        }
        running = false; activeId = null; invalidate();
        $("preview-button").disabled = false; $("stop").hidden = true;
        notice("Task reached a terminal state. Review the result and receipt.");
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) {
    $("reconnect").hidden = false;
    notice(`${error.message} Connection lost; task state is unknown. Reconnect instead of resubmitting.`);
  } finally { watching = false; }
}
$("run").addEventListener("click", async () => {
  if (!preview || preview.execution_disabled === true || !$("approval").checked || running) return;
  const id = preview.id; activeId = id; running = true;
  $("run").disabled = true; $("preview-button").disabled = true;
  $("run-status").textContent = "Submitting approved task...";
  $("answer").textContent = ""; $("receipt").hidden = true; $("what-changed").hidden = true;
  try {
    await api("/api/execute", {id, approved:true});
    await watchTask(id);
  } catch (error) {
    if ([400,401,403,413,415].includes(error.status)) {
      activeId=null; running=false; invalidate(); $("preview-button").disabled=false;
      notice(error.message);
    } else {
      $("reconnect").hidden = false;
      notice(`${error.message} Submission may have reached the server. Reconnect before retrying.`);
    }
  }
});
$("reconnect").addEventListener("click", () => { if (activeId) watchTask(activeId); });
$("stop").addEventListener("click", async () => {
  if (!activeId) return;
  try {
    $("stop").disabled = true;
    await api("/api/cancel", {id:activeId});
    notice("Local stop requested. Usage already consumed is not refunded.");
  } catch (error) { notice(error.message); }
  finally { $("stop").disabled = false; }
});
let fileTarget="evidence", fileDirectory=".", fileRows=[], fileRevision=0;
function renderFiles() {
  const query=$("file-filter").value.toLowerCase();
  $("file-entries").replaceChildren(...fileRows.filter(row=>row.name.toLowerCase().includes(query)).map(row=>{
    const button=document.createElement("button");
    button.textContent=(row.directory ? "Open " : "Add ")+row.name;
    button.addEventListener("click",()=>{
      if(row.directory) { browseFiles(row.path); return; }
      const selected=lines($(fileTarget).value);
      if(!selected.includes(row.path)) selected.push(row.path);
      $(fileTarget).value=selected.join("\n");
      $(fileTarget).dispatchEvent(new Event("input",{bubbles:true}));
      $("file-dialog").close(); notice("Selection updated. Previous approval cleared.");
    });
    return button;
  }));
}
async function browseFiles(directory) {
  const version=++fileRevision;
  $("file-message").textContent="Reading directory...";$("file-entries").replaceChildren();
  try {
    const row=await api("/api/files",{project:$("project").value,directory,images:fileTarget==="images"});
    if(version!==fileRevision || !$("file-dialog").open)return;
    fileDirectory=row.directory;fileRows=row.entries;$("file-path").textContent=row.directory;
    $("parent-folder").disabled=row.directory===".";
    $("file-filter").value="";
    $("file-message").textContent=row.truncated ? "Directory listing is partial. Enter an exact path for other files." : `${row.entries.length} entries`;
    renderFiles();
  }catch(error){$("file-message").textContent=error.message;}
}
function openPicker(target){fileTarget=target;$("file-title").textContent=target==="images" ? "Choose image" : "Choose evidence";$("file-dialog").showModal();browseFiles(".");}
$("browse-evidence").addEventListener("click",()=>openPicker("evidence"));
$("browse-images").addEventListener("click",()=>openPicker("images"));
$("close-picker").addEventListener("click",()=>$("file-dialog").close());
$("file-filter").addEventListener("input",renderFiles);
$("parent-folder").addEventListener("click",()=>browseFiles(fileDirectory.split("/").slice(0,-1).join("/") || "."));
let usageRevision = 0;
async function usage() {
  const current = ++usageRevision;
  $("usage-status").textContent = "Loading receipts...";
  $("usage-empty").hidden = true;
  $("history").closest(".table-scroll").hidden = true;
  try {
    const rows = await api("/api/history");
    if (current !== usageRevision) return;
    $("usage-status").textContent = rows.length ? `${rows.length} recorded tasks. Missing counters remain unknown.` : "No recorded tasks yet.";
    $("history").closest(".table-scroll").hidden = !rows.length;
    $("usage-empty").hidden = !!rows.length;
    $("usage-empty-title").textContent = preview ? "Preview only. No recorded run." : "Your first receipt starts with a task.";
    $("usage-empty-detail").textContent = preview?.execution_disabled === true
      ? "This session cannot execute models. Preview estimates are not consumed credits. Usage from other Codex chats is not collected here."
      : "Previews do not create usage receipts. An explicitly approved Workbench run creates a record; unavailable counters stay unknown. Other Codex chats are not automatically tracked.";
    $("history").replaceChildren(...rows.map(row => {
      const tr = document.createElement("tr");
      for (const value of [row.id.slice(0,8), row.status, row.requested_model || "Unknown", row.usage?.input_tokens ?? "Unknown", row.usage?.cached_tokens ?? "Unknown", row.usage?.output_tokens ?? "Unknown", money(row.estimated_credits)]) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      const action = document.createElement("td");
      const inspect = document.createElement("button");
      inspect.textContent = "View receipt";
      inspect.disabled = running;
      inspect.addEventListener("click",()=>{
        tab("task");
        $("answer").textContent = "Historical usage receipt. The answer is not stored in this history view.";
        $("run-status").textContent = row.status;
        showReceipt(row);
        $("result-section").scrollIntoView({block:"start"});
      });
      action.append(inspect);
      if (row.status === "unknown_usage") {
        const button = document.createElement("button");
        button.textContent = "Recover recorded usage";
        button.title = "Reconcile a recorded terminal host receipt without rerunning the task. Missing evidence stays unresolved.";
        button.disabled = running;
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            const result = await api("/api/reconcile", {id:row.id, approved:true});
            notice(result.message); await usage();
          } catch (error) { notice(error.message); button.disabled = running; }
        });
        action.append(button);
      }
      tr.append(action); return tr;
    }));
  } catch (error) { if (current === usageRevision) { $("history").replaceChildren(); $("usage-status").textContent = `Receipts unavailable: ${error.message}. Refresh to retry loading; do not rerun the task to recover a receipt.`; } }
}
$("usage-work").addEventListener("click",()=>tab("task"));
function tab(name) {
  for (const view of ["task", "usage", "evidence", "settings"]) {
    $(`${view}-view`).hidden = view !== name;
    $(`${view}-tab`).setAttribute("aria-pressed", String(view === name));
  }
  $("result-section").hidden = name !== "task";
  if (name === "usage") { usage(); loadObservations(); loadDigest(); }
  if (name === "settings") loadDigest();
}
for (const name of ["task", "usage", "evidence", "settings"]) $(`${name}-tab`).addEventListener("click", () => tab(name));
$("refresh-usage").addEventListener("click", usage);
let digestRevision = 0, digestSaving = false;
function clearDigest() {
  $("digest-result").hidden = true;
  $("digest-summary").replaceChildren(); $("digest-sources").replaceChildren();
}
async function loadDigest() {
  if (digestSaving) return;
  const version = ++digestRevision;
  clearDigest(); $("digest-enabled").disabled = true;
  $("digest-status").textContent = "Loading digest...";
  $("digest-preference-status").textContent = "Checking local preference...";
  try {
    const result = await api("/api/usage-digest");
    if (version !== digestRevision) return;
    $("digest-enabled").checked = result.enabled;
    $("digest-enabled").disabled = false;
    $("digest-preference-status").textContent = result.enabled ? "Local digest enabled." : "Local digest disabled.";
    if (!result.enabled) { $("digest-status").textContent = "Digest is off. Existing receipts are unchanged."; return; }
    const report = result.report;
    $("digest-status").textContent = report.observation_count ? `${report.observation_count} observation${report.observation_count === 1 ? "" : "s"} recorded in the last seven days.` : "No observations recorded in the last seven days.";
    $("digest-window").textContent = `${new Date(report.window_start).toLocaleString()} to ${new Date(report.window_end).toLocaleString()} (recording dates, not execution dates)`;
    const metrics = [["Sources seen",report.source_count],["Incomplete observations",report.incomplete_observation_count],["Undated tasks excluded",report.undated_tasks_excluded],["Weekly spend","Unknown"]];
    for (const [label,value] of metrics) {
      const group = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
      dt.textContent = label; dd.textContent = value; group.append(dt,dd); $("digest-summary").append(group);
    }
    $("digest-sources").replaceChildren(...report.latest_sources.map(source => {
      const tr = document.createElement("tr");
      for (const value of [source.source,source.recorded_model,source.ambiguous ? "Ambiguous" : source.counter_kind,source.input_tokens ?? "Unknown",source.cached_tokens ?? "Unknown",source.output_tokens ?? "Unknown"]) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      return tr;
    }));
    if (report.sources_truncated || report.future_observations) $("digest-status").textContent += ` ${report.sources_truncated ? "Newest 100 sources shown. " : ""}${report.future_observations ? `${report.future_observations} future-dated observations excluded.` : ""}`;
    $("digest-result").hidden = false;
  } catch (error) {
    if (version !== digestRevision) return;
    clearDigest(); $("digest-enabled").checked = false;
    $("digest-status").textContent = "Digest unavailable. Refresh to retry; no records changed.";
    $("digest-preference-status").textContent = "Preference could not be verified. Refresh the digest in Usage.";
  }
}
$("refresh-digest").addEventListener("click", loadDigest);
$("digest-enabled").addEventListener("change", async () => {
  const enabled = $("digest-enabled").checked;
  digestSaving = true; ++digestRevision; clearDigest(); $("digest-enabled").disabled = true;
  $("digest-preference-status").textContent = "Saving local preference...";
  try {
    await api("/api/usage-digest/settings", {enabled,approved:true});
    digestSaving = false; await loadDigest();
  } catch (error) {
    digestSaving = false;
    $("digest-preference-status").textContent = "Save outcome could not be verified. Refresh the digest in Usage before changing it again.";
    $("digest-status").textContent = "Preference needs verification. Refresh to retry.";
  }
});
let observationRevision = 0, observationPending = null;
let retentionRevision = 0, retentionPlan = null;
function clearRetention() {
  retentionRevision++; retentionPlan = null;
  $("retention-preview").hidden = true; $("retention-preview").textContent = "";
  $("retention-consent").checked = false; $("retention-consent").disabled = true; $("apply-retention").disabled = true;
}
async function loadObservations() {
  $("observation-list-status").textContent = "Loading journal...";
  try {
    const result = await api("/api/observations");
    $("observation-list").replaceChildren(...result.observations.map(row => {
      const tr = document.createElement("tr");
      for (const value of [row.observation_id.slice(0,12), row.recorded_at, row.coverage, row.receipt_count ?? "Unknown", money(row.estimated_credits)]) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      return tr;
    }));
    $("observation-list-status").textContent = result.observations.length ? `${result.observations.length} observations${result.truncated ? " (newest 100)" : ""}. Snapshots may overlap; do not add them together.` : "No saved observations.";
  } catch (error) { $("observation-list").replaceChildren(); $("observation-list-status").textContent = "Journal unavailable. No records were changed."; }
}
$("refresh-usage").addEventListener("click", loadObservations);
$("observation-file").addEventListener("change", async () => {
  const version = ++observationRevision, file = $("observation-file").files[0];
  observationPending = null; $("observation-consent").checked = false; $("observation-consent").disabled = true;
  $("save-observation").disabled = true; $("observation-preview").hidden = true;
  $("observation-content").textContent = "";
  if (!file) { $("observation-status").textContent = "No observation loaded."; return; }
  try {
    if (file.size > 61440) throw new Error("Receipt packet exceeds 60 KB.");
    let packet;
    try { packet = JSON.parse(await file.text()); } catch { throw new Error("A valid JSON receipt packet is required."); }
    const preview = await api("/api/observations/preview", packet);
    if (version !== observationRevision) return;
    observationPending = {packet, id:preview.id, fingerprint:preview.fingerprint};
    $("observation-content").textContent = JSON.stringify(preview.report, null, 2);
    $("observation-preview").hidden = false; $("observation-preview").open = true;
    $("observation-consent").disabled = false;
    $("observation-status").textContent = "Preview only. Unknown usage remains unknown; local identifiers may be sensitive.";
  } catch (error) { if (version === observationRevision) $("observation-status").textContent = error.message; }
});
$("observation-consent").addEventListener("change", () => { $("save-observation").disabled = !observationPending || !$("observation-consent").checked; });
$("save-observation").addEventListener("click", async () => {
  if (!observationPending || !$("observation-consent").checked) return;
  const request = observationPending, version = observationRevision;
  $("save-observation").disabled = true;
  try {
    await api("/api/observations/import", {...request, approved:true});
    clearRetention(); await loadObservations(); await loadDigest();
    if (version !== observationRevision) return;
    observationPending = null; $("observation-consent").checked = false; $("observation-consent").disabled = true;
    $("observation-status").textContent = "Observation saved. No model run started.";
  } catch (error) { if (version === observationRevision) { $("observation-status").textContent = error.message; $("save-observation").disabled = !$("observation-consent").checked; } }
});
$("retention-before").addEventListener("input", clearRetention);
$("preview-retention").addEventListener("click", async () => {
  clearRetention(); const version = retentionRevision;
  try {
    const date = $("retention-before").value;
    if (!date) throw new Error("Choose a cutoff date.");
    const plan = await api("/api/observations/retention", {action:"preview", before:new Date(`${date}T00:00:00`).toISOString()});
    if (version !== retentionRevision) return;
    retentionPlan = plan; $("retention-preview").textContent = JSON.stringify(plan, null, 2); $("retention-preview").hidden = false;
    $("retention-status").textContent = `${plan.remove_count} observations selected. Nothing removed yet.`;
    $("retention-consent").disabled = plan.remove_count === 0;
  } catch (error) { if (version === retentionRevision) $("retention-status").textContent = error.message; }
});
$("retention-consent").addEventListener("change", () => { $("apply-retention").disabled = !retentionPlan || !$("retention-consent").checked; });
$("apply-retention").addEventListener("click", async () => {
  if (!retentionPlan || !$("retention-consent").checked) return;
  const plan = retentionPlan; clearRetention();
  try {
    const result = await api("/api/observations/retention", {action:"apply", plan, approved:true});
    $("retention-status").textContent = `${result.removed} observations removed. Backup: ${result.backup_path || "Not needed"}`;
    await loadObservations();
    await loadDigest();
  } catch (error) { $("retention-status").textContent = `${error.message} Preview again before retrying.`; }
});
$("settings-projects").addEventListener("click", () => $("manage-projects").click());
$("settings-check").addEventListener("click", () => $("check").click());
let experimentRevision = 0;
let experimentExport = null;
const reviewExport = document.createElement("button");
reviewExport.id = "review-export"; reviewExport.textContent = "Review export"; reviewExport.hidden = true;
$("experiment-status").insertAdjacentElement("afterend", reviewExport);
reviewExport.addEventListener("click", () => {
  if (!experimentExport) return;
  $("export-content").textContent = experimentExport;
  $("export-consent").checked = false; $("download-experiment").disabled = true;
  $("export-dialog").showModal();
});
$("close-export").addEventListener("click", () => $("export-dialog").close());
$("export-consent").addEventListener("change", () => {
  $("download-experiment").disabled = !$("export-consent").checked || !experimentExport;
});
$("download-experiment").addEventListener("click", () => {
  if (!experimentExport || !$("export-consent").checked) return;
  const url = URL.createObjectURL(new Blob([experimentExport], {type:"application/json"}));
  const link = document.createElement("a"); link.href = url; link.download = "governor-experiment-summary.json";
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("experiment-file").addEventListener("change", async () => {
  const current = ++experimentRevision, file = $("experiment-file").files[0];
  experimentExport = null; reviewExport.hidden = true;
  $("export-dialog").close(); $("export-content").textContent = "";
  $("export-consent").checked = false; $("download-experiment").disabled = true;
  $("experiment-result").hidden = true;
  $("experiment-summary").replaceChildren(); $("experiment-rows").replaceChildren();
  if (!file) { $("experiment-status").textContent = "No comparison loaded."; return; }
  $("experiment-status").textContent = "Checking comparison...";
  try {
    if (file.size > 65536) throw new Error("Comparison exceeds 64 KB.");
    let packet;
    try { packet = JSON.parse(await file.text()); } catch { throw new Error("A valid JSON comparison packet is required."); }
    const result = await api("/api/experiments/compare", packet);
    if (current !== experimentRevision) return;
    if (result.export_preview) {
      experimentExport = JSON.stringify(result.export_preview, null, 2) + "\n";
      reviewExport.hidden = false;
    }
    $("experiment-status").textContent = result.recommendation.replaceAll("_", " ");
    for (const [label, value] of [["Enrollment", result.enrollment?.status || "Not supplied"], ["Missing planned runs", result.enrollment?.missing_runs ?? "Unknown"], ["Policy promotion", "Not automatic"]]) {
      const block = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
      dt.textContent = label; dd.textContent = value; block.append(dt, dd); $("experiment-summary").append(block);
    }
    for (const row of result.comparisons) {
      const tr = document.createElement("tr");
      for (const value of [row.arm, row.matched_cost_pairs, row.quality_regressions ?? "Unknown", money(row.mean_credit_difference), (row.cost_bases || []).join(", ") || "Unknown", row.coverage?.fully_matched ? "Matched supplied runs" : "Incomplete"] ) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      $("experiment-rows").append(tr);
    }
    $("experiment-result").hidden = false;
  } catch (error) { if (current === experimentRevision) $("experiment-status").textContent = error.message; }
});
let setupReport = null;
function diagnosticSummary(row) {
  // Export only constrained scalars, never the raw API response or UI state.
  const version = value => typeof value === "string" && /^\d+\.\d+\.\d+(?:(?:rc|a|b)\d+|[-+][\w.-]{1,40})?$/.test(value) ? value : null;
  const category = (value, allowed) => allowed.includes(value) ? value : "unknown";
  return {
    schema_version: 1, governor_version: version(row.governor_version),
    python_version: version(row.python?.version), codex_version: version(row.codex?.version),
    mcp_version: version(row.mcp?.version),
    codex_found: row.codex?.found === true, mcp_installed: row.mcp?.installed === true,
    authentication: category(row.authentication?.status, ["available", "unavailable", "missing", "not_checked", "unknown"]),
    model_execution: category(row.model_execution, ["preflight_ready", "needs_attention", "not_checked"]),
    model_access_verified: false, model_calls_started: 0
  };
}
$("close-setup").addEventListener("click", () => $("setup-dialog").close());
$("download-diagnostics").addEventListener("click", () => {
  if (!setupReport) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(setupReport, null, 2) + "\n"], {type:"application/json"}));
  const link = document.createElement("a"); link.href = url; link.download = "governor-setup-report.json";
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("check").addEventListener("click", async () => {
  setupReport = null; $("download-diagnostics").disabled = true; $("setup-next").replaceChildren();
  $("setup-status").textContent = "Checking local setup..."; $("setup-dialog").showModal();
  try {
    $("check").disabled = true;
    const row = await api("/api/doctor", {}); setupReport = diagnosticSummary(row);
    $("setup-status").textContent = `Setup: ${setupReport.model_execution.replaceAll("_", " ")}. Authentication: ${setupReport.authentication}. Model access is not verified.`;
    const steps = [];
    if (!setupReport.codex_found) steps.push("Install the official Codex CLI and make it available on PATH.");
    else if (!setupReport.codex_version) steps.push("Check the Codex CLI version in your terminal; it could not be verified.");
    if (setupReport.authentication === "unavailable") steps.push("Run codex login in your own terminal, then check setup again.");
    if (setupReport.authentication === "unknown") steps.push("The login check was inconclusive. Resolve any CLI timeout and check again.");
    if (!setupReport.mcp_installed) steps.push("MCP is optional for this workbench; install it only for an MCP client connection.");
    $("setup-next").replaceChildren(...steps.map(text => { const li = document.createElement("li"); li.textContent = text; return li; }));
    $("download-diagnostics").disabled = false;
    await refreshHostOptions();
  } catch (error) { $("setup-status").textContent = error.message; }
  finally { $("check").disabled = false; }
});
(async () => {
  if (!token) { notice("Session key missing. Reopen the private launch link to reconnect; refreshing does not stop a task."); $("preview-button").disabled=true; return; }
  try {
    await loadProjects();
    await refreshHostOptions();
    const jobs = await api("/api/jobs");
    const active = jobs.find(row => ["queued", "running", "stop_requested"].includes(row.status));
    if (active) { notice("Reconnected to the existing task. No new submission."); watchTask(active.id); }
    else { notice("Local session connected. No run started."); }
  } catch (error) { notice(error.message); $("preview-button").disabled=true; }
})();

// Field help is local UI content; opening it never submits or changes a task.
(() => {
  const help = {
    project: ["Project", "Choose the folder this task may read. Read-only tools can inspect files beyond the evidence you attach. Use a non-sensitive sample when trying the app."],
    task: ["Task", "Describe the result you want and what would count as finished. Name any required sources. Clear acceptance criteria help avoid unnecessary extra work."],
    family: ["Task type", "Classifies the work for planning and policy checks. General is a starting point when no category fits; changing this does not run a model."],
    strategy: ["Workflow", "Direct sends the task to the selected model. The other choices add a Sol preparation or draft stage before Astra. Extra stages can cost more; keep Direct unless the additional stage has a clear purpose."],
    effort: ["Reasoning", "Requests a reasoning level supported by your Codex host. Higher levels may suit harder problems but can use more time and tokens. Low is not proven sufficient for every task; choose the depth the task needs."],
    "context-profile": ["Skill discovery", "Inherited keeps the host's normal skill discovery. Focused catalog is experimental and can omit useful guidance; it currently requires Direct, Astra Preferred and Low reasoning. Leave Inherited selected unless you are testing that trade-off."],
    budget: ["Task budget", "A planning and admission allowance in estimated credits, not dollars or a percentage of your weekly limit. It includes contingency. It is not a provider-enforced cap, and actual usage can exceed the estimate."],
    evidence: ["Evidence", "Select the documents the task should consider using Browse files, or enter one project-relative path per line. A file is selected only when its name appears here. Selection alone does not start a model run."],
    images: ["Images", "Choose images the model needs to inspect, such as a chart or screenshot. Use Browse images or one project-relative path per line. Image support is checked against the chosen host and model."],
    context: ["Host context tokens", "An estimate of the instructions, tools and other context the host adds. It is not a limit on what the host sends. Keep the provisional value until you have an applicable measured receipt; lowering it only lowers the estimate."],
    output: ["Output tokens", "An allowance used to estimate generated tokens, including reasoning where the host counts it as output. It does not enforce an output cap. Use a realistic allowance for the required work."],
    approval: ["Execution approval", "Approves the reviewed task and estimated spend. Changing task inputs requires a new preview. This control stays disabled in a preview-only session; installing the app does not approve any model runs."],
    "experiment-file": ["Comparison packet", "Load a supported JSON experiment packet to compare supplied task outcomes and costs locally. It is not a source document for a model task. Missing or self-reported results do not prove independent savings."],
    "observation-file": ["Receipt packet", "Load a supported JSON usage packet for local review. This does not automatically collect other chats or upload your conversation. Review the proposed record before saving."],
    "observation-consent": ["Save observation", "Allows the reviewed usage observation to be written to this local journal. It does not settle a model budget or prove savings."],
    "digest-enabled": ["Usage digest", "Shows saved observations from the last seven recording days. It does not run background collection or email reports, and it is not your account's weekly bill. Turning it off keeps existing records."],
    "retention-before": ["Cleanup date", "Select the local-date cutoff for old observation records. Preview the affected records before removal. Project files and budget leases are not included."],
    "retention-consent": ["Cleanup approval", "Approves only the previewed cleanup after a verified backup. The backup still contains the removed records, so cleanup is not secure erasure."],
    "file-filter": ["Filter names", "Narrow the displayed files by name. This filters the list; it does not select or attach a file. Choose a file and check that it appears in Evidence or Images."],
    "new-project-path": ["Project folder", "Choose a folder on this computer. Review the full path before approving access. Adding a project does not start a model task or modify its files."],
    "project-consent": ["Project access approval", "Allows this local Workbench to use the specified folder. Read-only model tools may inspect the folder beyond attached excerpts. This is separate from approving a model run."],
    "export-consent": ["Export review", "Confirm that you reviewed the summary for sensitive information before downloading it. Numbers and identifiers can still reveal an experiment. Downloading is not permission to publish."],
  };
  const dialog = document.createElement("dialog"); dialog.id = "field-help-dialog";
  dialog.setAttribute("aria-labelledby", "field-help-title");
  const title = document.createElement("h2"), description = document.createElement("p"), close = document.createElement("button");
  title.id = "field-help-title"; description.id = "field-help-description";
  dialog.setAttribute("aria-describedby", description.id);
  close.type = "button"; close.textContent = "Close help";
  close.addEventListener("click", () => dialog.close());
  dialog.append(title, description, close); document.body.append(dialog);
  const tooltip = document.createElement("div"); tooltip.id = "field-help-tooltip";
  tooltip.setAttribute("role", "tooltip"); tooltip.setAttribute("popover", "manual");
  document.body.append(tooltip);
  let hoverTimer;
  const keepHover = () => clearTimeout(hoverTimer);
  function hideHover() { keepHover(); if (tooltip.matches(":popover-open")) tooltip.hidePopover(); }
  const leaveHover = () => { keepHover(); hoverTimer = setTimeout(hideHover, 3000); };
  function showHover(button, name, text) {
    if (dialog.open) return;
    keepHover(); tooltip.textContent = `${name}: ${text}`;
    if (!tooltip.matches(":popover-open")) tooltip.showPopover();
    const anchor = button.getBoundingClientRect(), box = tooltip.getBoundingClientRect();
    tooltip.style.left = `${Math.max(12, Math.min(anchor.left, innerWidth - box.width - 12))}px`;
    const below = anchor.bottom + 8;
    tooltip.style.top = `${Math.max(12, below + box.height <= innerHeight - 12 ? below : anchor.top - box.height - 8)}px`;
  }
  tooltip.addEventListener("pointerenter", keepHover);
  tooltip.addEventListener("pointerleave", leaveHover);
  document.addEventListener("keydown", event => { if (event.key === "Escape") hideHover(); });
  window.addEventListener("resize", hideHover);
  document.addEventListener("scroll", event => { if (!tooltip.contains(event.target)) hideHover(); }, true);
  function attach(anchor, controls, name, text, id) {
    const button = document.createElement("button"), note = document.createElement("span");
    button.type = "button"; button.className = "field-help-button"; button.textContent = "?";
    button.setAttribute("aria-label", `Help: ${name}`); button.setAttribute("aria-haspopup", "dialog");
    note.id = `help-${id}`; note.className = "screen-reader-only"; note.textContent = text;
    document.body.append(note);
    button.setAttribute("aria-describedby", note.id);
    button.addEventListener("pointerenter", event => { if (event.pointerType === "mouse") showHover(button, name, text); });
    button.addEventListener("pointerleave", leaveHover);
    for (const control of controls) control.setAttribute("aria-describedby", [control.getAttribute("aria-describedby"), note.id].filter(Boolean).join(" "));
    button.addEventListener("click", event => {
      event.preventDefault(); event.stopPropagation(); hideHover(); title.textContent = name; description.textContent = text; dialog.showModal();
    });
    if (anchor.tagName === "LABEL") {
      const row = document.createElement("div"); row.className = "field-help-label";
      anchor.before(row); row.append(anchor, button);
    } else anchor.append(button);
  }
  for (const [id, [name, text]] of Object.entries(help)) {
    const control = $(id), label = document.querySelector(`label[for="${id}"]`) || control?.closest("label");
    if (control && label) attach(label, [control], name, text, id);
  }
  attach(document.querySelector(".mode legend"), [...document.querySelectorAll('input[name="mode"]')], "Mode",
    "Astra Preferred preserves Astra participation when planning. Economy can select a cheaper model. Review the selected model before approval; this does not change the active model in other chats.", "mode");
  const summary = document.querySelector("#advanced-task summary");
  attach(summary, [], "Advanced workflow",
    "Optional controls for task type, workflow stages, model preference, reasoning and skill discovery. Opening this section changes nothing. Direct Astra with inherited discovery avoids extra model handoffs; choose reasoning appropriate to your task.", "advanced");
})();
