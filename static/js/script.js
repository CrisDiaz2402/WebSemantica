document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  const searchButton = document.getElementById("search-button");
  const resultsContainer = document.getElementById("results-container");

  searchButton.addEventListener("click", performSearch);
  searchInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      performSearch();
    }
  });

  function performSearch() {
    const query = searchInput.value.trim();

    if (!query) {
      resultsContainer.innerHTML =
        '<p class="no-results">Por favor ingrese una consulta de búsqueda.</p>';
      return;
    }

    // Mostrar carga
    resultsContainer.innerHTML = '<p class="loading">Buscando...</p>';

    // Enviar solicitud al servidor
    fetch("/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `query=${encodeURIComponent(query)}`,
    })
      .then((response) => response.json())
      .then((data) => displayResults(data.results, query))
      .catch((error) => {
        console.error("Error:", error);
        resultsContainer.innerHTML =
          '<p class="error">Ocurrió un error al realizar la búsqueda.</p>';
      });
  }

  function displayResults(results, query) {
    if (results.length === 0) {
      resultsContainer.innerHTML = `
                <p class="no-results">No se encontraron documentos que coincidan con "${query}".</p>
            `;
      return;
    }

    let html = `
            <div class="results-header">
                <h2>Resultados para: "${query}"</h2>
                <p class="results-count">${results.length} documentos encontrados</p>
            </div>
        `;

    results.forEach((result) => {
      html += `
                <div class="result-card">
                    <div class="result-header">
                        <h3>${result.filename} [${result.id}]</h3>
                        <span class="score">Relevancia: ${result.score}</span>
                    </div>
                    <div class="result-content">
                        <p>${highlightQueryTerms(result.content, query)}</p>
                    </div>
                </div>
            `;
    });

    resultsContainer.innerHTML = html;
  }

  function highlightQueryTerms(text, query) {
    const terms = query.toLowerCase().split(" ");
    let highlighted = text;

    terms.forEach((term) => {
      if (term.length > 2) {
        // Evitar resaltar palabras muy cortas
        const regex = new RegExp(`(${term})`, "gi");
        highlighted = highlighted.replace(
          regex,
          '<span class="highlight">$1</span>'
        );
      }
    });

    return highlighted;
  }
});
