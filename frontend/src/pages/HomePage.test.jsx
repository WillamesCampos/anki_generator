import { render, screen, waitFor } from "@testing-library/react";
import { forwardRef } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { fetchDeck, fetchDeckStatistics } from "../api/decks";
import { fetchReviews } from "../api/reviews";
import { colors, radius } from "../tokens/tokens";
import HomePage from "./HomePage";

vi.mock("../api/decks", () => ({
  fetchDeck: vi.fn(),
  fetchDeckStatistics: vi.fn(),
}));

vi.mock("../api/reviews", () => ({
  fetchReviews: vi.fn(),
}));

vi.mock("react-chartjs-2", () => ({
  Bar: forwardRef(function Bar({ data, options, ...chartProps }, ref) {
    return (
    <div
      {...chartProps}
      ref={ref}
      role="img"
      data-values={data.datasets[0].data.join(",")}
      data-border-color={data.datasets[0].borderColor}
      data-hover-background={data.datasets[0].hoverBackgroundColor}
      data-border-radius={data.datasets[0].borderRadius}
      data-x-grid={String(options.scales.x.grid.display)}
      data-y-begin-at-zero={String(options.scales.y.beginAtZero)}
      data-tooltip-background={options.plugins.tooltip.backgroundColor}
      data-animation={options.animation === false ? "disabled" : "default"}
    />
    );
  }),
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
  afterEach(() => {
    vi.unstubAllGlobals();
  });

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
    expect(chart).toHaveAttribute("aria-describedby", "home-rating-summary");
    expect(chart).toHaveAttribute("data-border-color", colors.textPrimary);
    expect(chart).toHaveAttribute("data-hover-background", colors.bgDark);
    expect(chart).toHaveAttribute("data-border-radius", String(Number.parseFloat(radius.card)));
    expect(chart).toHaveAttribute("data-x-grid", "false");
    expect(chart).toHaveAttribute("data-y-begin-at-zero", "true");
    expect(chart).toHaveAttribute("data-tooltip-background", colors.bgDark);

    const summary = screen.getByRole("list", { name: "Resumo das classificações" });
    expect(summary).toHaveAttribute("id", "home-rating-summary");
    expect(summary).toHaveTextContent("Errou3");
    expect(summary).toHaveTextContent("Difícil4");
    expect(summary).toHaveTextContent("Bom3");
    expect(summary).toHaveTextContent("Fácil2");
  });

  test("desativa a animação do gráfico quando o usuário prefere movimento reduzido", async () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));

    renderHome();

    const chart = await screen.findByRole("img", {
      name: "Distribuição das classificações da Home",
    });
    expect(chart).toHaveAttribute("data-animation", "disabled");
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

    const ctaCopy = screen.getByText("Não é o deck que deseja estudar agora? Escolha o seu deck!");
    expect(ctaCopy).toBeInTheDocument();
    expect(ctaCopy).toHaveClass("home-page__study-cta-copy");
    const decksLink = screen.getByRole("link", { name: "Ver meus decks" });
    expect(decksLink).toHaveAttribute("href", "/decks");
    expect(decksLink).toHaveClass("ui-button", "ui-button--secondary");
    expect(decksLink).toHaveAttribute("data-home-action", "decks");
    const eyeIcon = decksLink.querySelector(".home-page__decks-eye-icon");
    expect(eyeIcon).toHaveAttribute("aria-hidden", "true");
    expect(eyeIcon).toHaveAttribute("focusable", "false");
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

describe("meta de estudo da Home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchReviews.mockResolvedValue({ results: [] });
  });

  test("mostra a meta inicial como progresso acessível", async () => {
    renderHome();
    await screen.findByText("Você ainda não revisou nenhum card.");

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    expect(progress).toHaveAttribute("aria-valuemin", "0");
    expect(progress).toHaveAttribute("aria-valuemax", "100");
    expect(progress).toHaveAttribute("aria-valuenow", "0");
    expect(progress).toHaveAttribute("aria-valuetext", "0 de 20 cards revisados hoje");
    expect(screen.getByText("20 cards para concluir sua meta")).toBeInTheDocument();
    expect(screen.getByText("0%", { selector: ".home-page__goal-percent" })).toBeInTheDocument();
  });

  test("calcula o progresso parcial com as revisões de hoje", async () => {
    const today = new Date().toISOString();
    fetchReviews.mockResolvedValue({
      results: Array.from({ length: 5 }, (_, index) => ({
        id: `review-${index}`,
        deck_id: "deck-last",
        rating: "good",
        reviewed_at: today,
      })),
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    await waitFor(() => expect(progress).toHaveAttribute("aria-valuenow", "25"));
    expect(progress).toHaveAttribute("aria-valuetext", "5 de 20 cards revisados hoje");
    expect(screen.getByText("15 cards para concluir sua meta")).toBeInTheDocument();
  });

  test("mostra a conclusão quando a meta diária é atingida", async () => {
    const today = new Date().toISOString();
    fetchReviews.mockResolvedValue({
      results: Array.from({ length: 20 }, (_, index) => ({
        id: `review-${index}`,
        deck_id: "deck-last",
        rating: "easy",
        reviewed_at: today,
      })),
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    await waitFor(() => expect(progress).toHaveAttribute("aria-valuenow", "100"));
    expect(screen.getByText("Meta concluída hoje!")).toBeInTheDocument();
  });
});
