"""Client for TSE DivulgaCandContas API (Candidacies and results)."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseAPIClient
from .schemas import TSECandidatoSchema

logger = logging.getLogger(__name__)

class TSEClient(BaseAPIClient):
    """
    Client for the unofficial but public TSE DivulgaCandContas API.
    
    Documentation reference: https://github.com/augusto-herrmann/divulgacandcontas-doc
    """

    base_url = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1"

    def get_eleicoes_ordinarias(self) -> list[dict[str, Any]]:
        """Lista todas as eleições ordinárias disponíveis."""
        return self._get("/eleicao/ordinarias")

    def get_eleicao_id(self, ano: int = 2024) -> int:
        """
        Retorna o ID da eleição municipal para o ano especificado.
        Para 2024, o padrão é 2045202024.
        """
        eleicoes = self.get_eleicoes_ordinarias()
        for e in eleicoes:
            if e.get("ano") == ano and e.get("tipoAbrangencia") == "M":
                return e.get("id")
        
        # Fallback para o ID conhecido de 2024 se não encontrar
        if ano == 2024:
            return 2045202024
        raise ValueError(f"Eleição municipal para o ano {ano} não encontrada.")

    def buscar_municipio_tse_code(self, eleicao_id: int, uf: str, nome_municipio: str) -> str:
        """
        Busca o código TSE do município (diferente do IBGE).
        """
        import unicodedata

        def normalizar(txt: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", txt.upper())
                if unicodedata.category(c) != "Mn"
            ).strip()

        endpoint = f"/eleicao/buscar/{uf}/{eleicao_id}/municipios"
        data = self._get(endpoint)
        
        municipios = data.get("municipios", [])
        nome_alvo = normalizar(nome_municipio)
        
        for m in municipios:
            if normalizar(m.get("nome", "")) == nome_alvo:
                return m.get("codigo")
        
        raise ValueError(f"Município {nome_municipio}/{uf} não encontrado na base do TSE para a eleição {eleicao_id}.")

    def listar_candidatos(
        self, 
        ano: int, 
        tse_municipio_code: str, 
        eleicao_id: int, 
        cargo_code: int = 13
    ) -> list[TSECandidatoSchema]:
        """
        Lista todos os candidatos para um cargo específico em um município.
        Cargo 13 = Vereador, 11 = Prefeito.
        """
        endpoint = f"/candidatura/listar/{ano}/{tse_municipio_code}/{eleicao_id}/{cargo_code}/candidatos"
        data = self._get(endpoint)
        
        candidatos_raw = data.get("candidatos", [])
        return [TSECandidatoSchema.model_validate(c) for c in candidatos_raw]

    def get_candidatos_com_detalhes(self, ano: int, tse_municipio_code: str, eleicao_id: int, cargo_code: int = 13) -> list[TSECandidatoSchema]:
        """Retorna todos os candidatos (eleitos e não eleitos)."""
        return self.listar_candidatos(ano, tse_municipio_code, eleicao_id, cargo_code)
