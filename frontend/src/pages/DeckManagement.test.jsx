import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { createCategory, fetchCategories } from "../api/categories";
import { createDeck, fetchDecks } from "../api/decks";
import DeckListPage from "./DeckListPage";
import NewDeckPage from "./NewDeckPage";

vi.mock("../api/categories", () => ({
  createCategory: vi.fn(),
  fetchCategories: vi.fn(),
}));

vi.mock("../api/decks", () => ({
  createDeck: vi.fn(),
  fetchDecks: vi.fn(),
}));

function renderNewDeckPage() {
  return render(
    <MemoryRouter initialEntries={["/decks/novo"]}>
      <Routes>
        <Route path="/decks/novo" element={<NewDeckPage />} />
        <Route path="/decks/:deckId" element={<p>Detalhe criado</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("gerenciamento de decks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchCategories.mockResolvedValue({ results: [] });
  });

  test("mostra estado vazio e acesso à criação quando não há decks", async () => {
    fetchDecks.mockResolvedValue({ results: [] });

    render(
      <MemoryRouter>
        <DeckListPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Você ainda não criou nenhum deck.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Criar primeiro deck" })).toHaveAttribute("href", "/decks/novo");
  });

  test("lista título e descrição dos decks com link para o detalhe", async () => {
    fetchDecks.mockResolvedValue({
      results: [{ id: "deck-1", title: "Inglês técnico", description: "Vocabulário de backend" }],
    });

    render(
      <MemoryRouter>
        <DeckListPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Inglês técnico" })).toBeInTheDocument();
    expect(screen.getByText("Vocabulário de backend")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir deck Inglês técnico" })).toHaveAttribute(
      "href",
      "/decks/deck-1",
    );
  });

  test("cria um deck válido e navega para o detalhe", async () => {
    const user = userEvent.setup();
    fetchCategories.mockResolvedValue({ results: [{ id: "cat-1", name: "Idiomas" }] });
    createDeck.mockResolvedValue({ id: "deck-novo", title: "Inglês" });
    renderNewDeckPage();

    await user.type(screen.getByLabelText("Título"), "Inglês");
    await user.type(screen.getByLabelText("Descrição"), "Vocabulário diário");
    await user.selectOptions(await screen.findByLabelText("Categoria"), "cat-1");
    await user.type(screen.getByLabelText("Meta diária de revisões"), "20");
    await user.click(screen.getByRole("button", { name: "Criar deck" }));

    await waitFor(() => {
      expect(createDeck).toHaveBeenCalledWith({
        title: "Inglês",
        description: "Vocabulário diário",
        category_id: "cat-1",
        daily_review_goal: 20,
      });
    });
    expect(await screen.findByText("Detalhe criado")).toBeInTheDocument();
  });

  test("cria categoria inline e a seleciona antes de criar o deck", async () => {
    const user = userEvent.setup();
    createCategory.mockResolvedValue({ id: "cat-2", name: "Programação" });
    createDeck.mockResolvedValue({ id: "deck-2", title: "Python" });
    renderNewDeckPage();

    await user.type(screen.getByLabelText("Título"), "Python");
    await user.selectOptions(await screen.findByLabelText("Categoria"), "__new__");
    expect(screen.getByRole("button", { name: "Criar deck" })).toBeDisabled();
    await user.type(screen.getByLabelText("Nome da nova categoria"), "Programação");
    await user.click(screen.getByRole("button", { name: "Criar categoria" }));

    await waitFor(() => expect(createCategory).toHaveBeenCalledWith({ name: "Programação" }));
    expect(screen.getByLabelText("Categoria")).toHaveValue("cat-2");
    expect(screen.getByRole("button", { name: "Criar deck" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Criar deck" }));

    await waitFor(() => {
      expect(createDeck).toHaveBeenCalledWith(
        expect.objectContaining({ category_id: "cat-2" }),
      );
    });
  });
});
