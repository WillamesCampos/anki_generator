import { Link } from "react-router-dom";

import { fetchDecks } from "../api/decks";
import { useApiResource } from "../api/hooks";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import "./DeckManagement.css";

function collectionItems(response) {
  return response?.results ?? response ?? [];
}

export default function DeckListPage() {
  const { data, error, loading } = useApiResource(fetchDecks, []);
  const decks = collectionItems(data);

  return (
    <section className="deck-page">
      <header className="deck-page__header">
        <div>
          <p className="deck-page__eyebrow">Gerenciamento</p>
          <h1 className="deck-page__title">Seus decks</h1>
        </div>
        <Button as={Link} to="/decks/novo">Novo deck</Button>
      </header>

      {loading && <p>Carregando decks…</p>}
      {!loading && error && (
        <p role="alert">
          {error.status === 403 ? error.message : "Não foi possível carregar seus decks."}
        </p>
      )}

      {!loading && !error && decks.length === 0 && (
        <Card title="Nenhum deck por aqui">
          <p className="deck-page__empty-text">Você ainda não criou nenhum deck.</p>
          <Button as={Link} to="/decks/novo">Criar primeiro deck</Button>
        </Card>
      )}

      {!loading && !error && decks.length > 0 && (
        <div className="deck-page__grid">
          {decks.map((deck) => (
            <Card key={deck.id} title={deck.title}>
              <p className="deck-page__description">
                {deck.description || "Deck sem descrição."}
              </p>
              <Button
                as={Link}
                variant="secondary"
                to={`/decks/${deck.id}`}
                aria-label={`Abrir deck ${deck.title}`}
              >
                Abrir deck
              </Button>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
