from __future__ import annotations

from pathlib import Path

from apps.contratos.services import ContratoService
from apps.empresas.services import EmpresaService
from apps.municipios.services import MunicipioService

from .parsers import ContratoCSVParser


class ImportacaoContratosService:
    """Coordena parser e serviços de domínio para manter a ingestão orquestrada."""

    def __init__(self, parser: ContratoCSVParser | None = None) -> None:
        self.parser = parser or ContratoCSVParser()

    def importar_csv(self, file_path: str | Path) -> int:
        total_importado = 0

        for row in self.parser.parse(file_path):
            municipio = MunicipioService.obter_ou_criar(
                nome=row.municipio_nome,
                estado=row.municipio_estado,
                codigo_ibge=row.municipio_codigo_ibge,
                populacao=row.municipio_populacao,
            )
            empresa = EmpresaService.obter_ou_criar(
                nome=row.empresa_nome,
                cnpj=row.empresa_cnpj,
                data_abertura=row.empresa_data_abertura,
                municipio=municipio,
            )
            ContratoService.criar(
                municipio=municipio,
                empresa=empresa,
                objeto=row.objeto,
                valor=row.valor,
                data_assinatura=row.data_assinatura,
                data_publicacao=row.data_publicacao,
                fonte_dados=row.fonte_dados,
                numero_processo=row.numero_processo,
            )
            total_importado += 1

        return total_importado
