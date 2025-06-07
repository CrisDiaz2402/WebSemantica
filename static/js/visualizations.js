// Variables globales para visualizaciones
let chartsData = null
let chartsGenerated = 0
const currentTheme = {
  positive: "#28a745",
  negative: "#dc3545",
  neutral: "#6c757d",
}

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
  initializeVisualizationControls()
  loadVisualizationData()
  updateStats()
})

// Inicializar controles
function initializeVisualizationControls() {
  const generateBtn = document.getElementById("generate-charts")
  const refreshBtn = document.getElementById("refresh-data")

  if (generateBtn) {
    generateBtn.addEventListener("click", generateAllCharts)
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", refreshData)
  }
}

// Cargar datos para visualización
async function loadVisualizationData() {
  try {
    showLoading(true)
    console.log("Iniciando carga de datos...")

    const response = await fetch("/api/report")

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Error de respuesta del servidor" }))
      throw new Error(errorData.error || `Error del servidor: ${response.status}`)
    }

    const data = await response.json()
    console.log("Respuesta del servidor:", data)

    if (!data || Object.keys(data).length === 0) {
      throw new Error("No se recibieron datos del servidor")
    }

    if (data.error) {
      throw new Error(data.error)
    }

    chartsData = data
    console.log("Datos cargados exitosamente:", chartsData)

    // Verificar si hay datos de sentimientos
    if (!chartsData.distribución_sentimientos || Object.keys(chartsData.distribución_sentimientos).length === 0) {
      console.warn("No hay datos de sentimientos disponibles")
    }

    // Verificar si hay datos de productos
    if (!chartsData.productos_más_mencionados || Object.keys(chartsData.productos_más_mencionados).length === 0) {
      console.warn("No hay datos de productos disponibles")
    }

    showNotification("Datos cargados correctamente", "success")
    return true
  } catch (error) {
    console.error("Error cargando datos:", error)
    showNotification("Error al cargar datos: " + error.message, "error")
    return false
  } finally {
    showLoading(false)
  }
}

// Función para refrescar datos
async function refreshData() {
  chartsData = null
  chartsGenerated = 0

  // Limpiar gráficos existentes
  const chartContainers = ["sentiment-chart", "products-chart", "brands-chart", "events-chart"]
  chartContainers.forEach((containerId) => {
    const container = document.getElementById(containerId)
    if (container) {
      container.innerHTML = `
        <div class="chart-loading">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Cargando datos...</p>
        </div>
      `
    }
  })

  await loadVisualizationData()
}

// Generar todos los gráficos
async function generateAllCharts() {
  if (!chartsData) {
    const dataLoaded = await loadVisualizationData()
    if (!dataLoaded) {
      showNotification("No se pudieron cargar los datos. Verifica que hay reseñas procesadas.", "warning")
      return
    }
  }

  showLoading(true)
  chartsGenerated = 0

  try {
    console.log("Iniciando generación de gráficos...")

    const chartPromises = [
      generateSentimentChart(),
      generateProductsChart(),
      generateBrandsChart(),
      generateEventsChart(),
    ]

    const results = await Promise.allSettled(chartPromises)

    // Contar éxitos y fallos
    let successCount = 0
    let errorCount = 0

    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        successCount++
        chartsGenerated++
      } else {
        errorCount++
        console.error(`Error en gráfico ${index}:`, result.reason)
      }
    })

    if (successCount > 0) {
      showNotification(`${successCount} visualizaciones generadas exitosamente`, "success")
    }

    if (errorCount > 0) {
      showNotification(`${errorCount} visualizaciones fallaron`, "warning")
    }

    updateStats()
  } catch (error) {
    console.error("Error generando gráficos:", error)
    showNotification("Error generando visualizaciones: " + error.message, "error")
  } finally {
    showLoading(false)
  }
}

// Gráfico de sentimientos (siempre dona)
async function generateSentimentChart() {
  const containerId = "sentiment-chart"
  const container = document.getElementById(containerId)

  if (!container) {
    throw new Error(`Contenedor ${containerId} no encontrado`)
  }

  try {
    console.log("Generando gráfico de sentimientos...")

    const sentiments = chartsData.distribución_sentimientos || {}
    console.log("Datos de sentimientos:", sentiments)

    if (Object.keys(sentiments).length === 0) {
      container.innerHTML = `
        <div class="chart-error">
          <div>
            <i class="fas fa-exclamation-triangle"></i>
            <p>No hay datos de sentimientos disponibles</p>
          </div>
        </div>
      `
      return
    }

    const data = [
      {
        values: Object.values(sentiments),
        labels: Object.keys(sentiments).map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
        type: "pie",
        marker: {
          colors: [currentTheme.positive, currentTheme.negative, currentTheme.neutral],
        },
        hole: 0.4,
        textinfo: "label+percent",
        textposition: "outside",
      },
    ]

    const layout = {
      title: {
        text: "Distribución de Sentimientos",
        font: { size: 16 },
      },
      font: { family: "Segoe UI, sans-serif" },
      showlegend: true,
      height: 400,
      margin: { t: 50, b: 50, l: 50, r: 50 },
    }

    const config = {
      responsive: true,
      displayModeBar: false,
    }

    await Plotly.newPlot(containerId, data, layout, config)
    console.log("Gráfico de sentimientos generado exitosamente")
  } catch (error) {
    console.error("Error generando gráfico de sentimientos:", error)
    container.innerHTML = `
      <div class="chart-error">
        <div>
          <i class="fas fa-exclamation-circle"></i>
          <p>Error generando gráfico de sentimientos</p>
          <small>${error.message}</small>
        </div>
      </div>
    `
    throw error
  }
}

// Gráfico de productos (barras horizontales)
async function generateProductsChart() {
  const containerId = "products-chart"
  const container = document.getElementById(containerId)

  if (!container) {
    throw new Error(`Contenedor ${containerId} no encontrado`)
  }

  try {
    console.log("Generando gráfico de productos...")

    const products = chartsData.productos_más_mencionados || {}
    console.log("Datos de productos:", products)

    if (Object.keys(products).length === 0) {
      container.innerHTML = `
        <div class="chart-error">
          <div>
            <i class="fas fa-exclamation-triangle"></i>
            <p>No hay datos de productos disponibles</p>
          </div>
        </div>
      `
      return
    }

    const sortedProducts = Object.entries(products)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10) // Mostrar solo top 10

    const data = [
      {
        x: sortedProducts.map(([, count]) => count),
        y: sortedProducts.map(([name]) => name),
        type: "bar",
        orientation: "h",
        marker: {
          color: "rgba(102, 126, 234, 0.8)",
          line: { color: "rgba(102, 126, 234, 1)", width: 2 },
        },
      },
    ]

    const layout = {
      title: {
        text: "Productos Más Mencionados",
        font: { size: 16 },
      },
      xaxis: { title: "Menciones" },
      yaxis: { title: "Productos", automargin: true },
      font: { family: "Segoe UI, sans-serif" },
      height: 400,
      margin: { l: 150, r: 40, t: 60, b: 40 },
    }

    const config = {
      responsive: true,
      displayModeBar: false,
    }

    await Plotly.newPlot(containerId, data, layout, config)
    console.log("Gráfico de productos generado exitosamente")
  } catch (error) {
    console.error("Error generando gráfico de productos:", error)
    container.innerHTML = `
      <div class="chart-error">
        <div>
          <i class="fas fa-exclamation-circle"></i>
          <p>Error generando gráfico de productos</p>
          <small>${error.message}</small>
        </div>
      </div>
    `
    throw error
  }
}

// Gráfico de marcas (barras horizontales)
async function generateBrandsChart() {
  const containerId = "brands-chart"
  const container = document.getElementById(containerId)

  if (!container) {
    throw new Error(`Contenedor ${containerId} no encontrado`)
  }

  try {
    console.log("Generando gráfico de marcas...")

    const brands = chartsData.marcas_más_mencionadas || {}
    console.log("Datos de marcas:", brands)

    if (Object.keys(brands).length === 0) {
      container.innerHTML = `
        <div class="chart-error">
          <div>
            <i class="fas fa-exclamation-triangle"></i>
            <p>No hay datos de marcas disponibles</p>
          </div>
        </div>
      `
      return
    }

    const sortedBrands = Object.entries(brands)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10) // Mostrar solo top 10

    const data = [
      {
        x: sortedBrands.map(([, count]) => count),
        y: sortedBrands.map(([name]) => name),
        type: "bar",
        orientation: "h",
        marker: {
          color: "rgba(118, 75, 162, 0.8)",
          line: { color: "rgba(118, 75, 162, 1)", width: 2 },
        },
      },
    ]

    const layout = {
      title: {
        text: "Marcas Más Populares",
        font: { size: 16 },
      },
      xaxis: { title: "Menciones" },
      yaxis: { title: "Marcas", automargin: true },
      font: { family: "Segoe UI, sans-serif" },
      height: 400,
      margin: { l: 150, r: 40, t: 60, b: 40 },
    }

    const config = {
      responsive: true,
      displayModeBar: false,
    }

    await Plotly.newPlot(containerId, data, layout, config)
    console.log("Gráfico de marcas generado exitosamente")
  } catch (error) {
    console.error("Error generando gráfico de marcas:", error)
    container.innerHTML = `
      <div class="chart-error">
        <div>
          <i class="fas fa-exclamation-circle"></i>
          <p>Error generando gráfico de marcas</p>
          <small>${error.message}</small>
        </div>
      </div>
    `
    throw error
  }
}

// Gráfico de eventos (pie)
async function generateEventsChart() {
  const containerId = "events-chart"
  const container = document.getElementById(containerId)

  if (!container) {
    throw new Error(`Contenedor ${containerId} no encontrado`)
  }

  try {
    console.log("Generando gráfico de eventos...")

    const events = chartsData.tipos_eventos_más_comunes || {}
    console.log("Datos de eventos:", events)

    if (Object.keys(events).length === 0) {
      container.innerHTML = `
        <div class="chart-error">
          <div>
            <i class="fas fa-exclamation-triangle"></i>
            <p>No hay datos de eventos disponibles</p>
          </div>
        </div>
      `
      return
    }

    const data = [
      {
        values: Object.values(events),
        labels: Object.keys(events).map((e) => e.charAt(0).toUpperCase() + e.slice(1)),
        type: "pie",
        textinfo: "label+percent",
        textposition: "outside",
        marker: {
          colors: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"],
        },
      },
    ]

    const layout = {
      title: {
        text: "Distribución de Tipos de Eventos",
        font: { size: 16 },
      },
      font: { family: "Segoe UI, sans-serif" },
      height: 400,
      showlegend: true,
      margin: { t: 50, b: 50, l: 50, r: 50 },
    }

    const config = {
      responsive: true,
      displayModeBar: false,
    }

    await Plotly.newPlot(containerId, data, layout, config)
    console.log("Gráfico de eventos generado exitosamente")
  } catch (error) {
    console.error("Error generando gráfico de eventos:", error)
    container.innerHTML = `
      <div class="chart-error">
        <div>
          <i class="fas fa-exclamation-circle"></i>
          <p>Error generando gráfico de eventos</p>
          <small>${error.message}</small>
        </div>
      </div>
    `
    throw error
  }
}

// Actualizar estadísticas
function updateStats() {
  console.log(`Estadísticas actualizadas: ${chartsGenerated} gráficos generados`)
}

// Funciones auxiliares
function showLoading(show) {
  const overlay = document.getElementById("loading-overlay")
  if (overlay) {
    overlay.style.display = show ? "flex" : "none"
  }
}

function showNotification(message, type = "info") {
  // Crear elemento de notificación
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas fa-${getNotificationIcon(type)}</i>
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