"""
Nomes de `Group` usados pela autorização (Sprint 5, `permissoes-grupo-sem-contenttype`).

Constante única compartilhada pela migration de dados, pelo signal de
auto-atribuição (`signals.py`), pela `permission_classes` customizada
(`permissions.py`) e pelo comando de seed — evita o nome literal
"standard_user" espalhado e divergindo em algum desses lugares.
"""

STANDARD_USER_GROUP = "standard_user"
