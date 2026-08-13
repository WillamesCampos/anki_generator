import { apiFetch } from "./client";

export function fetchCard(cardId) {
  return apiFetch(`/cards/${cardId}/`);
}

export function fetchDueCards() {
  return apiFetch("/cards/?due=true");
}
