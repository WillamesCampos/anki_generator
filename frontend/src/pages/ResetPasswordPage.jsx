import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { confirmPasswordReset } from "../api/auth";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import "./LoginPage.css";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");

  const [newPassword1, setNewPassword1] = useState("");
  const [newPassword2, setNewPassword2] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  if (!uid || !token) {
    return (
      <main className="login-page">
        <h1 className="login-page__title">Link inválido</h1>
        <p className="login-page__error">
          Este link de redefinição de senha está incompleto ou inválido.
        </p>
        <Link to="/esqueci-minha-senha" className="login-page__divider">
          Solicitar um novo link
        </Link>
      </main>
    );
  }

  if (done) {
    return (
      <main className="login-page">
        <h1 className="login-page__title">Senha redefinida</h1>
        <p className="login-page__google-message">Sua senha foi alterada com sucesso.</p>
        <Link to="/login" className="login-page__divider">
          Ir para o login
        </Link>
      </main>
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (newPassword1 !== newPassword2) {
      setError("As senhas não coincidem.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await confirmPasswordReset({ uid, token, newPassword1, newPassword2 });
      setDone(true);
    } catch {
      setError("Não foi possível redefinir a senha. O link pode ter expirado ou já ter sido usado.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <h1 className="login-page__title">Criar nova senha</h1>

      <form className="login-page__form" onSubmit={handleSubmit}>
        <Input
          label="Nova senha"
          type="password"
          value={newPassword1}
          onChange={(event) => setNewPassword1(event.target.value)}
          required
        />
        <Input
          label="Confirmar nova senha"
          type="password"
          value={newPassword2}
          onChange={(event) => setNewPassword2(event.target.value)}
          required
        />
        {error && <p className="login-page__error">{error}</p>}
        <Button type="submit">{submitting ? "Salvando…" : "Redefinir senha"}</Button>
      </form>
    </main>
  );
}
