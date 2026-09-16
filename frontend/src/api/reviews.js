import { apiFetch } from "./client";

export function fetchReviews() {
  return apiFetch("/reviews/");
}

export function createReview(cardId, rating) {
  return apiFetch(`/cards/${cardId}/review/`, {
    method: "POST",
    body: JSON.stringify({ rating }),
  });
}
