import { useEffect, useState } from "react";

import { createCategory, fetchCategories } from "../../api/categories";
import Button from "../ui/Button";
import Input from "../ui/Input";
import "./DeckForm.css";

const NEW_CATEGORY_VALUE = "__new__";

function collectionItems(response) {
  return response?.results ?? response ?? [];
}

function errorMessage(error, fallback) {
  return error?.status === 403 ? error.message : fallback;
}

export default function DeckForm({ initialDeck = null, onSubmit, submitLabel }) {
  const [form, setForm] = useState({
    title: initialDeck?.title ?? "",
    description: initialDeck?.description ?? "",
    category_id: initialDeck?.category_id ?? "",
    daily_review_goal: initialDeck?.daily_review_goal ?? "",
  });
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoryError, setCategoryError] = useState("");
  const [newCategoryName, setNewCategoryName] = useState("");
  const [creatingCategory, setCreatingCategory] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetchCategories()
      .then((response) => {
        if (!cancelled) setCategories(collectionItems(response));
      })
      .catch((error) => {
        if (!cancelled) {
          setCategoryError(errorMessage(error, "Não foi possível carregar as categorias."));
        }
      })
      .finally(() => {
        if (!cancelled) setCategoriesLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleCreateCategory() {
    const name = newCategoryName.trim();
    if (!name) return;

    setCreatingCategory(true);
    setCategoryError("");
    try {
      const category = await createCategory({ name });
      setCategories((current) => [...current, category]);
      setForm((current) => ({ ...current, category_id: category.id }));
      setNewCategoryName("");
    } catch (error) {
      setCategoryError(errorMessage(error, "Não foi possível criar a categoria."));
    } finally {
      setCreatingCategory(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError("");

    const categoryId = form.category_id && form.category_id !== NEW_CATEGORY_VALUE
      ? form.category_id
      : null;
    const dailyGoal = form.daily_review_goal === "" ? null : Number(form.daily_review_goal);

    try {
      await onSubmit({
        title: form.title.trim(),
        description: form.description.trim(),
        category_id: categoryId,
        daily_review_goal: dailyGoal,
      });
    } catch (error) {
      setSubmitError(errorMessage(error, "Não foi possível salvar o deck."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="deck-form" onSubmit={handleSubmit}>
      <Input
        label="Título"
        name="title"
        value={form.title}
        onChange={updateField}
        maxLength={200}
        required
      />
      <Input
        as="textarea"
        label="Descrição"
        name="description"
        value={form.description}
        onChange={updateField}
      />

      <label className="ui-input">
        <span className="ui-input__label">Categoria</span>
        <select
          className="ui-input__field"
          name="category_id"
          value={form.category_id}
          onChange={updateField}
          disabled={categoriesLoading}
        >
          <option value="">Sem categoria</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
          <option value={NEW_CATEGORY_VALUE}>+ Nova categoria</option>
        </select>
      </label>

      {form.category_id === NEW_CATEGORY_VALUE && (
        <div className="deck-form__new-category">
          <Input
            label="Nome da nova categoria"
            value={newCategoryName}
            onChange={(event) => setNewCategoryName(event.target.value)}
            maxLength={200}
            required
          />
          <Button
            variant="secondary"
            onClick={handleCreateCategory}
            disabled={creatingCategory || !newCategoryName.trim()}
          >
            {creatingCategory ? "Criando…" : "Criar categoria"}
          </Button>
        </div>
      )}

      {categoryError && <p className="deck-form__error" role="alert">{categoryError}</p>}

      <Input
        label="Meta diária de revisões"
        name="daily_review_goal"
        type="number"
        min="1"
        value={form.daily_review_goal}
        onChange={updateField}
      />

      {submitError && <p className="deck-form__error" role="alert">{submitError}</p>}

      <div className="deck-form__actions">
        <Button
          type="submit"
          disabled={submitting || form.category_id === NEW_CATEGORY_VALUE}
        >
          {submitting ? "Salvando…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
