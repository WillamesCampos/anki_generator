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

  test('expõe o estado acessível e preserva a preferência manual ao alternar', async () => {
    const user = userEvent.setup()
    localStorage.setItem('anki_generator_sidebar_collapsed', 'false')
    installMatchMedia(true)
    renderSidebar()

    const navigation = screen.getByRole('navigation')
    const toggle = screen.getByRole('button', { name: 'Recolher menu' })
    const navigationList = document.getElementById('sidebar-navigation-list')
    const icon = toggle.querySelector('svg')

    expect(navigation).not.toHaveClass('sidebar--collapsed')
    expect(navigationList).toBeInTheDocument()
    expect(navigationList?.tagName).toBe('UL')
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(toggle).toHaveAttribute('aria-controls', 'sidebar-navigation-list')
    expect(toggle).toHaveAttribute('title', 'Recolher menu')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
    expect(icon).toHaveAttribute('focusable', 'false')

    await user.click(toggle)

    expect(navigation).toHaveClass('sidebar--collapsed')
    expect(screen.getByRole('button', { name: 'Expandir menu' })).toBe(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveAttribute('title', 'Expandir menu')
    expect(localStorage.getItem('anki_generator_sidebar_collapsed')).toBe('true')
  })
})
