"""API client module for civiscope ingestion."""

from .dados_abertos import DadosAbertosClient
from .pncp import PNCPClient
from .transparencia import TransparenciaClient

__all__ = ["DadosAbertosClient", "PNCPClient", "TransparenciaClient"]
