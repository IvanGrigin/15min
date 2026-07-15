(function () {
  var modules = [];
  var currentWorksheet = null;
  var printWithAnswers = false;

  var summary = document.getElementById("catalog-summary");
  var generateButton = document.getElementById("generate-button");
  var regenerateButton = document.getElementById("regenerate-button");
  var printButton = document.getElementById("print-button");
  var printAnswersButton = document.getElementById("print-answers-button");
  var showAnswersButton = document.getElementById("show-answers-button");
  var toggleAnswersButton = document.getElementById("toggle-answers-button");
  var clearButton = document.getElementById("clear-button");
  var allowRepeats = document.getElementById("allow-repeats");
  var errorState = document.getElementById("error-state");
  var sheetDate = document.getElementById("sheet-date");
  var worksheetProblems = document.getElementById("worksheet-problems");
  var answerKey = document.getElementById("answer-key");
  var answersList = document.getElementById("answers-list");

  function todayRu() {
    var now = new Date();
    return String(now.getDate()).padStart(2, "0") + "." +
      String(now.getMonth() + 1).padStart(2, "0") + "." +
      now.getFullYear();
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

  function canGenerate() {
    var ids = selectedIds();
    if (ids.length !== 5) {
      return false;
    }
    return true;
  }

  function optionLabel(module) {
    return module.display_name + " · шаблонов: " + (module.template_count || 0);
  }

  function matchesSearch(module, query) {
    if (!query) {
      return true;
    }
    var haystack = [
      module.display_name,
      module.title,
      module.module_id
    ].join(" ").toLowerCase();
    return haystack.indexOf(query.toLowerCase()) !== -1;
  }

  function fillSelect(select, query, currentValue) {
    select.innerHTML = "";
    var empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Ничего не выбрано";
    select.appendChild(empty);

    modules.filter(function (module) {
      return matchesSearch(module, query);
    }).forEach(function (module) {
      var option = document.createElement("option");
      option.value = module.module_id;
      option.textContent = optionLabel(module);
      select.appendChild(option);
    });
    if (currentValue && Array.from(select.options).some(function (option) { return option.value === currentValue; })) {
      select.value = currentValue;
    }
  }

  function refreshSelectors() {
    Array.from(document.querySelectorAll("[data-template-select]")).forEach(function (select) {
      var index = select.getAttribute("data-template-select");
      var search = document.querySelector('[data-template-search="' + index + '"]');
      var currentValue = select.value;
      fillSelect(select, search.value, currentValue);
      var status = document.querySelector('[data-selector-status="' + index + '"]');
      status.textContent = select.value ? "Модуль выбран." : "Модуль не выбран.";
    });
    if (modules.length === 0) {
      showError("Нет модулей, которые поддерживают безопасную генерацию целых ответов.");
    } else {
      showError("");
    }
    generateButton.disabled = !canGenerate();
    regenerateButton.disabled = !currentWorksheet || !canGenerate();
  }

  async function loadTemplates() {
    var response = await fetch("/api/templates");
    var payload = await response.json();
    modules = payload.modules || [];
    var stats = payload.stats || {};
    summary.textContent = "Доступно модулей: " + (stats.total_modules || modules.length || 0) +
      ". Шаблонов внутри модулей: " + (stats.total_templates || 0) +
      ". Покрыто исходных задач: " + (stats.covered_source_problem_numbers || 0) + ".";
    Array.from(document.querySelectorAll("[data-template-select]")).forEach(function (select) {
      fillSelect(select, "", "");
    });
    refreshSelectors();
  }

  function renderWorksheet(worksheet) {
    currentWorksheet = worksheet;
    sheetDate.textContent = worksheet.date || todayRu();
    worksheetProblems.innerHTML = "";
    answersList.innerHTML = "";
    worksheet.selected_templates.forEach(function (problem) {
      var problemItem = document.createElement("li");
      problemItem.innerHTML = "";
      var text = document.createElement("p");
      text.textContent = problem.rendered_problem;
      var line = document.createElement("div");
      line.className = "answer-line";
      problemItem.appendChild(text);
      problemItem.appendChild(line);
      worksheetProblems.appendChild(problemItem);

      var answerItem = document.createElement("li");
      answerItem.textContent = String(problem.answer);
      answersList.appendChild(answerItem);
    });
    printButton.disabled = false;
    printAnswersButton.disabled = false;
    showAnswersButton.disabled = false;
  }

  async function generateWorksheet() {
    if (!canGenerate()) {
      showError("Выберите пять модулей.");
      return;
    }
    showError("");
    var response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ module_ids: selectedIds(), seed: Math.floor(Math.random() * 1000000000) })
    });
    var payload = await response.json();
    if (!response.ok || !payload.ok) {
      showError(payload.error || "Не удалось подобрать корректные числа. Повторите попытку или выберите другой модуль.");
      return;
    }
    renderWorksheet(payload.worksheet);
  }

  Array.from(document.querySelectorAll("[data-template-search]")).forEach(function (input) {
    input.addEventListener("input", function () {
      var index = input.getAttribute("data-template-search");
      var select = document.querySelector('[data-template-select="' + index + '"]');
      fillSelect(select, input.value, select.value);
      refreshSelectors();
    });
  });

  Array.from(document.querySelectorAll("[data-template-select]")).forEach(function (select) {
    select.addEventListener("change", refreshSelectors);
  });

  allowRepeats.addEventListener("change", refreshSelectors);
  clearButton.addEventListener("click", function () {
    Array.from(document.querySelectorAll("[data-template-select]")).forEach(function (select) {
      select.value = "";
    });
    currentWorksheet = null;
    answerKey.hidden = true;
    showAnswersButton.disabled = true;
    printButton.disabled = true;
    printAnswersButton.disabled = true;
    refreshSelectors();
  });
  generateButton.addEventListener("click", generateWorksheet);
  regenerateButton.addEventListener("click", generateWorksheet);
  showAnswersButton.addEventListener("click", function () {
    answerKey.hidden = false;
  });
  toggleAnswersButton.addEventListener("click", function () {
    answerKey.hidden = true;
  });
  printButton.addEventListener("click", function () {
    printWithAnswers = false;
    document.body.classList.remove("print-with-answers");
    window.print();
  });
  printAnswersButton.addEventListener("click", function () {
    printWithAnswers = true;
    document.body.classList.add("print-with-answers");
    window.print();
  });
  window.addEventListener("afterprint", function () {
    if (!printWithAnswers) {
      document.body.classList.remove("print-with-answers");
    }
  });

  sheetDate.textContent = todayRu();
  loadTemplates().catch(function () {
    showError("Не удалось загрузить каталог шаблонов.");
  });
})();
