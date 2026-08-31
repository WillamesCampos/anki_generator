import { apiFetch } from "./client";

export function fetchCategories() {
  return apiFetch("/categories/");
}

export function createCategory(payload) {
  return apiFetch("/categories/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
