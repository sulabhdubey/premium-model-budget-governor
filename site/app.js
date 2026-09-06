const form = document.querySelector("#route-form");
const budget = document.querySelector("#remaining-budget");
const budgetOutput = document.querySelector("#budget-output");
const result = document.querySelector(".route-result");
const menuButton = document.querySelector(".menu-button");
const mobileMenu = document.querySelector("#mobile-menu");

const labels = { "astra-direct": "Astra direct", "astra-leads-terra-builds": "Astra-led hybrid", "sol-only": "Sol direct" };

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function budgetMode(remaining) {
  if (remaining <= 15) return "Emergency mode";
  if (remaining <= 30) return "Conserve mode";
  return "Normal mode";
}

function routeTask() {
  const mode = document.querySelector("#workflow-mode").value;
  const floor = document.querySelector("#host-context").value;
  const ceiling = Number(document.querySelector("#task-budget").value);
  const remaining = Number(budget.value);
  const ready = document.querySelector("#evidence-ready").checked;
  const approved = document.querySelector("#explicit-approval").checked;
  budgetOutput.value = `${remaining}%`;
  setText("#result-mode", budgetMode(remaining));
  const candidates = window.DEMO_WORKFLOWS[floor] || [];
  const eligible = candidates.filter(c => (mode !== "astra_preferred" || c.astra_roles.length)
    && (!c.astra_roles.length || (ready && (remaining > 15 || approved))));
  eligible.sort((a, b) => a.estimated_total_credits - b.estimated_total_credits);
  const selected = floor !== "0" && Number.isFinite(ceiling) && ceiling >= 0
    ? eligible.find(c => c.estimated_total_credits <= ceiling) : null;
  result.dataset.state = selected ? (selected.astra_roles.length ? "premium" : "efficient") : "blocked";
  setText("#recommended-model", selected ? labels[selected.id] : "Needs replan");
  setText("#decision-label", selected ? "Workflow fits estimate" : "No silent model fallback");
  setText("#decision-reason", selected
    ? "This complete illustrative workflow fits, including verification, host input, and contingency. No model has been called."
    : floor === "0" ? "Measure host input before treating a short prompt as a cheap call."
    : !ready && mode === "astra_preferred" ? "Prepare the required evidence, then compare Astra workflows again."
    : remaining <= 15 && !approved && mode === "astra_preferred" ? "Astra needs explicit approval at emergency capacity."
    : "No eligible workflow fits this budget. Reduce redundant work or revise the budget.");
  setText("#turns-allowed", selected ? String(selected.astra_roles.length) : "0");
  setText("#context-action", floor === "0" ? "Measure first" : ready ? "Evidence prepared" : "Prepare evidence");
  setText("#approval-gate", approved ? "Approved" : remaining <= 15 ? "Required for Astra" : "Policy satisfied");
  setText("#parity-value", selected ? `${selected.estimated_total_credits.toFixed(2)} / ${ceiling.toFixed(2)}` : "Not feasible");
  document.querySelector("#meter-fill").style.width = selected && ceiling > 0
    ? `${Math.min(100, selected.estimated_total_credits / ceiling * 100)}%` : "0%";
}

budget.addEventListener("input", routeTask);
form.addEventListener("submit", (event) => {
  event.preventDefault();
  routeTask();
});
form.addEventListener("change", routeTask);
form.addEventListener("input", routeTask);

menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!open));
  mobileMenu.hidden = open;
});

mobileMenu.addEventListener("click", () => {
  menuButton.setAttribute("aria-expanded", "false");
  mobileMenu.hidden = true;
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !mobileMenu.hidden) {
    menuButton.setAttribute("aria-expanded", "false");
    mobileMenu.hidden = true;
    menuButton.focus();
  }
});

document.querySelector("#copy-command").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const command = document.querySelector("#install-command").textContent;
  try {
    await navigator.clipboard.writeText(command);
    button.textContent = "Copied";
    button.setAttribute("aria-label", "Install command copied");
    document.querySelector("#copy-status").textContent = "Install command copied.";
  } catch {
    button.textContent = "Select command";
    button.setAttribute("aria-label", "Select and copy the install command");
    document.querySelector("#copy-status").textContent = "Clipboard unavailable. Select the command to copy it.";
  }
  window.setTimeout(() => {
    button.textContent = "Copy";
    button.setAttribute("aria-label", "Copy install command");
  }, 1600);
});

routeTask();
