import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'

import { AuthProvider } from '../../context/AuthContext'
import Sidebar from './Sidebar'

function installMatchMedia(matches) {
  const listeners = new Set()
  const mediaQuery = {
    matches,
    media: '(max-width: 1024px)',
    onchange: null,
    addEventListener: vi.fn((eventName, listener) => {
      if (eventName === 'change') listeners.add(listener)
    }),
    removeEventListener: vi.fn((eventName, listener) => {
      if (eventName === 'change') listeners.delete(listener)
    }),
    dispatchEvent: vi.fn(),
    emit(nextMatches) {
      this.matches = nextMatches
      listeners.forEach((listener) => listener({ matches: nextMatches }))
    },
  }

  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn(() => mediaQuery),
  })

  return mediaQuery
}

function renderSidebar() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Sidebar />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('Sidebar responsiva', () => {
  test('recolhe automaticamente em viewport de tablet sem preferência manual', () => {
    installMatchMedia(true)

    renderSidebar()

    expect(screen.getByRole('navigation')).toHaveClass('sidebar--collapsed')
  })

  test('acompanha mudanças de viewport enquanto não existe preferência manual', () => {
    const mediaQuery = installMatchMedia(false)
    renderSidebar()

    act(() => mediaQuery.emit(true))

    expect(screen.getByRole('navigation')).toHaveClass('sidebar--collapsed')
  })

  test('preserva e atualiza a preferência manual em viewport de tablet', async () => {
    const user = userEvent.setup()
    localStorage.setItem('anki_generator_sidebar_collapsed', 'false')
    installMatchMedia(true)
    renderSidebar()

    expect(screen.getByRole('navigation')).not.toHaveClass('sidebar--collapsed')

    await user.click(screen.getByRole('button', { name: 'Recolher menu' }))

    expect(screen.getByRole('navigation')).toHaveClass('sidebar--collapsed')
    expect(localStorage.getItem('anki_generator_sidebar_collapsed')).toBe('true')
  })
})
