import { Link, useNavigate } from "react-router-dom";

import { createDeck } from "../api/decks";
import DeckForm from "../components/decks/DeckForm";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import "./DeckManagement.css";

export default function NewDeckPage() {
  const navigate = useNavigate();

  async function handleCreate(payload) {
    const deck = await createDeck(payload);
    navigate(`/decks/${deck.id}`);
  }

  return (
    <section className="deck-page deck-page--form">
      <header className="deck-page__header">
        <div>
          <p className="deck-page__eyebrow">Novo deck</p>
          <h1 className="deck-page__title">Organize seu próximo estudo</h1>
        </div>
        <Button as={Link} variant="secondary" to="/decks">Voltar</Button>
      </header>

      <Card title="Dados do deck">
        <DeckForm submitLabel="Criar deck" onSubmit={handleCreate} />
      </Card>
    </section>
  );
}
