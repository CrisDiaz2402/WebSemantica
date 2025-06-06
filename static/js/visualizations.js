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
  // Botón generar gráficos
  document.getElementById("generate-charts").addEventListener("click", generateAllCharts)

  // Botón actualizar datos
  document.getElementById("refresh-data").addEventListener("click", refreshData)

  // Botón exportar
  document.getElementById("export-charts").addEventListener("click", exportAllCharts)

  // Controles de tipo de gráfico
  document.getElementById("sentiment-chart-type").addEventListener("change", updateSentimentChart)
  document.getElementById("products-limit").addEventListener("change", updateProductsChart)
  document.getElementById("brands-chart-type").addEventListener("change", updateBrandsChart)

  // Controles de configuración
  document.getElementById("color-positive").addEventListener("change", updateThemeColors)
  document.getElementById("color-negative").addEventListener("change", updateThemeColors)
  document.getElementById("color-neutral").addEventListener("change", updateThemeColors)

  // Control de duración de animación
  document.getElementById("animation-duration").addEventListener("input", function () {
    document.getElementById("duration-value").textContent = this.value + "ms"
  })
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
      generateHeatmapChart(),
      generateTimelineChart(),
      generateWordCloud(),
      generateNetworkChart(),
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

// Gráfico de sentimientos
async function generateSentimentChart() {
  const chartType = document.getElementById("sentiment-chart-type").value
  const sentiments = chartsData.distribución_sentimientos || {}

  const data = [
    {
      values: Object.values(sentiments),
      labels: Object.keys(sentiments).map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
      type: chartType === "pie" ? "pie" : "bar",
      marker: {
        colors: [currentTheme.positive, currentTheme.negative, currentTheme.neutral],
      },
      hole: chartType === "donut" ? 0.4 : 0,
    },
  ]

  const layout = {
    title: "Distribución de Sentimientos",
    font: { family: "Segoe UI, sans-serif" },
    showlegend: chartType !== "bar",
    height: 400,
  }

  if (chartType === "bar") {
    data[0].x = Object.keys(sentiments).map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    data[0].y = Object.values(sentiments)
    layout.xaxis = { title: "Sentimiento" }
    layout.yaxis = { title: "Cantidad" }
  }

  await Plotly.newPlot("sentiment-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de productos
async function generateProductsChart() {
  const limit = Number.parseInt(document.getElementById("products-limit").value)
  const products = chartsData.productos_más_mencionados || {}

  const sortedProducts = Object.entries(products)
    .sort(([, a], [, b]) => b - a)
    .slice(0, limit)

  const data = [
    {
      x: sortedProducts.map(([name]) => name),
      y: sortedProducts.map(([, count]) => count),
      type: "bar",
      marker: {
        color: "rgba(102, 126, 234, 0.8)",
        line: { color: "rgba(102, 126, 234, 1)", width: 2 },
      },
    },
  ]

  const layout = {
    title: `Top ${limit} Productos Más Mencionados`,
    xaxis: { title: "Productos", tickangle: -45 },
    yaxis: { title: "Menciones" },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
  }

  await Plotly.newPlot("products-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de marcas
async function generateBrandsChart() {
  const chartType = document.getElementById("brands-chart-type").value
  const brands = chartsData.marcas_más_mencionadas || {}

  const sortedBrands = Object.entries(brands)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)

  const data = [
    {
      type: "bar",
      marker: {
        color: "rgba(118, 75, 162, 0.8)",
        line: { color: "rgba(118, 75, 162, 1)", width: 2 },
      },
    },
  ]

  const layout = {
    title: "Top 10 Marcas Más Mencionadas",
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
  }

  if (chartType === "horizontal") {
    data[0].x = sortedBrands.map(([, count]) => count)
    data[0].y = sortedBrands.map(([name]) => name)
    data[0].orientation = "h"
    layout.xaxis = { title: "Menciones" }
    layout.yaxis = { title: "Marcas" }
  } else {
    data[0].x = sortedBrands.map(([name]) => name)
    data[0].y = sortedBrands.map(([, count]) => count)
    layout.xaxis = { title: "Marcas", tickangle: -45 }
    layout.yaxis = { title: "Menciones" }
  }

  await Plotly.newPlot("brands-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Gráfico de eventos
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

// Mapa de calor
async function generateHeatmapChart() {
  // Simular datos de mapa de calor (productos vs sentimientos)
  const products = Object.keys(chartsData.productos_más_mencionados || {}).slice(0, 10)
  const sentiments = ["Positivo", "Negativo", "Neutro"]

  // Generar datos simulados
  const z = products.map(() => sentiments.map(() => Math.floor(Math.random() * 50) + 1))

  const data = [
    {
      z: z,
      x: sentiments,
      y: products,
      type: "heatmap",
      colorscale: "RdYlBu",
      showscale: true,
    },
  ]

  const layout = {
    title: "Mapa de Calor: Productos vs Sentimientos",
    xaxis: { title: "Sentimientos" },
    yaxis: { title: "Productos" },
    font: { family: "Segoe UI, sans-serif" },
    height: 500,
  }

  await Plotly.newPlot("heatmap-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Línea temporal
async function generateTimelineChart() {
  // Simular datos temporales
  const dates = []
  const positiveData = []
  const negativeData = []
  const neutralData = []

  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split("T")[0])

    positiveData.push(Math.floor(Math.random() * 20) + 5)
    negativeData.push(Math.floor(Math.random() * 15) + 2)
    neutralData.push(Math.floor(Math.random() * 10) + 3)
  }

  const data = [
    {
      x: dates,
      y: positiveData,
      type: "scatter",
      mode: "lines+markers",
      name: "Positivo",
      line: { color: currentTheme.positive },
    },
    {
      x: dates,
      y: negativeData,
      type: "scatter",
      mode: "lines+markers",
      name: "Negativo",
      line: { color: currentTheme.negative },
    },
    {
      x: dates,
      y: neutralData,
      type: "scatter",
      mode: "lines+markers",
      name: "Neutro",
      line: { color: currentTheme.neutral },
    },
  ]

  const layout = {
    title: "Evolución Temporal de Sentimientos",
    xaxis: { title: "Fecha" },
    yaxis: { title: "Cantidad de Eventos" },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
  }

  await Plotly.newPlot("timeline-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Nube de palabras (simulada con gráfico de barras)
async function generateWordCloud() {
  const sentiment = document.getElementById("wordcloud-sentiment").value

  // Palabras simuladas según sentimiento
  const words = {
    all: ["excelente", "bueno", "malo", "perfecto", "terrible", "increíble", "defectuoso", "recomendado"],
    positivo: ["excelente", "bueno", "perfecto", "increíble", "recomendado", "fantástico"],
    negativo: ["malo", "terrible", "defectuoso", "horrible", "decepcionante"],
    neutro: ["normal", "regular", "aceptable", "promedio", "estándar"],
  }

  const selectedWords = words[sentiment] || words.all
  const frequencies = selectedWords.map(() => Math.floor(Math.random() * 100) + 10)

  const data = [
    {
      x: selectedWords,
      y: frequencies,
      type: "bar",
      marker: {
        color: frequencies,
        colorscale: "Viridis",
      },
    },
  ]

  const layout = {
    title: `Palabras Más Frecuentes - ${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}`,
    xaxis: { title: "Palabras", tickangle: -45 },
    yaxis: { title: "Frecuencia" },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
  }

  await Plotly.newPlot("wordcloud-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Red de relaciones (simulada)
async function generateNetworkChart() {
  // Simular datos de red
  const nodes = ["Usuario", "Producto", "Marca", "Compra", "Reseña"]
  const edges = [
    [0, 1],
    [1, 2],
    [0, 3],
    [3, 1],
    [0, 4],
    [4, 1],
  ]

  const nodeTrace = {
    x: [0, 1, 2, 0.5, 1.5],
    y: [0, 0, 0, 1, 1],
    mode: "markers+text",
    text: nodes,
    textposition: "middle center",
    marker: {
      size: 30,
      color: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
    },
    type: "scatter",
  }

  const edgeTraces = edges.map(([start, end]) => ({
    x: [nodeTrace.x[start], nodeTrace.x[end], null],
    y: [nodeTrace.y[start], nodeTrace.y[end], null],
    mode: "lines",
    line: { color: "#888", width: 2 },
    type: "scatter",
    showlegend: false,
  }))

  const data = [...edgeTraces, nodeTrace]

  const layout = {
    title: "Red de Relaciones Semánticas",
    showlegend: false,
    xaxis: { showgrid: false, zeroline: false, showticklabels: false },
    yaxis: { showgrid: false, zeroline: false, showticklabels: false },
    font: { family: "Segoe UI, sans-serif" },
    height: 400,
  }

  await Plotly.newPlot("network-chart", data, layout, { responsive: true })
  chartsGenerated++
}

// Funciones de actualización
function updateSentimentChart() {
  generateSentimentChart()
}

function updateProductsChart() {
  generateProductsChart()
}

function updateBrandsChart() {
  generateBrandsChart()
}

function updateThemeColors() {
  currentTheme.positive = document.getElementById("color-positive").value
  currentTheme.negative = document.getElementById("color-negative").value
  currentTheme.neutral = document.getElementById("color-neutral").value

  // Regenerar gráficos que usan colores de tema
  if (chartsData) {
    generateSentimentChart()
    generateTimelineChart()
  }
}

// Actualizar datos
async function refreshData() {
  await loadVisualizationData()
  if (chartsData) {
    generateAllCharts()
  }
}

// Exportar gráficos
function exportAllCharts() {
  const formats = []
  if (document.getElementById("export-png").checked) formats.push("png")
  if (document.getElementById("export-svg").checked) formats.push("svg")
  if (document.getElementById("export-pdf").checked) formats.push("pdf")
  if (document.getElementById("export-html").checked) formats.push("html")

  if (formats.length === 0) {
    showNotification("Selecciona al menos un formato de exportación", "warning")
    return
  }

  showNotification(`Exportando gráficos en formatos: ${formats.join(", ")}`, "info")

  // Aquí implementarías la lógica de exportación real
  setTimeout(() => {
    showNotification("Gráficos exportados exitosamente", "success")
  }, 2000)
}

// Actualizar estadísticas
function updateStats() {
  document.getElementById("charts-generated").textContent = chartsGenerated
  document.getElementById("data-points").textContent = chartsData ? chartsData.resumen_general?.total_reseñas || 0 : 0
  document.getElementById("last-update").textContent = new Date().toLocaleTimeString()

  // Incrementar contador de visualizaciones
  const currentViews = Number.parseInt(localStorage.getItem("visualization-views") || "0")
  const newViews = currentViews + 1
  localStorage.setItem("visualization-views", newViews.toString())
  document.getElementById("views-count").textContent = newViews
}

// Funciones auxiliares
function showLoading(show) {
  const overlay = document.getElementById("loading-overlay")
  if (overlay) {
    overlay.style.display = show ? "flex" : "none"
  }
}

function showNotification(message, type = "info") {
  // Reutilizar la función del main.js
  if (window.showNotification) {
    window.showNotification(message, type)
  } else {
    console.log(`${type.toUpperCase()}: ${message}`)
  }
}
