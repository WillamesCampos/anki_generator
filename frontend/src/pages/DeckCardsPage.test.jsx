import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { createCard, deleteCard, fetchCardsByDeck, updateCard } from "../api/cards";
import { fetchDeck } from "../api/decks";
import DeckCardsPage from "./DeckCardsPage";

vi.mock("../api/cards", () => ({
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  fetchCardsByDeck: vi.fn(),
  updateCard: vi.fn(),
}));

vi.mock("../api/decks", () => ({
  fetchDeck: vi.fn(),
}));

const DECK = { id: "deck-1", title: "Inglês técnico" };
const CARD = {
  id: "card-1",
  deck_id: "deck-1",
  front: "network",
  back: "rede",
  front_description: "The network is stable.",
  back_description: "A rede está estável.",
  tags: ["infra"],
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/decks/deck-1/cards"]}>
      <Routes>
        <Route path="/decks/:deckId/cards" element={<DeckCardsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("cards do deck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchDeck.mockResolvedValue(DECK);
    fetchCardsByDeck.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
  });

  test("mostra o estado vazio na página dedicada", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "Cards de Inglês técnico" })).toBeInTheDocument();
    expect(screen.getByText("Este deck ainda não tem cards.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voltar ao deck" })).toHaveAttribute(
      "href",
      "/decks/deck-1",
    );
  });

  test("lista cards usando os quatro novos campos", async () => {
    fetchCardsByDeck.mockResolvedValue({ count: 1, next: null, previous: null, results: [CARD] });
    renderPage();

    expect(await screen.findByRole("heading", { name: "network" })).toBeInTheDocument();
    expect(screen.getByText("rede")).toBeInTheDocument();
    expect(screen.getByText("The network is stable.")).toBeInTheDocument();
    expect(screen.getByText("A rede está estável.")).toBeInTheDocument();
  });

  test("renderiza o formulário antes da lista", async () => {
    fetchCardsByDeck.mockResolvedValue({ count: 1, next: null, previous: null, results: [CARD] });
    renderPage();

    const form = await screen.findByRole("form", { name: "Adicionar card" });
    const listHeading = screen.getByRole("heading", { name: "Lista" });

    expect(form.compareDocumentPosition(listHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("navega entre páginas de 10 cards", async () => {
    const user = userEvent.setup();
    const secondCard = { ...CARD, id: "card-11", front: "database" };
    fetchCardsByDeck.mockImplementation((_deckId, page = 1) => Promise.resolve(
      page === 2
        ? { count: 11, next: null, previous: "?page=1", results: [secondCard] }
        : { count: 11, next: "?page=2", previous: null, results: [CARD] },
    ));
    renderPage();

    expect(await screen.findByText("11 cards")).toBeInTheDocument();
    expect(screen.getByText("Página 1 de 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Próxima" }));

    expect(await screen.findByRole("heading", { name: "database" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "network" })).not.toBeInTheDocument();
    expect(fetchCardsByDeck).toHaveBeenLastCalledWith("deck-1", 2);
    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();
  });

  test("cria um card com os nomes novos e o associa ao deck", async () => {
    const user = userEvent.setup();
    const createdCard = { ...CARD, id: "card-2", front: "database" };
    fetchCardsByDeck
      .mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] })
      .mockResolvedValue({ count: 1, next: null, previous: null, results: [createdCard] });
    createCard.mockResolvedValue(createdCard);
    renderPage();

    await screen.findByRole("heading", { name: "Cards de Inglês técnico" });
    await user.type(screen.getByLabelText("Frente"), "database");
    await user.type(screen.getByLabelText("Verso"), "banco de dados");
    await user.type(screen.getByLabelText("Descrição da frente"), "The database is available.");
    await user.type(screen.getByLabelText("Descrição do verso"), "O banco de dados está disponível.");
    await user.type(screen.getByLabelText("Tags"), "backend, dados");
    await user.click(screen.getByRole("button", { name: "Adicionar card" }));

    await waitFor(() => {
      expect(createCard).toHaveBeenCalledWith({
        front: "database",
        back: "banco de dados",
        front_description: "The database is available.",
        back_description: "O banco de dados está disponível.",
        tags: ["backend", "dados"],
        deck_id: "deck-1",
      });
    });
    expect(await screen.findByRole("heading", { name: "database" })).toBeInTheDocument();
  });

  test("volta para a página anterior ao excluir o único card da última página", async () => {
    const user = userEvent.setup();
    const lastCard = { ...CARD, id: "card-11", front: "database" };
    let deleted = false;
    fetchCardsByDeck.mockImplementation((_deckId, page = 1) => {
      if (page === 2 && !deleted) {
        return Promise.resolve({ count: 11, next: null, previous: "?page=1", results: [lastCard] });
      }
      return Promise.resolve({ count: deleted ? 10 : 11, next: deleted ? null : "?page=2", previous: null, results: [CARD] });
    });
    deleteCard.mockImplementation(() => {
      deleted = true;
      return Promise.resolve(null);
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Próxima" }));
    await user.click(await screen.findByRole("button", { name: "Excluir card database" }));
    await user.click(within(screen.getByRole("dialog", { name: "Excluir card" })).getByRole(
      "button",
      { name: "Confirmar exclusão" },
    ));

    expect(await screen.findByText("Página 1 de 1")).toBeInTheDocument();
    expect(fetchCardsByDeck).toHaveBeenLastCalledWith("deck-1", 1);
  });

  test("edita e exclui um card inline", async () => {
    const user = userEvent.setup();
    fetchCardsByDeck
      .mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [CARD] })
      .mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
    updateCard.mockResolvedValue({ ...CARD, back: "rede de computadores" });
    deleteCard.mockResolvedValue(null);
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Editar card network" }));
    const editForm = screen.getByRole("form", { name: "Editar card network" });
    const back = within(editForm).getByLabelText("Verso");
    await user.clear(back);
    await user.type(back, "rede de computadores");
    await user.click(within(editForm).getByRole("button", { name: "Salvar card" }));

    await waitFor(() => {
      expect(updateCard).toHaveBeenCalledWith(
        "card-1",
        expect.objectContaining({ back: "rede de computadores" }),
      );
    });
    expect(await screen.findByText("rede de computadores")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Excluir card network" }));
    const dialog = screen.getByRole("dialog", { name: "Excluir card" });
    await user.click(within(dialog).getByRole("button", { name: "Confirmar exclusão" }));

    await waitFor(() => expect(deleteCard).toHaveBeenCalledWith("card-1"));
    expect(screen.queryByRole("heading", { name: "network" })).not.toBeInTheDocument();
    expect(screen.getByText("Este deck ainda não tem cards.")).toBeInTheDocument();
  });
});
