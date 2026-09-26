"""PDF genérico (Sprint 11, D-PDF): `POST /document-generator/v1/documents/pdf`
recebe título + seções tipadas e devolve um PDF. Capacidade isolada, sem
consumidor Django nesta sprint (usada na Sprint 15, relatório semanal)."""

import io

import pytest
from pypdf import PdfReader

from tests.conftest import make_service_token

PDF_PATH = "/document-generator/v1/documents/pdf"

REPORT = {
    "title": "Relatório semanal de estudo",
    "subtitle": "14 a 20 de setembro de 2026",
    "sections": [
        {"type": "heading", "text": "Resumo da semana", "level": 1},
        {"type": "paragraph", "text": "Você revisou 214 cards em 5 dias de estudo."},
        {"type": "heading", "text": "Desempenho por deck", "level": 2},
        {
            "type": "table",
            "columns": ["Deck", "Revisões", "Acertos"],
            "rows": [
                ["Inglês — Phrasal verbs", "128", "81%"],
                ["Inglês — Vocabulário", "86", "73%"],
            ],
        },
        {
            "type": "bar_chart",
            "categories": ["Errei", "Difícil", "Bom", "Fácil"],
            "series": [{"name": "Revisões", "values": [47, 38, 92, 37]}],
        },
        {"type": "bullet_list", "items": ["Meta diária cumprida em 4 de 7 dias", "Deck mais estudado: Phrasal verbs"]},
    ],
}


def post(client, payload, token=None):
    token = token or make_service_token()
    return client.post(PDF_PATH, json=payload, headers={"Authorization": f"Bearer {token}"})


def pdf_text(response) -> str:
    reader = PdfReader(io.BytesIO(response.content))
    return "\n".join(page.extract_text() for page in reader.pages)


def page_count(response) -> int:
    return len(PdfReader(io.BytesIO(response.content)).pages)


# --- autenticação --------------------------------------------------------------


def test_request_without_a_service_token_is_rejected(client, tts_calls):
    response = client.post(PDF_PATH, json=REPORT)

    assert response.status_code == 401
    assert b"%PDF" not in response.content


def test_request_with_a_wrong_secret_is_rejected(client):
    assert post(client, REPORT, token=make_service_token(secret="wrong")).status_code == 401


def test_authenticated_request_returns_a_pdf(client):
    response = post(client, REPORT)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


# --- conteúdo -------------------------------------------------------------------


def test_every_section_type_reaches_the_document(client):
    text = pdf_text(post(client, REPORT))

    assert "Relatório semanal de estudo" in text
    assert "14 a 20 de setembro de 2026" in text
    assert "Resumo da semana" in text
    assert "Você revisou 214 cards em 5 dias de estudo." in text
    assert "Desempenho por deck" in text
    for cell in ["Deck", "Revisões", "Acertos", "Phrasal verbs", "128", "81%", "Vocabulário", "73%"]:
        assert cell in text, cell
    for category in ["Errei", "Difícil", "Bom", "Fácil"]:  # rótulos do gráfico
        assert category in text, category
    assert "Meta diária cumprida em 4 de 7 dias" in text
    assert "Deck mais estudado" in text


def test_text_with_markup_characters_is_shown_literally_not_interpreted(client):
    payload = {
        "title": "A & B <script>",
        "sections": [{"type": "paragraph", "text": "5 < 7 & <b>não é negrito</b>"}],
    }

    text = pdf_text(post(client, payload))

    assert "A & B <script>" in text
    assert "5 < 7 & <b>não é negrito</b>" in text


def test_minimal_document_with_only_a_title_is_valid(client):
    response = post(client, {"title": "Só título", "sections": []})

    assert response.status_code == 200
    assert "Só título" in pdf_text(response)


def test_long_content_flows_onto_more_than_one_page(client):
    payload = {
        "title": "Longo",
        "sections": [{"type": "paragraph", "text": "linha de conteúdo " * 40} for _ in range(40)],
    }

    assert page_count(post(client, payload)) >= 2


def test_a_large_table_paginates_instead_of_failing(client):
    payload = {
        "title": "Tabela grande",
        "sections": [
            {
                "type": "table",
                "columns": ["N", "Valor"],
                "rows": [[str(i), f"valor {i}"] for i in range(150)],
            }
        ],
    }

    response = post(client, payload)

    assert response.status_code == 200
    assert page_count(response) >= 2
    assert "valor 149" in pdf_text(response)


def test_bar_chart_with_several_series_renders(client):
    payload = {
        "title": "Comparativo",
        "sections": [
            {
                "type": "bar_chart",
                "title": "Semana atual x anterior",
                "categories": ["Seg", "Ter", "Qua"],
                "series": [
                    {"name": "Atual", "values": [10, 20, 15]},
                    {"name": "Anterior", "values": [8, 12, 30]},
                ],
            }
        ],
    }

    text = pdf_text(post(client, payload))

    assert "Semana atual x anterior" in text
    for label in ["Seg", "Ter", "Qua", "Atual", "Anterior"]:
        assert label in text, label


# --- validação do contrato ------------------------------------------------------


@pytest.mark.parametrize(
    "bad_section",
    [
        {"type": "video", "url": "http://x"},  # tipo desconhecido
        {"type": "paragraph"},  # sem texto
        {"type": "table", "columns": ["A", "B"], "rows": [["só uma célula"]]},  # linha curta
        {"type": "table", "columns": [], "rows": []},  # sem colunas
        {"type": "bar_chart", "categories": ["a", "b"], "series": [{"name": "s", "values": [1]}]},  # valores != categorias
        {"type": "bar_chart", "categories": [], "series": []},
        {"type": "bullet_list", "items": []},
        {"type": "heading", "text": "x", "level": 9},
    ],
)
def test_invalid_sections_are_rejected_with_422(client, bad_section):
    response = post(client, {"title": "T", "sections": [bad_section]})

    assert response.status_code == 422


def test_document_without_a_title_is_rejected(client):
    assert post(client, {"sections": []}).status_code == 422


def test_too_many_sections_are_rejected(client):
    payload = {"title": "T", "sections": [{"type": "paragraph", "text": "x"}] * 501}

    assert post(client, payload).status_code == 422


def test_oversized_table_is_rejected(client):
    payload = {
        "title": "T",
        "sections": [{"type": "table", "columns": ["A"], "rows": [["x"]] * 2001}],
    }

    assert post(client, payload).status_code == 422
