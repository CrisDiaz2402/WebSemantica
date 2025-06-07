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
  document.getElementById("generate-charts").addEventListener("click", generateAllCharts)
  document.getElementById("refresh-data").addEventListener("click", refreshData)
}

// Cargar datos para visualización
async function loadVisualizationData() {
  try {
    showLoading(true)
    const response = await fetch("/api/report")
    const data = await response.json()

    if (response.ok) {
      chartsData = data
      console.log("Datos cargados:", chartsData)
    } else {
      showNotification("Error cargando datos: " + data.error, "error")
    }
  } catch (error) {
    console.error("Error:", error)
    showNotification("Error de conexión al cargar datos", "error")
  } finally {
    showLoading(false)
  }
}

// Generar todos los gráficos
async function generateAllCharts() {
  if (!chartsData) {
    showNotification("No hay datos disponibles. Carga un archivo CSV primero.", "warning")
    return
  }

  showLoading(true)
  chartsGenerated = 0

  try {
    await Promise.all([
      generateSentimentChart(),
      generateProductsChart(),
      generateBrandsChart(),
      generateEventsChart(),
      generateTimelineChart(),
    ])

    showNotification("Todas las visualizaciones generadas exitosamente", "success")
    updateStats()
  } catch (error) {
    console.error("Error generando gráficos:", error)
    showNotification("Error generando algunas visualizaciones", "error")
  } finally {
    showLoading(false)
  }
}

// Gráfico de sentimientos (siempre dona)
async function generateSentimentChart() {
  const sentiments = chartsData.distribución_sentimientos || {}

  const data = [
    {
      values: Object.values(sentiments),
      labels: Object.keys(sentiments).map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
      type: "pie",
      marker: {
        colors: [currentTheme.positive, currentTheme.negative, currentTheme.neutral],
      },
      hole: 0.4,
    },
  ]

  const layout = {
    title: "Distribución de Sentimientos",
    font: { family: "Segoe UI, sans-serif" },
    showlegend: true,
    height: 400,
  }

  await Plotly.newPlot("sentiment-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de productos (barras horizontales)
async function generateProductsChart() {
  const products = chartsData.productos_más_mencionados || {}

  const sortedProducts = Object.entries(products)
    .sort(([, a], [, b]) => b - a)

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
    title: "Most Mentioned Products",
    xaxis: { title: "Mentions" },
    yaxis: { title: "Products", automargin: true },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
    margin: { l: 120, r: 40, t: 60, b: 40 }
  }

  await Plotly.newPlot("products-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de marcas (barras horizontales)
async function generateBrandsChart() {
  const brands = chartsData.marcas_más_mencionadas || {}

  const sortedBrands = Object.entries(brands)
    .sort(([, a], [, b]) => b - a)

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
    title: "Most Popular Brands",
    xaxis: { title: "Mentions" },
    yaxis: { title: "Brands", automargin: true },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
    margin: { l: 120, r: 40, t: 60, b: 40 }
  }

  await Plotly.newPlot("brands-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de eventos (pie)
async function generateEventsChart() {
  const events = chartsData.tipos_eventos_más_comunes || {}

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
    title: "Distribución de Tipos de Eventos",
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
    showlegend: true,
  }

  await Plotly.newPlot("events-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Actualizar estadísticas
function updateStats() {
  // Si tienes elementos de stats, actualízalos aquí
}

// Funciones auxiliares
function showLoading(show) {
  const overlay = document.getElementById("loading-overlay")
  if (overlay) {
    overlay.style.display = show ? "flex" : "none"
  }
}

function showNotification(message, type = "info") {
  if (window.showNotification) {
    window.showNotification(message, type)
  } else {
    console.log(`${type.toUpperCase()}: ${message}`)
  }
}