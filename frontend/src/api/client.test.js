import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { apiFetch, setTokens } from './client'

function mockFetchOnce(body, init = {}) {
  const fetchMock = vi.fn(() =>
    Promise.resolve(
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        ...init,
      }),
    ),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('não envia um access token guardado na request de login', async () => {
    setTokens({ access: 'token-velho-invalido', refresh: 'refresh-velho' })
    const fetchMock = mockFetchOnce({ access: 'novo', refresh: 'novo', user: {} })

    await apiFetch('/auth/login/', { method: 'POST', body: '{}' })

    const [, requestInit] = fetchMock.mock.calls[0]
    expect(requestInit.headers.Authorization).toBeUndefined()
  })

  test('não envia um access token guardado na request de login com Google', async () => {
    setTokens({ access: 'token-velho-invalido', refresh: 'refresh-velho' })
    const fetchMock = mockFetchOnce({ access: 'novo', refresh: 'novo', user: {} })

    await apiFetch('/auth/google/', { method: 'POST', body: '{}' })

    const [, requestInit] = fetchMock.mock.calls[0]
    expect(requestInit.headers.Authorization).toBeUndefined()
  })

  test('envia o access token guardado em requests autenticadas normais', async () => {
    setTokens({ access: 'token-valido', refresh: 'refresh-valido' })
    const fetchMock = mockFetchOnce({ results: [] })

    await apiFetch('/decks/')

    const [, requestInit] = fetchMock.mock.calls[0]
    expect(requestInit.headers.Authorization).toBe('Bearer token-valido')
  })
})
