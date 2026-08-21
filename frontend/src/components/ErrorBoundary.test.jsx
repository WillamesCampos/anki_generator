import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import ErrorBoundary from './ErrorBoundary'

function BrokenChild() {
  throw new Error('falha de renderização')
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('substitui uma falha de renderização por uma tela de recuperação', () => {
    render(
      <ErrorBoundary>
        <BrokenChild />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Não foi possível carregar a aplicação',
    )
  })
})
