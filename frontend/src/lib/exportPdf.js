export async function exportChartToPdf(chart) {
  if (!chart) return false

  const { default: jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ orientation: 'landscape' })

  pdf.text('Estatísticas de estudo', 14, 15)
  pdf.addImage(chart.toBase64Image(), 'PNG', 14, 25, 260, 120)
  pdf.save('estatisticas-anki-generator.pdf')

  return true
}
