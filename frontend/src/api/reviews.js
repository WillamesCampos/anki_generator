import { apiFetch } from "./client";

export function fetchReviews() {
  return apiFetch("/reviews/");
}
