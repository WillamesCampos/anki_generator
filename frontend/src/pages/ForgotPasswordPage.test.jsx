import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { requestPasswordReset } from "../api/auth";
import ForgotPasswordPage from "./ForgotPasswordPage";

vi.mock("../api/auth", () => ({
  requestPasswordReset: vi.fn(),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );
}

describe("esqueci minha senha", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("envia o e-mail e mostra a mesma mensagem em caso de sucesso", async () => {
    const user = userEvent.setup();
    requestPasswordReset.mockResolvedValue({ detail: "ok" });

    renderPage();

    await user.type(screen.getByLabelText("E-mail"), "ana@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar link" }));

    expect(
      await screen.findByText(
        "Se esse e-mail estiver cadastrado, você vai receber um link para redefinir sua senha.",
      ),
    ).toBeInTheDocument();
    expect(requestPasswordReset).toHaveBeenCalledWith("ana@example.com");
  });

  test("mostra a mesma mensagem mesmo se a chamada falhar (não revela se o e-mail existe)", async () => {
    const user = userEvent.setup();
    requestPasswordReset.mockRejectedValue(new Error("network error"));

    renderPage();

    await user.type(screen.getByLabelText("E-mail"), "nao-existe@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar link" }));

    expect(
      await screen.findByText(
        "Se esse e-mail estiver cadastrado, você vai receber um link para redefinir sua senha.",
      ),
    ).toBeInTheDocument();
  });
});
