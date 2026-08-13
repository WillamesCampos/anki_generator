// Meta de estudo (tarefa 3.2) — não existe nenhum conceito de "meta" no
// backend hoje (nenhum model/endpoint guarda isso). Em vez de inventar
// schema novo de backend sem um requisito de produto definido (o que
// seria escopo especulativo, diferente do endpoint de reviews — que só
// expunha um dado histórico que já existia), a meta é uma preferência
// local por enquanto: guardada em localStorage, número de cards
// revisados por dia. Documentado como decisão explícita, não escondido.

const GOAL_KEY = "anki_generator_daily_goal";
const DEFAULT_GOAL = 20;

export function getDailyGoal() {
  const stored = localStorage.getItem(GOAL_KEY);
  return stored ? Number(stored) : DEFAULT_GOAL;
}

export function setDailyGoal(value) {
  localStorage.setItem(GOAL_KEY, String(value));
}

export function computeGoalProgress(reviews, goal) {
  const today = new Date().toDateString();
  const reviewedToday = reviews.filter((review) => new Date(review.reviewed_at).toDateString() === today).length;

  return {
    reviewedToday,
    goal,
    percentage: goal > 0 ? Math.min(100, Math.round((reviewedToday / goal) * 100)) : 0,
  };
}
