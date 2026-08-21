import { beforeEach, describe, expect, test, vi } from 'vitest'

const { JsPdfMock, pdf, jsPdfConstructor } = vi.hoisted(() => {
  const pdfDocument = {
    text: vi.fn(),
    addImage: vi.fn(),
    save: vi.fn(),
  }
  const constructorSpy = vi.fn()

  class JsPdfClassMock {
    constructor(options) {
      constructorSpy(options)
      return pdfDocument
    }
  }

  return {
    JsPdfMock: JsPdfClassMock,
    pdf: pdfDocument,
    jsPdfConstructor: constructorSpy,
  }
})

vi.mock('jspdf', () => ({
  default: JsPdfMock,
}))

import { exportChartToPdf } from './exportPdf'

describe('exportChartToPdf', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('carrega e executa o exportador somente quando solicitado', async () => {
    const chart = {
      toBase64Image: vi.fn(() => 'data:image/png;base64,chart'),
    }

    expect(jsPdfConstructor).not.toHaveBeenCalled()

    await expect(exportChartToPdf(chart)).resolves.toBe(true)

    expect(jsPdfConstructor).toHaveBeenCalledWith({ orientation: 'landscape' })
    expect(chart.toBase64Image).toHaveBeenCalledOnce()
    expect(pdf.text).toHaveBeenCalledWith('Estatísticas de estudo', 14, 15)
    expect(pdf.addImage).toHaveBeenCalledWith(
      'data:image/png;base64,chart',
      'PNG',
      14,
      25,
      260,
      120,
    )
    expect(pdf.save).toHaveBeenCalledWith('estatisticas-anki-generator.pdf')
  })

  test('ignora a exportação quando o gráfico ainda não está disponível', async () => {
    await expect(exportChartToPdf(null)).resolves.toBe(false)

    expect(jsPdfConstructor).not.toHaveBeenCalled()
  })
})
