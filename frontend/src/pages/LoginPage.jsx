import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginWithGoogle, loginWithPassword } from "../api/auth";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import useAuth from "../context/useAuth";
import "./LoginPage.css";

// Client ID (público) do mesmo projeto OAuth cujo Client ID/Secret já são
// esperados em django/.env (GOOGLE_OAUTH_CLIENT_ID/SECRET) — ver
// frontend/.env.example. Ainda não configurado com credenciais reais (ver
// PRD Sprint 3, tarefa 3.7): o botão fica desabilitado até existir.
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function LoginPage() {
  const navigate = useNavigate();
  const { markAuthenticated } = useAuth();
  const tokenClientRef = useRef(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !window.google?.accounts?.oauth2) return;

    // Fluxo de OAuth2 "token client" (access_token), não o botão de "Sign
    // In" mais novo do Google Identity Services (que devolve um ID token/JWT)
    // — o backend (GoogleOAuth2Adapter/OAuth2Client do allauth, ver
    // apps/accounts/views.py) espera um access_token OAuth2 de verdade.
    tokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: "openid email profile",
      callback: async (response) => {
        if (!response.access_token) return;
        await loginWithGoogle(response.access_token);
        markAuthenticated();
        navigate("/", { replace: true });
      },
    });
  }, [markAuthenticated, navigate]);

  function handleGoogleLogin() {
    if (!tokenClientRef.current) {
      console.error("Google Identity Services não carregou (VITE_GOOGLE_CLIENT_ID ausente ou script bloqueado).");
      return;
    }
    tokenClientRef.current.requestAccessToken();
  }

  async function handlePasswordLogin(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginWithPassword(email, password);
      markAuthenticated();
      navigate("/", { replace: true });
    } catch {
      setError("E-mail ou senha incorretos.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <h1 className="login-page__title">Anki Generator</h1>

      <form className="login-page__form" onSubmit={handlePasswordLogin}>
        <Input
          label="E-mail"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <Input
          label="Senha"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && <p className="login-page__error">{error}</p>}
        <Button type="submit">{submitting ? "Entrando…" : "Entrar"}</Button>
      </form>

      <div className="login-page__divider">ou</div>

      {GOOGLE_CLIENT_ID ? (
        <Button onClick={handleGoogleLogin} variant="secondary">
          Entrar com Google
        </Button>
      ) : (
        <p className="login-page__google-message">
          Login com Google ainda não configurado (<code>VITE_GOOGLE_CLIENT_ID</code> vazio). Veja{" "}
          <code>frontend/README.md</code>.
        </p>
      )}
    </main>
  );
}
