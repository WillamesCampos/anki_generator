import { useState } from "react";
import { Link } from "react-router-dom";

import { requestPasswordReset } from "../api/auth";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import "./LoginPage.css";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await requestPasswordReset(email);
    } catch {
      // Ignorado de propósito: sempre mostra a mesma mensagem, com sucesso
      // ou erro — o backend já não revela se o e-mail existe (sempre 200);
      // o frontend segue o mesmo princípio, sem distinguir os dois casos.
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  }

  return (
    <main className="login-page">
      <h1 className="login-page__title">Esqueci minha senha</h1>

      {submitted ? (
        <p className="login-page__google-message">
          Se esse e-mail estiver cadastrado, você vai receber um link para redefinir sua senha.
        </p>
      ) : (
        <form className="login-page__form" onSubmit={handleSubmit}>
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <Button type="submit">{submitting ? "Enviando…" : "Enviar link"}</Button>
        </form>
      )}

      <Link to="/login" className="login-page__divider">
        Voltar ao login
      </Link>
    </main>
  );
}
