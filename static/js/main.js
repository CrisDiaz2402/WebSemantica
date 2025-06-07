// Variables globales
let isProcessing = false
let fileExists = false

// Elementos del DOM
const processDataBtn = document.getElementById("process-data")
const generateSampleBtn = document.getElementById("generate-sample")
const searchButton = document.getElementById("search-button")
const searchInput = document.getElementById("search-input")
const searchResults = document.getElementById("search-results")
const loadingOverlay = document.getElementById("loading-overlay")
const filterButtons = document.querySelectorAll(".filter-btn")
const fileStatus = document.getElementById("file-status")
const fileInfoText = document.getElementById("file-info-text")

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  // Verificar archivo al cargar
  checkDataFile()

  // Cargar estadísticas iniciales
  loadStats()

  // Process data button
  if (processDataBtn) {
    processDataBtn.addEventListener("click", handleDataProcessing)
  }

  // // Generate sample data
  // if (generateSampleBtn) {
  //   generateSampleBtn.addEventListener("click", generateSampleData)
  // }

  // Search functionality
  if (searchButton) {
    searchButton.addEventListener("click", performSearch)
  }

  if (searchInput) {
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        performSearch()
      }
    })
  }

  // Filter buttons
  filterButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const sentiment = this.dataset.sentiment
      searchBySentiment(sentiment)
    })
  })
})

// Verificar si existe el archivo test.csv
async function checkDataFile() {
  try {
    const response = await fetch("/api/check-data-file")
    const result = await response.json()

    if (result.exists) {
      fileExists = true
      fileStatus.className = "file-status success"
      fileInfoText.textContent = `Archivo encontrado - ${result.rows} filas, columnas: ${result.columns.join(", ")}`
      processDataBtn.disabled = false
    } else {
      fileExists = false
      fileStatus.className = "file-status error"
      fileInfoText.textContent = "Archivo no encontrado. Genera datos de ejemplo para comenzar."
      processDataBtn.disabled = true
    }
  } catch (error) {
    console.error("Error verificando archivo:", error)
    fileStatus.className = "file-status error"
    fileInfoText.textContent = "Error verificando archivo"
    processDataBtn.disabled = true
  }
}

// Procesar datos del archivo fijo
async function handleDataProcessing() {
  if (isProcessing || !fileExists) return

  const textColumn = document.getElementById("text-column").value.trim()

  if (!textColumn) {
    showNotification("Por favor especifica el nombre de la columna de texto", "warning")
    return
  }

  isProcessing = true
  showLoading(true)

  try {
    const response = await fetch(`/process-fixed-data?text_column=${encodeURIComponent(textColumn)}`)
    const result = await response.json()

    if (response.ok) {
      showNotification(result.message, "success")
      loadStats()
    } else {
      showNotification(result.error || "Error procesando datos", "error")
    }
  } catch (error) {
    console.error("Error:", error)
    showNotification("Error de conexión", "error")
  } finally {
    isProcessing = false
    showLoading(false)
  }
}

async function performSearch() {
  const query = searchInput.value.trim()

  if (!query) {
    showNotification("Por favor ingresa una consulta", "warning")
    return
  }

  showLoading(true)

  try {
    const formData = new FormData()
    formData.append("query", query)
    formData.append("top_k", "5")

    const response = await fetch("/search", {
      method: "POST",
      body: formData,
    })

    const result = await response.json()

    if (response.ok) {
      displaySearchResults(result.results, query)
    } else {
      showNotification(result.error || "Error en búsqueda", "error")
    }
  } catch (error) {
    console.error("Error:", error)
    showNotification("Error de conexión", "error")
  } finally {
    showLoading(false)
  }
}

async function searchBySentiment(sentiment) {
  showLoading(true)

  try {
    const response = await fetch(`/search/sentiment/${sentiment}?top_k=5`)
    const result = await response.json()

    if (response.ok) {
      displaySearchResults(result.results, `Sentimiento: ${sentiment}`)
    } else {
      showNotification(result.error || "Error en búsqueda", "error")
    }
  } catch (error) {
    console.error("Error:", error)
    showNotification("Error de conexión", "error")
  } finally {
    showLoading(false)
  }
}

function displaySearchResults(results, query) {
  if (!searchResults) return

  if (results.length === 0) {
    searchResults.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No se encontraron resultados para "${query}"</p>
            </div>
        `
    return
  }

  let html = `
        <div class="results-header">
            <h3><i class="fas fa-search"></i> Resultados para: "${query}"</h3>
            <p class="results-count">${results.length} resultados encontrados</p>
        </div>
    `

  results.forEach((result, index) => {
    const sentimentIcon = getSentimentIcon(result.sentiment)
    const sentimentClass = getSentimentClass(result.sentiment)

    html += `
            <div class="result-item">
                <div class="result-header">
                    <h4><i class="fas fa-file-alt"></i> ${result.id}</h4>
                    <div class="result-meta">
                        <span class="result-score">Score: ${result.score}</span>
                        <span class="sentiment-badge ${sentimentClass}">
                            ${sentimentIcon} ${result.sentiment}
                        </span>
                    </div>
                </div>
                <p class="result-text">${result.text}</p>
                ${
                  result.products && result.products.length > 0
                    ? `<div class="result-tags">
                        <strong>Productos:</strong> ${result.products.join(", ")}
                    </div>`
                    : ""
                }
                ${
                  result.brands && result.brands.length > 0
                    ? `<div class="result-tags">
                        <strong>Marcas:</strong> ${result.brands.join(", ")}
                    </div>`
                    : ""
                }
            </div>
        `
  })

  searchResults.innerHTML = html
}

async function loadStats() {
  try {
    const response = await fetch("/api/report")
    const report = await response.json()

    if (response.ok && report.resumen_general) {
      updateStatsDisplay(report.resumen_general)
    }
  } catch (error) {
    console.error("Error loading stats:", error)
  }
}

function updateStatsDisplay(stats) {
  const elements = {
    "total-reviews": stats.total_reseñas || 0,
    "total-products": stats.productos_únicos || 0,
    "total-brands": stats.marcas_únicas || 0,
    "total-events": stats.eventos_totales || 0,
  }

  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id)
    if (element) {
      animateNumber(element, value)
    }
  })
}

function animateNumber(element, targetValue) {
  const startValue = Number.parseInt(element.textContent) || 0
  const duration = 1000
  const startTime = performance.now()

  function updateNumber(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)

    const currentValue = Math.floor(startValue + (targetValue - startValue) * progress)
    element.textContent = currentValue

    if (progress < 1) {
      requestAnimationFrame(updateNumber)
    }
  }

  requestAnimationFrame(updateNumber)
}

function getSentimentIcon(sentiment) {
  switch (sentiment) {
    case "positivo":
      return '<i class="fas fa-smile"></i>'
    case "negativo":
      return '<i class="fas fa-frown"></i>'
    case "neutro":
      return '<i class="fas fa-meh"></i>'
    default:
      return '<i class="fas fa-question"></i>'
  }
}

function getSentimentClass(sentiment) {
  switch (sentiment) {
    case "positivo":
      return "sentiment-positive"
    case "negativo":
      return "sentiment-negative"
    case "neutro":
      return "sentiment-neutral"
    default:
      return "sentiment-unknown"
  }
}

function showLoading(show) {
  if (loadingOverlay) {
    loadingOverlay.style.display = show ? "flex" : "none"
  }
}

function showNotification(message, type = "info") {
  // Crear elemento de notificación
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `

  // Añadir estilos si no existen
  if (!document.querySelector("#notification-styles")) {
    const styles = document.createElement("style")
    styles.id = "notification-styles"
    styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                animation: slideIn 0.3s ease;
            }
            
            .notification-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .notification-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .notification-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .notification-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 1rem;
            }
            
            .notification-close {
                background: none;
                border: none;
                cursor: pointer;
                margin-left: auto;
                opacity: 0.7;
            }
            
            .notification-close:hover { opacity: 1; }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `
    document.head.appendChild(styles)
  }

  // Añadir al DOM
  document.body.appendChild(notification)

  // Evento de cierre
  notification.querySelector(".notification-close").addEventListener("click", () => {
    notification.remove()
  })

  // Auto-remove después de 5 segundos
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove()
    }
  }, 5000)
}

function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "check-circle"
    case "error":
      return "exclamation-circle"
    case "warning":
      return "exclamation-triangle"
    case "info":
      return "info-circle"
    default:
      return "info-circle"
  }
}

// Añadir estilos CSS adicionales para los resultados
const additionalStyles = `
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .result-meta {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .sentiment-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .sentiment-positive { background: #d4edda; color: #155724; }
    .sentiment-negative { background: #f8d7da; color: #721c24; }
    .sentiment-neutral { background: #e2e3e5; color: #383d41; }
    .sentiment-unknown { background: #fff3cd; color: #856404; }
    
    .result-tags {
        margin-top: 0.5rem;
        font-size: 0.9rem;
        color: #6c757d;
    }
    
    .results-header {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e1e5e9;
    }
    
    .results-count {
        color: #6c757d;
        font-style: italic;
        margin-top: 0.5rem;
    }
`

// Añadir estilos adicionales
const styleSheet = document.createElement("style")
styleSheet.textContent = additionalStyles
document.head.appendChild(styleSheet)