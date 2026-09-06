const form = document.querySelector("#route-form");
const budget = document.querySelector("#remaining-budget");
const budgetOutput = document.querySelector("#budget-output");
const result = document.querySelector(".route-result");
const menuButton = document.querySelector(".menu-button");
const mobileMenu = document.querySelector("#mobile-menu");

const labels = {
  "gpt-6-astra": "GPT-6 Astra",
  "gpt-5.6-sol": "GPT-5.6 Sol",
  "gpt-5.6-terra": "GPT-5.6 Terra",
};

const premiumReasons = new Set(["frontier_architecture", "critical_security", "final_release_review"]);
const lowLeverage = new Set(["repo_exploration", "implementation"]);

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function budgetMode(remaining) {
  if (remaining <= 15) return "Emergency mode";
  if (remaining <= 30) return "Conserve mode";
  return "Normal mode";
}

function routeTask() {
  const requested = document.querySelector("#requested-model").value;
  const task = document.querySelector("#task-type").value;
  const remaining = Number(budget.value);
  const broad = document.querySelector("#broad-context").checked;
  const approved = document.querySelector("#explicit-approval").checked;

  budgetOutput.value = `${remaining}%`;
  setText("#result-mode", budgetMode(remaining));
  setText("#parity-value", "40%");
  document.querySelector("#meter-fill").style.width = "40%";

  if (requested !== "gpt-6-astra") {
    result.dataset.state = "efficient";
    setText("#recommended-model", labels[requested]);
    setText("#decision-label", "Allow non-premium route");
    setText("#decision-reason", "The requested model is already an efficient execution route. The premium gate is not needed.");
    setText("#turns-allowed", "0 premium");
    setText("#context-action", broad ? "Profile first" : "Proceed");
    setText("#approval-gate", "Not required");
    return;
  }

  if (broad || lowLeverage.has(task)) {
    result.dataset.state = "blocked";
    setText("#recommended-model", "GPT-5.6 Sol");
    setText("#decision-label", "Block broad Astra work");
    setText("#decision-reason", broad
      ? "Broad context must be explored and compressed before Astra sees it. Sol can execute while evidence is ranked and scanned."
      : "This task shape is execution-heavy. Use Sol, then escalate only an unresolved decision.");
    setText("#turns-allowed", "0");
    setText("#context-action", "Compress");
    setText("#approval-gate", remaining <= 15 ? "Required after compression" : "Not yet eligible");
    return;
  }

  if (remaining <= 15 && !approved) {
    result.dataset.state = "blocked";
    setText("#recommended-model", "GPT-5.6 Sol");
    setText("#decision-label", "Ask explicit approval");
    setText("#decision-reason", "Emergency capacity protects the remaining budget. One capsule-based Astra decision needs fresh approval.");
    setText("#turns-allowed", "0 until approved");
    setText("#context-action", "Build capsule");
    setText("#approval-gate", "Required");
    return;
  }

  if (remaining <= 30 && !premiumReasons.has(task) && !approved) {
    result.dataset.state = "blocked";
    setText("#recommended-model", "GPT-5.6 Sol");
    setText("#decision-label", "Conserve premium capacity");
    setText("#decision-reason", "At this capacity, Astra is reserved for architecture, security, release judgment, or work that remains unresolved after Sol.");
    setText("#turns-allowed", "0");
    setText("#context-action", "Use Sol first");
    setText("#approval-gate", "High-value reason");
    return;
  }

  result.dataset.state = "premium";
  setText("#recommended-model", "GPT-6 Astra");
  setText("#decision-label", "Allow one capsule");
  setText("#decision-reason", "The task is a high-leverage decision and the context is bounded. Keep the premium prompt below the Sol-parity ceiling.");
  setText("#turns-allowed", "1");
  setText("#context-action", "Scan + score capsule");
  setText("#approval-gate", approved ? "Approved" : "Policy satisfied");
}

budget.addEventListener("input", routeTask);
form.addEventListener("submit", (event) => {
  event.preventDefault();
  routeTask();
});
form.addEventListener("change", routeTask);

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
