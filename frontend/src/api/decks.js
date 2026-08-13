import { apiFetch } from "./client";

export function fetchDecks() {
  return apiFetch("/decks/");
}

export function fetchDeck(deckId) {
  return apiFetch(`/decks/${deckId}/`);
}
