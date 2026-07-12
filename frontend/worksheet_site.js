(function () {
  var button = document.getElementById("generate-button");
  var loadingState = document.getElementById("loading-state");
  var errorState = document.getElementById("error-state");
  var resultState = document.getElementById("result-state");
  var downloadLink = document.getElementById("download-link");
  var answersPath = document.getElementById("answers-path");
  var problemsPath = document.getElementById("problems-path");

  function collectItems() {
    return Array.from(document.querySelectorAll("[data-difficulty-index]")).map(function (select) {
      var index = select.getAttribute("data-difficulty-index");
      var module = document.querySelector('[data-module-index="' + index + '"]');
      return { module: module.value, difficulty: Number(select.value) };
    });
  }

  function setLoading(isLoading) {
    loadingState.hidden = !isLoading;
    button.disabled = isLoading;
  }

  button.addEventListener("click", async function () {
    errorState.hidden = true;
    resultState.hidden = true;
    errorState.textContent = "";
    setLoading(true);

    try {
      var response = await fetch("/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ items: collectItems() })
      });

      var payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "Не удалось сгенерировать лист.");
      }

      downloadLink.href = payload.download_url;
      answersPath.textContent = "Ответы: " + payload.answers_path;
      problemsPath.textContent = "Задачи: " + payload.problems_path;
      resultState.hidden = false;
    } catch (error) {
      errorState.textContent = error.message;
      errorState.hidden = false;
    } finally {
      setLoading(false);
    }
  });
})();
