from fastapi import APIRouter, Depends, Response

from app.auth import require_service_jwt
from app.pdf import PdfDocument, render_pdf

router = APIRouter(
    prefix="/documents", tags=["Documents"], dependencies=[Depends(require_service_jwt)]
)


@router.post("/pdf")
def generate_pdf(document: PdfDocument) -> Response:
    """Gera um PDF a partir de título + seções tipadas (Sprint 11).

    Mesma proteção do `/decks/export` (`require_service_jwt`). Rota síncrona
    (`def`) de propósito: a renderização é CPU-bound e o FastAPI a roda numa
    threadpool, sem travar o event loop. O PDF é montado em memória.
    """
    return Response(content=render_pdf(document), media_type="application/pdf")
