"""Management command: ingerir_transparencia

Usage:
    python manage.py ingerir_transparencia --codigo-orgao 26246 \\
        --municipio-ibge 3550308 --municipio-nome "São Paulo" --estado SP --paginas 5
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.api_service import IngestaoAPIService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ingere contratos do Portal da Transparência para um município."

    def add_arguments(self, parser):
        parser.add_argument(
            "--codigo-orgao",
            required=True,
            help="Código do órgão no Portal da Transparência.",
        )
        parser.add_argument(
            "--municipio-ibge",
            default="",
            help="Código IBGE do município (7 dígitos, ex: 3550308 para São Paulo).",
        )
        parser.add_argument(
            "--municipio-nome",
            default="",
            help="Nome do município (usado para criar o registro se não existir).",
        )
        parser.add_argument(
            "--estado",
            default="BR",
            help="UF do município (2 letras, ex: SP).",
        )
        parser.add_argument(
            "--paginas",
            type=int,
            default=None,
            help="Número máximo de páginas a buscar (padrão: todas).",
        )

    def handle(self, *args, **options):
        codigo_orgao: str = options["codigo_orgao"]
        codigo_ibge: str = options["municipio_ibge"]
        municipio_nome: str = options["municipio_nome"]
        estado: str = options["estado"]
        paginas: int | None = options["paginas"]

        if not codigo_ibge and not (municipio_nome and estado and estado != "BR"):
            raise CommandError(
                "Informe --municipio-ibge ou o par --municipio-nome e --estado."
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Iniciando ingestão Transparência ..."
            )
        )

        try:
            service = IngestaoAPIService()
            total = service.ingerir_contratos_transparencia(
                codigo_orgao=codigo_orgao,
                codigo_ibge=codigo_ibge,
                municipio_nome=municipio_nome,
                estado_uf=estado,
                paginas=paginas,
            )
        except Exception as exc:
            raise CommandError(f"Falha na ingestão: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"✅ {total} contratos processados."))
