import { useState } from "react";

import Button from "../ui/Button";
import Input from "../ui/Input";
import "./CardForm.css";

function errorMessage(error) {
  return error?.status === 403 ? error.message : "Não foi possível salvar o card.";
}

function parseTags(value) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export default function CardForm({
  deckId,
  initialCard = null,
  onSubmit,
  onCancel,
  submitLabel,
  ariaLabel,
}) {
  const [form, setForm] = useState({
    front: initialCard?.front ?? "",
    back: initialCard?.back ?? "",
    front_description: initialCard?.front_description ?? "",
    back_description: initialCard?.back_description ?? "",
    tags: initialCard?.tags?.join(", ") ?? "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await onSubmit({
        front: form.front.trim(),
        back: form.back.trim(),
        front_description: form.front_description.trim(),
        back_description: form.back_description.trim(),
        tags: parseTags(form.tags),
        deck_id: deckId,
      });

      if (!initialCard) {
        setForm({
          front: "",
          back: "",
          front_description: "",
          back_description: "",
          tags: "",
        });
      }
    } catch (submitError) {
      setError(errorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card-form" onSubmit={handleSubmit} aria-label={ariaLabel}>
      <div className="card-form__grid">
        <Input
          label="Frente"
          name="front"
          value={form.front}
          onChange={updateField}
          maxLength={200}
          required
        />
        <Input
          label="Verso"
          name="back"
          value={form.back}
          onChange={updateField}
          maxLength={200}
          required
        />
      </div>
      <Input
        as="textarea"
        label="Descrição da frente"
        name="front_description"
        value={form.front_description}
        onChange={updateField}
        required
      />
      <Input
        as="textarea"
        label="Descrição do verso"
        name="back_description"
        value={form.back_description}
        onChange={updateField}
        required
      />
      <Input
        label="Tags"
        name="tags"
        value={form.tags}
        onChange={updateField}
        placeholder="backend, inglês, trabalho"
      />

      {error && <p className="card-form__error" role="alert">{error}</p>}

      <div className="card-form__actions">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel} disabled={submitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" disabled={submitting}>
          {submitting ? "Salvando…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
