from app.generator import CARD_MODEL_FIELDS, CARD_MODEL_TEMPLATE


def test_anki_model_uses_english_field_names_with_portuguese_labels():
    assert [field["name"] for field in CARD_MODEL_FIELDS] == [
        "Front",
        "Back",
        "FrontDescription",
        "BackDescription",
        "Notes",
        "Audio",
    ]

    template = CARD_MODEL_TEMPLATE[0]
    assert template["qfmt"] == "{{Front}}<br>{{Audio}}"
    assert "{{Back}}" in template["afmt"]
    assert "{{FrontDescription}}" in template["afmt"]
    assert "{{BackDescription}}" in template["afmt"]
    assert "<b>Verso:</b>" in template["afmt"]
    assert "<b>Descrição da frente:</b>" in template["afmt"]
    assert "<b>Descrição do verso:</b>" in template["afmt"]
