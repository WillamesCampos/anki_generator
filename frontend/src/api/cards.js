import { apiFetch } from "./client";

export function fetchCard(cardId) {
  return apiFetch(`/cards/${cardId}/`);
}

export function fetchDueCards() {
  return apiFetch("/cards/?due=true");
}

export function fetchCardsByDeck(deckId, page = 1) {
  return apiFetch(`/cards/?deck_id=${deckId}&page=${page}`);
}

export function fetchCardCount(deckId) {
  return apiFetch(`/cards/count/?deck_id=${deckId}`);
}

export function createCard(payload) {
  return apiFetch("/cards/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCard(cardId, payload) {
  return apiFetch(`/cards/${cardId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteCard(cardId) {
  return apiFetch(`/cards/${cardId}/`, {
    method: "DELETE",
  });
}
