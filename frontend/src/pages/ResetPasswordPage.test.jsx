import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { confirmPasswordReset } from "../api/auth";
import ResetPasswordPage from "./ResetPasswordPage";

vi.mock("../api/auth", () => ({
  confirmPasswordReset: vi.fn(),
}));

function renderPage(search = "?uid=1&token=abc-123") {
  return render(
    <MemoryRouter initialEntries={[`/redefinir-senha${search}`]}>
      <Routes>
        <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("redefinir senha", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("link sem uid/token mostra estado de link inválido", () => {
    renderPage("");

    expect(screen.getByRole("heading", { name: "Link inválido" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Solicitar um novo link" })).toHaveAttribute(
      "href",
      "/esqueci-minha-senha",
    );
  });

  test("senhas diferentes não chegam a chamar a API", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Nova senha"), "senha-nova-123");
    await user.type(screen.getByLabelText("Confirmar nova senha"), "outra-coisa");
    await user.click(screen.getByRole("button", { name: "Redefinir senha" }));

    expect(await screen.findByText("As senhas não coincidem.")).toBeInTheDocument();
    expect(confirmPasswordReset).not.toHaveBeenCalled();
  });

  test("sucesso mostra confirmação e chama a API com uid/token da URL", async () => {
    const user = userEvent.setup();
    confirmPasswordReset.mockResolvedValue({ detail: "ok" });
    renderPage();

    await user.type(screen.getByLabelText("Nova senha"), "senha-nova-123");
    await user.type(screen.getByLabelText("Confirmar nova senha"), "senha-nova-123");
    await user.click(screen.getByRole("button", { name: "Redefinir senha" }));

    expect(await screen.findByRole("heading", { name: "Senha redefinida" })).toBeInTheDocument();
    expect(confirmPasswordReset).toHaveBeenCalledWith({
      uid: "1",
      token: "abc-123",
      newPassword1: "senha-nova-123",
      newPassword2: "senha-nova-123",
    });
  });

  test("token inválido/expirado mostra mensagem de erro", async () => {
    const user = userEvent.setup();
    confirmPasswordReset.mockRejectedValue(new Error("400"));
    renderPage();

    await user.type(screen.getByLabelText("Nova senha"), "senha-nova-123");
    await user.type(screen.getByLabelText("Confirmar nova senha"), "senha-nova-123");
    await user.click(screen.getByRole("button", { name: "Redefinir senha" }));

    expect(
      await screen.findByText(
        "Não foi possível redefinir a senha. O link pode ter expirado ou já ter sido usado.",
      ),
    ).toBeInTheDocument();
  });
});
