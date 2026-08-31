import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import ConfirmDialog from "./ConfirmDialog";

describe("ConfirmDialog", () => {
  test("não renderiza quando está fechado", () => {
    render(<ConfirmDialog open={false} title="Excluir deck" onConfirm={() => {}} onCancel={() => {}} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  test("avisa sobre os sete dias e exige confirmação explícita", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <ConfirmDialog
        open
        title="Excluir deck"
        message="Este deck entrará na janela de retenção antes da remoção permanente."
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByRole("dialog", { name: "Excluir deck" })).toHaveTextContent("7 dias");

    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));

    expect(onCancel).toHaveBeenCalledOnce();
    expect(onConfirm).toHaveBeenCalledOnce();
  });
});
