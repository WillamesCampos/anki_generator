"""Leitura de um `.apkg` gerado — é um zip com `collection.anki2` (SQLite) e
um `media` (JSON índice → nome do arquivo). Os testes inspecionam o pacote
real em vez de detalhes internos do gerador."""

import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


def read_apkg(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        media = json.loads(zf.read("media"))
        with tempfile.TemporaryDirectory() as tmp:
            zf.extract("collection.anki2", tmp)
            conn = sqlite3.connect(Path(tmp) / "collection.anki2")
            try:
                decks_json, models_json = conn.execute(
                    "select decks, models from col"
                ).fetchone()
                notes = conn.execute("select guid, mid, flds from notes order by id").fetchall()
            finally:
                conn.close()
    decks = json.loads(decks_json)
    models = json.loads(models_json)
    return {
        "deck_ids": sorted(int(k) for k in decks if k != "1"),
        "model_ids": sorted(int(k) for k in models),
        "notes": [{"guid": g, "model_id": m, "fields": f.split("\x1f")} for g, m, f in notes],
        "media": sorted(media.values()),
    }
