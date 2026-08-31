import { apiFetch } from "./client";

export function fetchDecks() {
  return apiFetch("/decks/");
}

export function fetchDeck(deckId) {
  return apiFetch(`/decks/${deckId}/`);
}

export function fetchDeckStatistics(deckId) {
  return apiFetch(`/decks/${deckId}/statistics/`);
}

export function createDeck(payload) {
  return apiFetch("/decks/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateDeck(deckId, payload) {
  return apiFetch(`/decks/${deckId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteDeck(deckId) {
  return apiFetch(`/decks/${deckId}/`, {
    method: "DELETE",
  });
}
