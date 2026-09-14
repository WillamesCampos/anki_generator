import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { fetchDeck, fetchDeckStatistics } from "../api/decks";
import { fetchReviews } from "../api/reviews";
import HomePage from "./HomePage";

vi.mock("../api/decks", () => ({
  fetchDeck: vi.fn(),
  fetchDeckStatistics: vi.fn(),
}));

vi.mock("../api/reviews", () => ({
  fetchReviews: vi.fn(),
}));

vi.mock("react-chartjs-2", () => ({
  Bar: ({ data }) => (
    <div
      role="img"
      aria-label="Distribuição das classificações da Home"
      data-values={data.datasets[0].data.join(",")}
    />
  ),
}));

const LAST_DECK = {
  id: "deck-last",
  title: "Hospedagem e Transporte",
  description: "Vocabulário de viagem",
};

function renderHome() {
  return render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );
}

describe("estatísticas da Home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchReviews.mockResolvedValue({
      results: [
        { id: "review-1", deck_id: "deck-last", rating: "again", reviewed_at: "2026-08-31T12:00:00Z" },
        { id: "review-2", deck_id: "deck-other", rating: "easy", reviewed_at: "2026-08-31T11:00:00Z" },
      ],
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({
      rating_distribution: { again: 3, hard: 4, good: 3, easy: 2 },
    });
  });

  test("usa o histórico completo do último deck em vez de somar revisões de outros decks", async () => {
    renderHome();

    expect(await screen.findByText("Hospedagem e Transporte")).toBeInTheDocument();
    const chart = await screen.findByRole("img", {
      name: "Distribuição das classificações da Home",
    });

    expect(fetchDeckStatistics).toHaveBeenCalledWith("deck-last");
    expect(chart).toHaveAttribute("data-values", "3,4,3,2");
  });

  test("mantém o card do último deck quando a consulta de estatísticas falha", async () => {
    fetchDeckStatistics.mockRejectedValue(new Error("offline"));

    renderHome();

    expect(await screen.findByText("Hospedagem e Transporte")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar as estatísticas do último deck.",
    );
  });

  test("não consulta estatísticas de deck quando ainda não há revisões", async () => {
    fetchReviews.mockResolvedValue({ results: [] });

    renderHome();

    expect(await screen.findByText("Você ainda não revisou nenhum card.")).toBeInTheDocument();
    await waitFor(() => expect(fetchDeckStatistics).not.toHaveBeenCalled());
  });
});

describe("caminhos até a tela de estudo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("com último deck válido: botão 'Continuar estudando' aponta pro deck, e o CTA convida a trocar de deck", async () => {
    fetchReviews.mockResolvedValue({
      results: [
        { id: "review-1", deck_id: "deck-last", rating: "again", reviewed_at: "2026-08-31T12:00:00Z" },
      ],
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    await screen.findByText("Hospedagem e Transporte");

    const continueLink = screen.getByRole("link", { name: "Continuar estudando" });
    expect(continueLink).toHaveAttribute(
      "href",
      "/decks/deck-last/estudar",
    );
    expect(continueLink).toHaveClass("ui-button", "ui-button--primary");
    expect(continueLink).toHaveAttribute("data-home-action", "continue");

    expect(
      screen.getByText("Não é o deck que deseja estudar agora? Escolha o seu deck!"),
    ).toBeInTheDocument();
    const decksLink = screen.getByRole("link", { name: "Ver meus decks" });
    expect(decksLink).toHaveAttribute("href", "/decks");
    expect(decksLink).toHaveClass("ui-button", "ui-button--secondary");
    expect(decksLink).toHaveAttribute("data-home-action", "decks");
  });

  test("sem nenhuma revisão: sem botão 'Continuar estudando', CTA convida a escolher um deck", async () => {
    fetchReviews.mockResolvedValue({ results: [] });

    renderHome();

    await screen.findByText("Você ainda não revisou nenhum card.");

    expect(screen.queryByRole("link", { name: "Continuar estudando" })).not.toBeInTheDocument();
    expect(screen.getByText("Escolha um deck pra começar a estudar!")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver meus decks" })).toHaveAttribute("href", "/decks");
  });

  test("deck da revisão mais recente não está mais acessível: sem botão 'Continuar estudando', CTA neutro", async () => {
    fetchReviews.mockResolvedValue({
      results: [
        { id: "review-1", deck_id: "deck-deleted", rating: "again", reviewed_at: "2026-08-31T12:00:00Z" },
      ],
    });
    fetchDeck.mockRejectedValue({ status: 404, message: "Not found" });

    renderHome();

    await waitFor(() => expect(fetchDeck).toHaveBeenCalledWith("deck-deleted"));
    await waitFor(() =>
      expect(screen.queryByRole("link", { name: "Continuar estudando" })).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Escolha um deck pra começar a estudar!")).toBeInTheDocument();
  });
});
