import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { fetchCardCount } from "../api/cards";
import { fetchCategories } from "../api/categories";
import { deleteDeck, fetchDeck, fetchDeckStatistics, fetchDecks, updateDeck } from "../api/decks";
import DeckDetailPage from "./DeckDetailPage";
import DeckListPage from "./DeckListPage";

vi.mock("../api/cards", () => ({
  fetchCardCount: vi.fn(),
}));

vi.mock("../api/categories", () => ({
  createCategory: vi.fn(),
  fetchCategories: vi.fn(),
}));

vi.mock("../api/decks", () => ({
  deleteDeck: vi.fn(),
  fetchDeck: vi.fn(),
  fetchDeckStatistics: vi.fn(),
  fetchDecks: vi.fn(),
  updateDeck: vi.fn(),
}));

vi.mock("react-chartjs-2", () => ({
  Bar: ({ data }) => (
    <div
      role="img"
      aria-label="Distribuição das classificações do deck"
      data-values={data.datasets[0].data.join(",")}
    />
  ),
}));

const DECK = {
  id: "deck-1",
  title: "Inglês técnico",
  description: "Vocabulário de backend",
  category_id: null,
  daily_review_goal: 15,
};

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={["/decks/deck-1"]}>
      <Routes>
        <Route path="/decks/:deckId" element={<DeckDetailPage />} />
        <Route path="/decks" element={<DeckListPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("detalhe do deck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchDeck.mockResolvedValue(DECK);
    fetchDecks.mockResolvedValue({ results: [] });
    fetchCardCount.mockResolvedValue({ count: 0 });
    fetchDeckStatistics.mockResolvedValue({
      rating_distribution: { again: 0, hard: 0, good: 0, easy: 0 },
      reviewed_today: 0,
      daily_review_goal: 15,
      goal_progress_percentage: 0,
    });
    fetchCategories.mockResolvedValue({ results: [] });
  });

  test("mostra os dados e somente a contagem de cards no detalhe", async () => {
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Inglês técnico" })).toBeInTheDocument();
    expect(screen.getByText("Vocabulário de backend")).toBeInTheDocument();
    expect(await screen.findByText("0 cards")).toBeInTheDocument();
    expect(fetchCardCount).toHaveBeenCalledWith("deck-1");
    expect(screen.queryByRole("form", { name: "Adicionar card" })).not.toBeInTheDocument();
  });

  test("usa singular e oferece navegação para todos os cards", async () => {
    fetchCardCount.mockResolvedValue({ count: 1 });
    renderDetail();

    expect(await screen.findByText("1 card")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver todos os cards" })).toHaveAttribute(
      "href",
      "/decks/deck-1/cards",
    );
  });

  test("mostra erro próprio quando a contagem falha", async () => {
    fetchCardCount.mockRejectedValue(new Error("offline"));
    renderDetail();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar a quantidade de cards.",
    );
  });

  test("mostra a distribuição histórica das quatro classificações do deck", async () => {
    fetchDeckStatistics.mockResolvedValue({
      rating_distribution: { again: 2, hard: 3, good: 5, easy: 7 },
      reviewed_today: 1,
      daily_review_goal: 15,
      goal_progress_percentage: 7,
    });
    renderDetail();

    const chart = await screen.findByRole("img", { name: "Distribuição das classificações do deck" });
    expect(chart).toHaveAttribute("data-values", "2,3,5,7");
    expect(screen.getByText("Errou: 2")).toBeInTheDocument();
    expect(screen.getByText("Difícil: 3")).toBeInTheDocument();
    expect(screen.getByText("Bom: 5")).toBeInTheDocument();
    expect(screen.getByText("Fácil: 7")).toBeInTheDocument();
    expect(fetchDeckStatistics).toHaveBeenCalledWith("deck-1");
  });

  test("mantém o detalhe utilizável quando as estatísticas falham", async () => {
    fetchDeckStatistics.mockRejectedValue(new Error("offline"));
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Inglês técnico" })).toBeInTheDocument();
    expect(await screen.findByText("Não foi possível carregar as estatísticas do deck.")).toHaveAttribute(
      "role",
      "alert",
    );
    expect(screen.getByRole("link", { name: "Ver todos os cards" })).toBeInTheDocument();
  });

  test("edita o deck inline e reflete os dados persistidos", async () => {
    const user = userEvent.setup();
    updateDeck.mockResolvedValue({ ...DECK, title: "Inglês para APIs", daily_review_goal: 25 });
    renderDetail();

    await user.click(await screen.findByRole("button", { name: "Editar deck" }));
    const title = screen.getByLabelText("Título");
    await user.clear(title);
    await user.type(title, "Inglês para APIs");
    const goal = screen.getByLabelText("Meta diária de revisões");
    await user.clear(goal);
    await user.type(goal, "25");
    await user.click(screen.getByRole("button", { name: "Salvar alterações" }));

    await waitFor(() => {
      expect(updateDeck).toHaveBeenCalledWith(
        "deck-1",
        expect.objectContaining({ title: "Inglês para APIs", daily_review_goal: 25 }),
      );
    });
    expect(await screen.findByRole("heading", { name: "Inglês para APIs" })).toBeInTheDocument();
  });

  test("confirma a exclusão do deck, avisa sobre retenção e volta à lista", async () => {
    const user = userEvent.setup();
    deleteDeck.mockResolvedValue(null);
    renderDetail();

    await user.click(await screen.findByRole("button", { name: "Excluir deck" }));
    const dialog = screen.getByRole("dialog", { name: "Excluir deck" });
    expect(dialog).toHaveTextContent("7 dias");
    await user.click(within(dialog).getByRole("button", { name: "Confirmar exclusão" }));

    await waitFor(() => expect(deleteDeck).toHaveBeenCalledWith("deck-1"));
    expect(await screen.findByText("Você ainda não criou nenhum deck.")).toBeInTheDocument();
  });

});
