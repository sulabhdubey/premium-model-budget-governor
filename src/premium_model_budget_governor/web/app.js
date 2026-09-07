"use strict";
const $ = id => document.getElementById(id);
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
const errorFields = ["project", "task", "budget", "evidence", "images", "context", "output", "effort"];
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
function invalidate() { revision++; clearFieldErrors(); if (!running) discardPreview(preview?.id); preview = null; $("preview").hidden = true; $("approval").checked = false; $("run").disabled = true; $("plan-status").textContent = "Preview required"; }
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
}
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
$("approval").addEventListener("change", () => { $("run").disabled = !preview || !$("approval").checked || running; });
$("task-form").addEventListener("submit", async event => {
  event.preventDefault(); if(running) return; invalidate(); $("preview-button").disabled = true; notice("Checking host and preparing preview...");
  const requestedRevision = revision;
  try {
    await previewCleanup;
    if (requestedRevision !== revision) return;
    const row = await api("/api/preview", {project:$("project").value, task:$("task").value, family:$("family").value, strategy:$("strategy").value, mode:document.querySelector('input[name="mode"]:checked').value, budget_credits:Number($("budget").value), effort:$("effort").value, evidence:lines($("evidence").value), images:lines($("images").value), context_allowance_tokens:Number($("context").value), output_allowance_tokens:Number($("output").value)});
    if (requestedRevision !== revision) { discardPreview(row.id); notice("Task changed while previewing. Review the updated task again."); return; }
    if (!row.plan.selected) { discardPreview(row.id); $("plan-status").textContent="Needs a new plan: requested participation does not fit this budget."; notice("No run started. Review the budget and allowances."); return; }
    preview = row; $("preview").hidden = false; $("plan-status").textContent = "Ready for your approval";
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
  if (!preview || !$("approval").checked || running) return;
  const id = preview.id; activeId = id; running = true;
  $("run").disabled = true; $("preview-button").disabled = true;
  $("run-status").textContent = "Submitting approved task...";
  $("answer").textContent = ""; $("receipt").hidden = true;
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
async function usage() {
  try {
    const rows = await api("/api/history");
    $("history").replaceChildren(...rows.map(row => {
      const tr = document.createElement("tr");
      for (const value of [row.id.slice(0,8), row.status, row.requested_model || "Unknown", row.usage?.input_tokens ?? "Unknown", row.usage?.cached_tokens ?? "Unknown", row.usage?.output_tokens ?? "Unknown", money(row.estimated_credits)]) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      const action = document.createElement("td");
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
      } else { action.textContent = "Not required"; }
      tr.append(action); return tr;
    }));
  } catch (error) { notice(error.message); }
}
function tab(name){const task=name==="task";$("task-view").hidden=!task;$("result-section").hidden=!task;$("usage-view").hidden=task;$("task-tab").setAttribute("aria-pressed",String(task));$("usage-tab").setAttribute("aria-pressed",String(!task));if(!task)usage();}
$("task-tab").addEventListener("click",()=>tab("task"));$("usage-tab").addEventListener("click",()=>tab("usage"));
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
