(function () {
  "use strict";

  var csrf = document.querySelector('meta[name="template-studio-csrf"]').content;
  var currentDraft = null;
  var modules = [];
  var errorBox = document.getElementById("studio-error");
  var workbench = document.getElementById("studio-workbench");

  function showError(message) {
    errorBox.textContent = message || "";
    errorBox.hidden = !message;
  }

  async function request(url, method, payload) {
    var options = { method: method || "GET", headers: {} };
    if (method && method !== "GET") {
      options.headers["Content-Type"] = "application/json";
      options.headers["X-Template-Studio-CSRF"] = csrf;
      options.body = JSON.stringify(payload || {});
    }
    var response = await fetch(url, options);
    var data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Запрос Template Studio не выполнен.");
    }
    return data;
  }

  function jsonValue(id, fallback) {
    var source = document.getElementById(id).value.trim();
    if (!source) { return fallback; }
    try { return JSON.parse(source); } catch (error) { throw new Error("Некорректный JSON в поле " + id + "."); }
  }

  function fillModuleSelect(select, selected, allowEmpty) {
    select.innerHTML = "";
    if (allowEmpty) {
      var empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "Без модуля (только draft)";
      select.appendChild(empty);
    }
    modules.forEach(function (module) {
      var option = document.createElement("option");
      option.value = module.module_id;
      option.textContent = module.display_name;
      select.appendChild(option);
    });
    select.value = selected || "";
  }

  function parameterRow(name, rule) {
    var row = document.createElement("div");
    row.className = "studio-parameter-row";
    row.innerHTML = "";
    var nameInput = document.createElement("input");
    nameInput.placeholder = "name";
    nameInput.value = name || "";
    nameInput.setAttribute("data-parameter-name", "");
    var type = document.createElement("select");
    type.setAttribute("data-parameter-type", "");
    ["integer", "positive_integer", "nonnegative_integer", "decimal", "fraction", "boolean", "string", "word", "letter", "name", "choice", "integer_list", "word_list"].forEach(function (item) {
      var option = document.createElement("option"); option.value = item; option.textContent = item; type.appendChild(option);
    });
    type.value = (rule && rule.type) || "integer";
    var minimum = document.createElement("input");
    minimum.type = "number"; minimum.placeholder = "minimum"; minimum.value = rule && rule.minimum !== undefined ? String(rule.minimum) : ""; minimum.setAttribute("data-parameter-minimum", "");
    var maximum = document.createElement("input");
    maximum.type = "number"; maximum.placeholder = "maximum"; maximum.value = rule && rule.maximum !== undefined ? String(rule.maximum) : ""; maximum.setAttribute("data-parameter-maximum", "");
    var values = document.createElement("input");
    values.placeholder = "allowed values JSON"; values.value = rule && rule.allowed_values ? JSON.stringify(rule.allowed_values) : ""; values.setAttribute("data-parameter-values", "");
    var remove = document.createElement("button"); remove.type = "button"; remove.className = "button-secondary"; remove.textContent = "×"; remove.addEventListener("click", function () { row.remove(); });
    row.append(nameInput, type, minimum, maximum, values, remove);
    return row;
  }

  function renderParameters(schema) {
    var root = document.getElementById("studio-parameter-rows");
    root.innerHTML = "";
    Object.keys(schema || {}).forEach(function (name) { root.appendChild(parameterRow(name, schema[name])); });
  }

  function readParameters() {
    var result = {};
    document.querySelectorAll(".studio-parameter-row").forEach(function (row) {
      var name = row.querySelector("[data-parameter-name]").value.trim();
      if (!name) { return; }
      var rule = { type: row.querySelector("[data-parameter-type]").value };
      var minimum = row.querySelector("[data-parameter-minimum]").value;
      var maximum = row.querySelector("[data-parameter-maximum]").value;
      var values = row.querySelector("[data-parameter-values]").value.trim();
      if (minimum !== "") { rule.minimum = Number(minimum); }
      if (maximum !== "") { rule.maximum = Number(maximum); }
      if (values) {
        try { rule.allowed_values = JSON.parse(values); } catch (error) { throw new Error("allowed values параметра " + name + " — не JSON."); }
      }
      result[name] = rule;
    });
    return result;
  }

  function collectChanges() {
    return {
      template_id: document.getElementById("studio-template-id").value.trim(),
      module_id: document.getElementById("studio-edit-module").value || null,
      answer_type: document.getElementById("studio-edit-answer-type").value,
      candidate_template_text: document.getElementById("studio-template-text").value,
      parameter_schema: readParameters(),
      derived_values: jsonValue("studio-derived-values", {}),
      solver_strategy: document.getElementById("studio-strategy").value,
      answer_expression: document.getElementById("studio-answer-expression").value.trim(),
      constraints: jsonValue("studio-constraints", {}),
      answer_rendering: jsonValue("studio-answer-rendering", {}),
      grammar_metadata: jsonValue("studio-grammar", {}),
      source_metadata: {
        problem_number: document.getElementById("studio-edit-source-number").value.trim() || null,
        filename: document.getElementById("studio-edit-source-file").value.trim() || null
      },
      notes: document.getElementById("studio-notes").value
    };
  }

  function displayValidation(report) {
    var root = document.getElementById("studio-validation-results");
    root.innerHTML = "";
    if (!report) { root.textContent = "Проверка ещё не запускалась."; return; }
    var heading = document.createElement("p"); heading.className = report.passed ? "studio-pass" : "studio-fail"; heading.textContent = report.passed ? "Validation passed" : "Validation failed"; root.appendChild(heading);
    (report.checks || []).forEach(function (check) {
      var item = document.createElement("article"); item.className = "studio-check " + (check.passed ? "studio-pass" : "studio-fail");
      var title = document.createElement("strong"); title.textContent = (check.passed ? "✓ " : "× ") + check.label;
      var details = document.createElement("p"); details.textContent = check.message;
      item.append(title, details); root.appendChild(item);
    });
  }

  function displayPreviews(previews) {
    var root = document.getElementById("studio-preview-results"); root.innerHTML = "";
    (previews || []).forEach(function (preview) {
      var item = document.createElement("article"); item.className = "studio-preview";
      var title = document.createElement("strong"); title.textContent = "seed " + preview.seed + (preview.validation.passed ? " · OK" : " · ошибка");
      var problem = document.createElement("p"); problem.textContent = preview.rendered_problem || preview.validation.message;
      var details = document.createElement("pre"); details.textContent = "parameters: " + JSON.stringify(preview.parameters || {}, null, 2) + "\nderived: " + JSON.stringify(preview.derived_values || {}, null, 2) + "\nanswer: " + JSON.stringify(preview.answer);
      item.append(title, problem, details); root.appendChild(item);
    });
  }

  function showDraft(draft) {
    currentDraft = draft;
    workbench.hidden = false;
    document.getElementById("studio-draft-id").textContent = draft.draft_id;
    document.getElementById("studio-status").textContent = "Статус: " + draft.status + " · обновлён " + draft.updated_at;
    document.getElementById("studio-source-view").textContent = draft.original_text;
    document.getElementById("studio-notes").value = draft.notes || "";
    document.getElementById("studio-template-id").value = draft.template_id || "";
    fillModuleSelect(document.getElementById("studio-edit-module"), draft.module_id, true);
    document.getElementById("studio-edit-answer-type").value = draft.answer_type || "integer";
    document.getElementById("studio-template-text").value = draft.candidate_template_text || "";
    renderParameters(draft.parameter_schema || {});
    document.getElementById("studio-derived-values").value = JSON.stringify(draft.derived_values || {}, null, 2);
    document.getElementById("studio-strategy").value = draft.solver_strategy || "manual";
    document.getElementById("studio-answer-expression").value = draft.answer_expression || "";
    document.getElementById("studio-constraints").value = JSON.stringify(draft.constraints || {}, null, 2);
    document.getElementById("studio-answer-rendering").value = JSON.stringify(draft.answer_rendering || {}, null, 2);
    document.getElementById("studio-grammar").value = JSON.stringify(draft.grammar_metadata || {}, null, 2);
    document.getElementById("studio-edit-source-number").value = (draft.source_metadata || {}).problem_number || "";
    document.getElementById("studio-edit-source-file").value = (draft.source_metadata || {}).filename || "";
    document.getElementById("studio-raw-json").value = JSON.stringify(draft, null, 2);
    displayValidation(draft.validation_report);
    var history = document.getElementById("studio-history"); history.innerHTML = "";
    (draft.revision_history || []).slice().reverse().forEach(function (event) { var li = document.createElement("li"); li.textContent = event.at + " · " + event.action; history.appendChild(li); });
    selectSection("template");
  }

  function selectSection(name) {
    document.querySelectorAll("[data-studio-panel]").forEach(function (panel) { panel.hidden = panel.getAttribute("data-studio-panel") !== name; });
    document.querySelectorAll("[data-studio-section]").forEach(function (button) { button.classList.toggle("is-active", button.getAttribute("data-studio-section") === name); });
  }

  async function refreshDrafts() {
    var data = await request("/api/admin/template-studio/drafts");
    var root = document.getElementById("studio-drafts"); root.innerHTML = "";
    (data.drafts || []).forEach(function (draft) {
      var button = document.createElement("button"); button.type = "button"; button.className = "studio-draft-link"; button.textContent = draft.template_id + " · " + draft.status; button.addEventListener("click", function () { showDraft(draft); }); root.appendChild(button);
    });
    if (!(data.drafts || []).length) { root.textContent = "Черновиков пока нет."; }
  }

  async function save() {
    if (!currentDraft) { return; }
    var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id), "PATCH", collectChanges());
    showDraft(data.draft); await refreshDrafts(); return data.draft;
  }

  document.getElementById("studio-source-form").addEventListener("submit", async function (event) {
    event.preventDefault(); showError("");
    try {
      var data = await request("/api/admin/template-studio/analyze", "POST", {
        original_text: document.getElementById("studio-original-text").value,
        module_id: document.getElementById("studio-module").value || null,
        source_problem_number: document.getElementById("studio-source-number").value,
        source_filename: document.getElementById("studio-source-file").value,
        language: document.getElementById("studio-language").value,
        answer_type: document.getElementById("studio-answer-type").value
      });
      showDraft(data.draft); await refreshDrafts();
    } catch (error) { showError(error.message); }
  });
  document.getElementById("studio-refresh-drafts").addEventListener("click", function () { refreshDrafts().catch(function (error) { showError(error.message); }); });
  document.getElementById("studio-add-parameter").addEventListener("click", function () { document.getElementById("studio-parameter-rows").appendChild(parameterRow("", { type: "integer", minimum: 1, maximum: 10 })); });
  document.getElementById("studio-save").addEventListener("click", function () { save().catch(function (error) { showError(error.message); }); });
  document.getElementById("studio-preview").addEventListener("click", async function () { try { await save(); var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/preview", "POST", { count: Number(document.getElementById("studio-preview-count").value), seed: Number(document.getElementById("studio-preview-seed").value) }); displayPreviews(data.previews); selectSection("preview"); } catch (error) { showError(error.message); } });
  document.getElementById("studio-validate").addEventListener("click", async function () { try { await save(); var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/validate", "POST", {}); showDraft(data.draft); displayValidation(data.report); selectSection("validation"); await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-activate").addEventListener("click", async function () { try { var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/activate", "POST", {}); showDraft(data.draft); await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-archive").addEventListener("click", async function () { try { var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/archive", "POST", {}); showDraft(data.draft); await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-restore").addEventListener("click", async function () { try { var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/restore", "POST", {}); showDraft(data.draft); await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-reject").addEventListener("click", async function () { var reason = window.prompt("Причина отклонения:"); if (reason === null) { return; } try { var data = await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id) + "/reject", "POST", { reason: reason }); showDraft(data.draft); await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-delete").addEventListener("click", async function () { if (!window.confirm("Навсегда удалить только этот draft? Активный шаблон удалить нельзя.")) { return; } try { await request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id), "DELETE", { confirmed: true }); currentDraft = null; workbench.hidden = true; await refreshDrafts(); } catch (error) { showError(error.message); } });
  document.getElementById("studio-apply-raw").addEventListener("click", function () { try { var raw = jsonValue("studio-raw-json", {}); var editable = ["template_id", "module_id", "candidate_template_text", "answer_type", "parameter_schema", "derived_values", "constraints", "solver_strategy", "answer_expression", "answer_rendering", "grammar_metadata", "source_metadata", "notes", "language"]; var changes = {}; editable.forEach(function (key) { if (Object.prototype.hasOwnProperty.call(raw, key)) { changes[key] = raw[key]; } }); request("/api/admin/template-studio/drafts/" + encodeURIComponent(currentDraft.draft_id), "PATCH", changes).then(function (data) { showDraft(data.draft); refreshDrafts(); }).catch(function (error) { showError(error.message); }); } catch (error) { showError(error.message); } });
  document.querySelectorAll("[data-studio-section]").forEach(function (button) { button.addEventListener("click", function () { selectSection(button.getAttribute("data-studio-section")); }); });

  Promise.all([request("/api/admin/template-studio/modules"), refreshDrafts()]).then(function (results) { modules = results[0].modules || []; fillModuleSelect(document.getElementById("studio-module"), "", true); }).catch(function (error) { showError(error.message); });
})();
