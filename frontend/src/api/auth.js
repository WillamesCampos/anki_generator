import { apiFetch, clearTokens, getRefreshToken, setTokens } from "./client";

// Resposta confirmada inspecionando dj-rest-auth 7.2.0 (JWTSerializer)
// instalado no projeto: {"access": ..., "refresh": ..., "user": {...}}.
//
// Só login — cadastro (registro de conta nova) e vínculo com conta Google
// pelo mesmo e-mail ainda estão no backlog de refinamento (PRD.md, 7.1),
// pendentes de decisão sobre verificação de e-mail/EMAIL_BACKEND.
export async function loginWithPassword(email, password) {
  const data = await apiFetch("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setTokens({ access: data.access, refresh: data.refresh });
  return data.user;
}

export async function loginWithGoogle(googleAccessToken) {
  const data = await apiFetch("/auth/google/", {
    method: "POST",
    body: JSON.stringify({ access_token: googleAccessToken }),
  });
  setTokens({ access: data.access, refresh: data.refresh });
  return data.user;
}

export async function logout() {
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await apiFetch("/auth/logout/", {
        method: "POST",
        body: JSON.stringify({ refresh }),
      });
    }
  } finally {
    clearTokens();
  }
}
