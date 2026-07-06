(function () {
  var config = window.PROBLEMGEN_CONFIG || { domains: {} };
  var formState = window.PROBLEMGEN_FORM || {};

  var domainSelect = document.getElementById("domain");
  var templateSelect = document.getElementById("template_name");
  var themeSelect = document.getElementById("story_theme");

  function refillSelect(select, options, selectedValue, withAnyLabel) {
    select.innerHTML = "";
    var anyOption = document.createElement("option");
    anyOption.value = "any";
    anyOption.textContent = withAnyLabel;
    select.appendChild(anyOption);

    options.forEach(function (option) {
      var item = document.createElement("option");
      item.value = option.value;
      item.textContent = option.label;
      if (option.description) {
        item.title = option.description;
      }
      select.appendChild(item);
    });

    select.value = selectedValue || "any";
    if (!select.value) {
      select.value = "any";
    }
  }

  function syncDomainOptions() {
    var domainCode = domainSelect.value;
    var domain = config.domains[domainCode];
    if (!domain) {
      return;
    }

    refillSelect(
      templateSelect,
      domain.templates.map(function (template) {
        return {
          value: template.code,
          label: template.label,
          description: template.description
        };
      }),
      formState.template_name,
      "Любой шаблон"
    );

    refillSelect(
      themeSelect,
      Object.keys(domain.themes).map(function (code) {
        return { value: code, label: domain.themes[code] };
      }),
      formState.story_theme,
      "Любая тема"
    );
  }

  domainSelect.addEventListener("change", function () {
    formState.template_name = "any";
    formState.story_theme = "any";
    syncDomainOptions();
  });

  syncDomainOptions();
})();
