// Camada fina de acesso à API do Django (/api/v1/...).
//
// Guarda access + refresh token (localStorage). Num 401, tenta renovar via
// /auth/token/refresh/ automaticamente e repete a chamada original uma
// única vez — só se essa segunda tentativa também falhar (refresh
// inválido/expirado/ausente) é que a sessão é considerada encerrada
// (evento "auth:session-expired", ouvido pelo AuthContext).

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const ACCESS_TOKEN_KEY = "anki_generator_access_token";
const REFRESH_TOKEN_KEY = "anki_generator_refresh_token";
const SESSION_EXPIRED_EVENT = "auth:session-expired";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function onSessionExpired(handler) {
  window.addEventListener(SESSION_EXPIRED_EVENT, handler);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handler);
}

function notifySessionExpired() {
  clearTokens();
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function rawFetch(path, options, token) {
  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}

// Compartilhada entre chamadas concorrentes: se duas requisições levarem
// 401 ao mesmo tempo (ex.: Home disparando /reviews/ e /decks/{id}/ perto
// uma da outra), só um /auth/token/refresh/ real é feito — economiza uma
// chamada do orçamento global, além de evitar corrida.
let refreshPromise = null;

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refresh = getRefreshToken();
      if (!refresh) {
        throw new ApiError("No refresh token available", 401);
      }

      const response = await rawFetch("/auth/token/refresh/", {
        method: "POST",
        body: JSON.stringify({ refresh }),
      });

      if (!response.ok) {
        throw new ApiError("Refresh token invalid or expired", response.status);
      }

      const data = await response.json();
      setTokens({ access: data.access, refresh: data.refresh });
      return data.access;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

// Login/Google login não devem levar um access token guardado — se sobrou
// um token velho/inválido no localStorage (de uma sessão anterior), o DRF
// rejeita a request inteira com 401 assim que vê um Authorization header
// inválido, mesmo antes de validar email/senha. Bug real encontrado
// investigando um "login não funciona" que na verdade eram credenciais
// corretas sendo bloqueadas por um token velho.
const UNAUTHENTICATED_PATHS = [
  "/auth/login/",
  "/auth/google/",
  "/auth/password/reset/",
  "/auth/password/reset/confirm/",
];

export async function apiFetch(path, options = {}, { isRetry = false } = {}) {
  const token = UNAUTHENTICATED_PATHS.includes(path) ? null : getAccessToken();
  const response = await rawFetch(path, options, token);

  if (response.status === 401 && !isRetry && !path.startsWith("/auth/")) {
    try {
      await refreshAccessToken();
    } catch {
      notifySessionExpired();
      throw new ApiError(`${options.method || "GET"} ${path} failed with 401: sessão expirada`, 401);
    }
    return apiFetch(path, options, { isRetry: true });
  }

  // 403 é distinto de outros erros (Sprint 6, forbidden-error-handling): a
  // partir da Sprint 5 (permissão por grupo) esse status passa a poder
  // acontecer de verdade — usuário autenticado, mas sem permissão pra essa
  // ação. Mensagem clara em vez do texto técnico genérico abaixo.
  if (response.status === 403) {
    throw new ApiError("Você não tem permissão para executar essa ação.", 403);
  }

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(
      `${options.method || "GET"} ${path} failed with ${response.status}${body ? `: ${body}` : ""}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
