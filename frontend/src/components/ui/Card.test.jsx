import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "vitest";

import Card from "./Card";

const cardStyles = readFileSync(resolve("src/components/ui/Card.css"), "utf8");

test("renderiza título e conteúdo com os hooks globais", () => {
  render(<Card title="Resumo">Conteúdo</Card>);

  expect(screen.getByRole("heading", { name: "Resumo" })).toHaveClass("ui-card__title");
  expect(screen.getByText("Conteúdo")).toHaveClass("ui-card__body");
});

test("define a superfície, o título e o padding móvel no CSS global", () => {
  expect(cardStyles).toContain("border: 2px solid var(--color-text-primary);");
  expect(cardStyles).toContain("box-shadow: 4px 4px 0 var(--color-text-primary);");
  expect(cardStyles).toContain("font-size: var(--font-size-lg);");
  expect(cardStyles).toContain("font-weight: 700;");
  expect(cardStyles).toContain(".ui-card__title::before");
  expect(cardStyles).toContain("background: var(--color-accent);");
  expect(cardStyles).toContain("@media (max-width: 640px)");
  expect(cardStyles).toContain("padding: var(--space-sm);");
});
