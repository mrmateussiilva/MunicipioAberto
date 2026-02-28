from __future__ import annotations

from pathlib import Path

from .services import ImportacaoContratosService


def importar_contratos_em_lote(file_path: str | Path) -> int:
    """Ponto único para futura integração com filas ou schedulers."""

    service = ImportacaoContratosService()
    return service.importar_csv(file_path)
