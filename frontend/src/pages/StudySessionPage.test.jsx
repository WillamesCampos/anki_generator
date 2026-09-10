import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { fetchDueCards } from "../api/cards";
import { fetchDeck } from "../api/decks";
import { createReview } from "../api/reviews";
import StudySessionPage from "./StudySessionPage";

vi.mock("../api/cards", () => ({
  fetchDueCards: vi.fn(),
}));

vi.mock("../api/decks", () => ({
  fetchDeck: vi.fn(),
}));

vi.mock("../api/reviews", () => ({
  createReview: vi.fn(),
}));

const DECK = { id: "deck-1", title: "Inglês técnico" };

function buildCard(overrides) {
  return {
    id: "card-1",
    front: "network",
    back: "rede",
    front_description: "The network is stable.",
    back_description: "A rede está estável.",
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/decks/deck-1/estudar"]}>
      <Routes>
        <Route path="/decks/:deckId/estudar" element={<StudySessionPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("sessão de estudo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchDeck.mockResolvedValue(DECK);
  });

  test("estado vazio quando o deck não tem cards devidos", async () => {
    fetchDueCards.mockResolvedValue({ results: [] });
    renderPage();

    expect(await screen.findByText("Nenhum card devido agora neste deck.")).toBeInTheDocument();
  });

  test("fluxo completo: revela resposta, avalia e avança pro próximo card", async () => {
    const user = userEvent.setup();
    const cardOne = buildCard({ id: "card-1", front: "network" });
    const cardTwo = buildCard({ id: "card-2", front: "database", back: "banco de dados" });
    fetchDueCards.mockResolvedValue({ results: [cardOne, cardTwo] });
    createReview.mockResolvedValue({});

    renderPage();

    expect(await screen.findByRole("heading", { name: "network" })).toBeInTheDocument();
    expect(screen.getByText("Card 1 de 2")).toBeInTheDocument();
    expect(screen.queryByText("rede")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Mostrar resposta" }));

    expect(screen.getByText("rede")).toBeInTheDocument();
    expect(screen.getByText("The network is stable.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Bom" }));

    await waitFor(() => {
      expect(createReview).toHaveBeenCalledWith("card-1", "good");
    });

    expect(await screen.findByRole("heading", { name: "database" })).toBeInTheDocument();
    expect(screen.getByText("Card 2 de 2")).toBeInTheDocument();
    expect(screen.queryByText("banco de dados")).not.toBeInTheDocument();
  });

  test("avaliar o último card mostra a tela de fim de sessão", async () => {
    const user = userEvent.setup();
    fetchDueCards.mockResolvedValue({ results: [buildCard()] });
    createReview.mockResolvedValue({});

    renderPage();

    await screen.findByRole("heading", { name: "network" });
    await user.click(screen.getByRole("button", { name: "Mostrar resposta" }));
    await user.click(screen.getByRole("button", { name: "Fácil" }));

    expect(await screen.findByRole("heading", { name: "Sessão concluída" })).toBeInTheDocument();
    expect(screen.getByText("Você revisou 1 card neste deck.")).toBeInTheDocument();

    const backLinks = screen.getAllByRole("link", { name: "Voltar ao deck" });
    expect(backLinks).toHaveLength(2);
    backLinks.forEach((link) => expect(link).toHaveAttribute("href", "/decks/deck-1"));
  });
});
