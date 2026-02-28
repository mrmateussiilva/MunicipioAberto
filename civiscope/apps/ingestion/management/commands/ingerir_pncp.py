"""Management command: ingerir_pncp

Usage:
    python manage.py ingerir_pncp --cnpj-orgao 00394460000141 \\
        --municipio-ibge 3550308 --municipio-nome "São Paulo" --estado SP --paginas 3
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.api_service import IngestaoAPIService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ingere contratos do PNCP (Portal Nacional de Contratações Públicas)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cnpj-orgao",
            required=True,
            help="CNPJ do órgão público (apenas dígitos, ex: 00394460000141).",
        )
        parser.add_argument(
            "--municipio-ibge",
            default="0000000",
            help="Código IBGE do município relacionado ao órgão.",
        )
        parser.add_argument(
            "--municipio-nome",
            default="",
            help="Nome do município.",
        )
        parser.add_argument(
            "--estado",
            default="BR",
            help="UF do município (2 letras).",
        )
        parser.add_argument(
            "--data-inicio",
            default="",
            help="Data inicial para busca (YYYYMMDD, ex: 20240101). Padrão: 01/01 do ano atual.",
        )
        parser.add_argument(
            "--data-fim",
            default="",
            help="Data final para busca (YYYYMMDD, ex: 20241231). Padrão: 31/12 do ano atual.",
        )
        parser.add_argument(
            "--paginas",
            type=int,
            default=None,
            help="Número máximo de páginas a buscar (padrão: todas).",
        )

    def handle(self, *args, **options):
        cnpj_orgao: str = options["cnpj_orgao"]
        municipio_ibge: str = options["municipio_ibge"]
        municipio_nome: str = options["municipio_nome"]
        estado: str = options["estado"]
        paginas: int | None = options["paginas"]
        data_inicio: str = options["data_inicio"]
        data_fim: str = options["data_fim"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Iniciando ingestão PNCP — CNPJ órgão {cnpj_orgao} ..."
            )
        )

        try:
            service = IngestaoAPIService()
            total = service.ingerir_contratos_pncp(
                cnpj_orgao=cnpj_orgao,
                codigo_ibge=municipio_ibge,
                municipio_nome=municipio_nome,
                estado_uf=estado,
                paginas=paginas,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        except Exception as exc:
            raise CommandError(f"Falha na ingestão: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"✅ {total} contratos processados."))
