"""
Verificação do JWT de serviço (Sprint 5, `autenticacao-service-to-service-jwt`).
Ver `app/auth.py` (dependency) e design.md D4 — verificação sempre local,
sem round-trip pro Django; qualquer `kid` presente no mapa configurado é
aceito, não só o mais recente (rotação sem downtime).
"""

from tests.conftest import (
    EXPORT_PAYLOAD,
    SIGNING_KID,
    SIGNING_SECRET,
    make_service_token,
)

EXPORT_PATH = "/document-generator/v1/decks/export"


def test_request_without_token_is_rejected(client):
    response = client.post(EXPORT_PATH, json=EXPORT_PAYLOAD)

    assert response.status_code == 401


def test_request_with_valid_token_is_accepted(client):
    token = make_service_token()

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_request_with_expired_token_is_rejected(client):
    token = make_service_token(expires_in=-10)

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_request_with_unknown_kid_is_rejected(client):
    token = make_service_token(kid="unknown-kid")

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_request_with_wrong_audience_is_rejected(client):
    token = make_service_token(audience="some-other-service")

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_request_with_wrong_secret_is_rejected(client):
    # Assinado com uma chave diferente da configurada para o mesmo `kid`
    # (simula um segredo desalinhado entre os dois lados do par).
    token = make_service_token(secret="a-completely-different-secret")

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_rotation_window_accepts_both_old_and_new_key(monkeypatch, client):
    from app.config import get_settings

    new_kid, new_secret = "v2", "new-signing-secret"
    monkeypatch.setenv(
        "SERVICE_JWT_KEYS",
        f'{{"{SIGNING_KID}": "{SIGNING_SECRET}", "{new_kid}": "{new_secret}"}}',
    )
    get_settings.cache_clear()

    old_token = make_service_token(kid=SIGNING_KID, secret=SIGNING_SECRET)
    new_token = make_service_token(kid=new_kid, secret=new_secret)

    for token in (old_token, new_token):
        response = client.post(
            EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


def test_removed_key_is_rejected_after_rotation(monkeypatch, client):
    from app.config import get_settings

    # Só a chave nova permanece configurada — simula o passo final da
    # rotação, depois que a chave antiga foi removida dos dois lados.
    monkeypatch.setenv("SERVICE_JWT_KEYS", '{"v2": "new-signing-secret"}')
    get_settings.cache_clear()

    old_token = make_service_token(kid=SIGNING_KID, secret=SIGNING_SECRET)

    response = client.post(
        EXPORT_PATH, json=EXPORT_PAYLOAD, headers={"Authorization": f"Bearer {old_token}"}
    )

    assert response.status_code == 401


def test_health_check_does_not_require_service_jwt(client):
    response = client.get("/document-generator/v1/health/")

    assert response.status_code == 200
