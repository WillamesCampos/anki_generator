# Home Statistics Chart Visual Enrichment Design

Date: 2026-09-14
Status: Approved from the existing “Contraste expressivo” direction

## Goal

Turn the Home statistics area into a clear, product-branded dashboard surface without changing review data, API calls, error/loading branches, or PDF export behavior.

## Visual direction

- Keep the chart inside the existing `Card`, but give only the Home statistics card a stronger black border and a restrained offset shadow.
- Add a small orange marker to the `Estatísticas` title so the section reads as part of the same orange/black system used by the study actions.
- Place the canvas on a light neutral inset surface with card-radius corners, padding, and a subtle border.
- Render orange bars with black outlines. On hover, invert the bar to black with an orange outline.
- Theme axes and tooltip with existing JS tokens: black text, subtle grid, Outfit typography, black tooltip, orange tooltip border.
- Keep labels horizontal, force the Y scale to begin at zero and use integer ticks.

## Accessible data summary

Below the canvas, show four compact values: `Errou`, `Difícil`, `Bom`, and `Fácil`. The list uses the exact values already passed to Chart.js and is linked to the canvas through `aria-describedby="home-rating-summary"`.

The summary is not a new data source and does not make additional requests. It gives users who cannot perceive the canvas or tooltip an equivalent textual reading.

## Motion and responsive behavior

- At widths up to `1024px`, keep the existing reduced chart height.
- At widths up to `640px`, reduce card/chart padding, set the chart to 240px, and arrange the value summary in two columns. Each summary cell stacks its label and value vertically so four-digit values remain legible and cannot overlap or force horizontal overflow at 320px.
- No fixed bar width is allowed; `maxBarThickness` may cap oversized bars without causing overlap.
- When `window.matchMedia("(prefers-reduced-motion: reduce)").matches` is true, pass `animation: false` to Chart.js. Normal Chart.js motion remains unchanged.

## Boundaries

- Do not change `fetchReviews`, `fetchDeckStatistics`, the distribution calculation, loading/error rendering, or `exportChartToPdf`.
- Keep `chartRef` attached to `Bar`.
- Do not register new Chart.js plugins or install dependencies.
- Do not modify `Card`, `Button`, global tokens, `DeckDetailPage`, the sidebar, or the recently approved Home CTA styles.
- Use only `colors`, `typography`, and `radius` from `tokens.js`, plus existing CSS custom properties.

## Verification

- Tests must prove the same values are used by the chart and the textual summary.
- Tests must inspect the important Chart.js styling/options and reduced-motion behavior.
- The canvas must keep its current accessible name and gain the summary description.
- Focused tests, full frontend tests, lint, build, diff check, and a responsive browser inspection are required.
