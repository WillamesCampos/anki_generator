const RATING_LABELS = { again: "Errou", hard: "Difícil", good: "Bom", easy: "Fácil" };
const RATING_ORDER = ["again", "hard", "good", "easy"];

export function computeRatingDistribution(reviews) {
  const counts = { again: 0, hard: 0, good: 0, easy: 0 };
  for (const review of reviews) {
    if (review.rating in counts) counts[review.rating] += 1;
  }

  return {
    labels: RATING_ORDER.map((rating) => RATING_LABELS[rating]),
    values: RATING_ORDER.map((rating) => counts[rating]),
  };
}

export function mostRecentReview(reviews) {
  return reviews.length > 0 ? reviews[0] : null;
}
