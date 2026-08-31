import { beforeEach, describe, expect, test, vi } from "vitest";

import { apiFetch } from "./client";
import { createDeck, deleteDeck, fetchDeckStatistics, updateDeck } from "./decks";
import { createCard, deleteCard, fetchCardCount, fetchCardsByDeck, updateCard } from "./cards";
import { createCategory, fetchCategories } from "./categories";

vi.mock("./client", () => ({
  apiFetch: vi.fn(),
}));

describe("clientes de gerenciamento", () => {
  beforeEach(() => {
    apiFetch.mockReset();
  });

  test("cria, atualiza e exclui decks nos endpoints versionados", async () => {
    const payload = { title: "Inglês", daily_review_goal: 20 };

    await createDeck(payload);
    await updateDeck("deck-1", payload);
    await deleteDeck("deck-1");
    await fetchDeckStatistics("deck-1");

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/decks/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    expect(apiFetch).toHaveBeenNthCalledWith(2, "/decks/deck-1/", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    expect(apiFetch).toHaveBeenNthCalledWith(3, "/decks/deck-1/", {
      method: "DELETE",
    });
    expect(apiFetch).toHaveBeenNthCalledWith(4, "/decks/deck-1/statistics/");
  });

  test("lista cards do deck e executa suas mutations", async () => {
    const payload = { front: "network", deck_id: "deck-1" };

    await fetchCardCount("deck-1");
    await fetchCardsByDeck("deck-1", 2);
    await createCard(payload);
    await updateCard("card-1", payload);
    await deleteCard("card-1");

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/cards/count/?deck_id=deck-1");
    expect(apiFetch).toHaveBeenNthCalledWith(2, "/cards/?deck_id=deck-1&page=2");
    expect(apiFetch).toHaveBeenNthCalledWith(3, "/cards/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    expect(apiFetch).toHaveBeenNthCalledWith(4, "/cards/card-1/", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    expect(apiFetch).toHaveBeenNthCalledWith(5, "/cards/card-1/", {
      method: "DELETE",
    });
  });

  test("lista e cria categorias", async () => {
    await fetchCategories();
    await createCategory({ name: "Idiomas" });

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/categories/");
    expect(apiFetch).toHaveBeenNthCalledWith(2, "/categories/", {
      method: "POST",
      body: JSON.stringify({ name: "Idiomas" }),
    });
  });
});
