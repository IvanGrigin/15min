(function () {
  var modules = [];
  var currentWorksheet = null;
  var minTaskCount = 1;
  var maxTaskCount = 20;

  var summary = document.getElementById("catalog-summary");
  var taskCount = document.getElementById("task-count");
  var selectorGrid = document.getElementById("selector-grid");
  var quickGenerateButton = document.getElementById("quick-generate-button");
  var generateButton = document.getElementById("generate-button");
  var regenerateButton = document.getElementById("regenerate-button");
  var printButton = document.getElementById("print-button");
  var printAnswersButton = document.getElementById("print-answers-button");
  var showAnswersButton = document.getElementById("show-answers-button");
  var toggleAnswersButton = document.getElementById("toggle-answers-button");
  var clearButton = document.getElementById("clear-button");
  var errorState = document.getElementById("error-state");
  var sheetDate = document.getElementById("sheet-date");
  var worksheetProblems = document.getElementById("worksheet-problems");
  var answerKey = document.getElementById("answer-key");
  var answersList = document.getElementById("answers-list");
  var printAnswersList = document.getElementById("print-answers-list");

  function todayRu() {
    var now = new Date();
    return String(now.getDate()).padStart(2, "0") + "." +
      String(now.getMonth() + 1).padStart(2, "0") + "." + now.getFullYear();
  }

  function showError(message) {
    errorState.textContent = message;
    errorState.hidden = !message;
  }

  function selectedIds() {
    return Array.from(document.querySelectorAll("[data-template-select]"))
      .map(function (select) { return select.value; })
      .filter(Boolean);
  }

  function currentCount() {
    var parsed = Number.parseInt(taskCount.value, 10);
    if (!Number.isFinite(parsed)) {
      parsed = 5;
    }
    return Math.max(minTaskCount, Math.min(maxTaskCount, parsed));
  }

  function normalizeCount() {
    taskCount.value = String(currentCount());
  }

  function canGenerate() {
    return selectedIds().length === currentCount();
  }

  function optionLabel(module, moduleIndex) {
    var suffix = module.answer_status === "unverified" ? " · без восстановленных ответов" : " · с ответами";
    var number = String(moduleIndex + 1).padStart(2, "0");
    return number + ". " + module.display_name + " · шаблонов: " + (module.template_count || 0) + suffix;
  }

  function selectorCard(index, selectedValue) {
    var article = document.createElement("article");
    article.className = "selector-card";
    article.innerHTML = "<div class=\"selector-card__header\"><span>" + index +
      "</span><div><h3>Задача " + index + "</h3><p>Модуль задач</p></div></div>";
    var label = document.createElement("label");
    label.htmlFor = "template-select-" + index;
    label.textContent = "Выберите модуль";
    var select = document.createElement("select");
    select.id = "template-select-" + index;
    select.setAttribute("data-template-select", String(index));
    var empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Ничего не выбрано";
    select.appendChild(empty);
    modules.forEach(function (module, moduleIndex) {
      var option = document.createElement("option");
      option.value = module.module_id;
      option.textContent = optionLabel(module, moduleIndex);
      select.appendChild(option);
    });
    select.value = selectedValue || "";
    select.addEventListener("change", refreshControls);
    article.appendChild(label);
    article.appendChild(select);
    selectorGrid.appendChild(article);
  }

  function rebuildSelectors() {
    var previous = selectedIds();
    selectorGrid.innerHTML = "";
    for (var index = 1; index <= currentCount(); index += 1) {
      selectorCard(index, previous[index - 1]);
    }
    refreshControls();
  }

  function refreshControls() {
    generateButton.disabled = !canGenerate();
    regenerateButton.disabled = !currentWorksheet;
    quickGenerateButton.disabled = modules.length === 0;
    if (modules.length === 0) {
      showError("Нет модулей, которые поддерживают безопасную генерацию.");
    } else if (!errorState.hidden && errorState.textContent.indexOf("Нет модулей") !== -1) {
      showError("");
    }
  }

  async function loadTemplates() {
    var response = await fetch("/api/templates");
    var payload = await response.json();
    if (!response.ok) {
      throw new Error("Не удалось загрузить каталог.");
    }
    modules = payload.modules || [];
    var stats = payload.stats || {};
    var limits = payload.limits || {};
    minTaskCount = limits.min_task_count || 1;
    maxTaskCount = limits.max_task_count || 20;
    taskCount.min = String(minTaskCount);
    taskCount.max = String(maxTaskCount);
    normalizeCount();
    summary.textContent = "Для быстрого варианта: " + (stats.verified_answer_templates || 0) +
      " шаблонов с ответами. В архиве: " + (stats.recovered_archive_templates || 0) +
      " заданий с восстановленными формулами и " + (stats.unverified_archive_templates || 0) +
      " подготовленных текстов без формул.";
    rebuildSelectors();
  }

  function renderWorksheet(worksheet) {
    currentWorksheet = worksheet;
    sheetDate.textContent = worksheet.date || todayRu();
    worksheetProblems.innerHTML = "";
    answersList.innerHTML = "";
    printAnswersList.innerHTML = "";
    worksheet.selected_templates.forEach(function (problem) {
      var problemItem = document.createElement("li");
      var text = document.createElement("p");
      text.textContent = problem.rendered_problem;
      var line = document.createElement("div");
      line.className = "answer-line";
      problemItem.appendChild(text);
      problemItem.appendChild(line);
      worksheetProblems.appendChild(problemItem);

      var answerText = String(problem.answer);
      var answerItem = document.createElement("li");
      answerItem.textContent = answerText;
      answersList.appendChild(answerItem);
      var printAnswerItem = document.createElement("li");
      printAnswerItem.textContent = answerText;
      printAnswersList.appendChild(printAnswerItem);
    });
    printButton.disabled = false;
    printAnswersButton.disabled = false;
    showAnswersButton.disabled = false;
    refreshControls();
  }

  async function requestWorksheet(mode) {
    normalizeCount();
    if (mode === "manual" && !canGenerate()) {
      showError("Выберите модуль для каждой задачи или используйте деревянный вариант.");
      return;
    }
    showError("");
    var body = { count: currentCount(), seed: Math.floor(Math.random() * 1000000000) };
    if (mode === "random") {
      body.mode = "random";
    } else {
      body.module_ids = selectedIds();
    }
    var response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    var payload = await response.json();
    if (!response.ok || !payload.ok) {
      showError(payload.error || "Не удалось подобрать корректные числа. Повторите попытку.");
      return;
    }
    renderWorksheet(payload.worksheet);
  }

  taskCount.addEventListener("change", function () {
    normalizeCount();
    rebuildSelectors();
  });
  clearButton.addEventListener("click", function () {
    selectorGrid.innerHTML = "";
    rebuildSelectors();
    currentWorksheet = null;
    answerKey.hidden = true;
    showAnswersButton.disabled = true;
    printButton.disabled = true;
    printAnswersButton.disabled = true;
  });
  quickGenerateButton.addEventListener("click", function () { requestWorksheet("random"); });
  generateButton.addEventListener("click", function () { requestWorksheet("manual"); });
  regenerateButton.addEventListener("click", function () {
    requestWorksheet(currentWorksheet && currentWorksheet.mode === "random_verified_modules" ? "random" : "manual");
  });
  showAnswersButton.addEventListener("click", function () { answerKey.hidden = false; });
  toggleAnswersButton.addEventListener("click", function () { answerKey.hidden = true; });
  printButton.addEventListener("click", function () {
    document.body.classList.remove("print-with-answers");
    window.print();
  });
  printAnswersButton.addEventListener("click", function () {
    document.body.classList.add("print-with-answers");
    window.print();
  });
  window.addEventListener("afterprint", function () { document.body.classList.remove("print-with-answers"); });

  sheetDate.textContent = todayRu();
  loadTemplates().catch(function () { showError("Не удалось загрузить каталог шаблонов."); });
})();
