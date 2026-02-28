"""Management command: ingerir_municipio

Usage:
    python manage.py ingerir_municipio --cidade "Colatina" --estado ES
    python manage.py ingerir_municipio --cidade "São Paulo" --estado SP --paginas 3
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.api_service import IngestaoAPIService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Ingere contratos de TODAS as fontes públicas (PNCP + Transparência) "
        "para um município, a partir do nome da cidade e UF."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cidade",
            required=True,
            help="Nome da cidade (ex: 'Colatina', 'São Paulo').",
        )
        parser.add_argument(
            "--estado",
            required=True,
            help="UF do estado (2 letras, ex: ES, SP, RJ).",
        )
        parser.add_argument(
            "--codigo-ibge",
            default="",
            help="Código IBGE do município (opcional — resolve automaticamente se omitido).",
        )
        parser.add_argument(
            "--paginas",
            type=int,
            default=5,
            help="Número máximo de páginas por fonte (padrão: 5).",
        )
        parser.add_argument(
            "--data-inicio",
            default="",
            help="Data inicial para busca (YYYYMMDD). Padrão: 01/01 do ano atual.",
        )
        parser.add_argument(
            "--data-fim",
            default="",
            help="Data final para busca (YYYYMMDD). Padrão: 31/12 do ano atual.",
        )

    def handle(self, *args, **options):
        cidade: str = options["cidade"].strip()
        estado: str = options["estado"].strip().upper()
        codigo_ibge: str = options["codigo_ibge"].strip()
        paginas: int = options["paginas"]
        data_inicio: str = options["data_inicio"].strip()
        data_fim: str = options["data_fim"].strip()

        if len(estado) != 2:
            raise CommandError("O estado deve ter exatamente 2 letras (ex: SP, ES, RJ).")

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"🔍 Resolvendo município: {cidade}/{estado} ...")
        )

        try:
            service = IngestaoAPIService()
            resultados = service.ingerir_tudo_por_municipio(
                municipio_nome=cidade,
                estado_uf=estado,
                codigo_ibge=codigo_ibge,
                paginas=paginas,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:
            raise CommandError(f"Falha na ingestão: {exc}") from exc

        total_pncp = resultados.get("pncp", 0)
        total_transparencia = resultados.get("transparencia", 0)
        total_geral = total_pncp + total_transparencia

        self.stdout.write("")
        self.stdout.write(f"  📡 PNCP: {total_pncp} contratos")
        self.stdout.write(f"  📡 Transparência: {total_transparencia} contratos")
        self.stdout.write("")
        self.stdout.write("━" * 40)
        self.stdout.write(
            self.style.SUCCESS(
                f"📊 Total: {total_geral} contratos de {sum(1 for v in resultados.values() if v > 0)} fonte(s)"
            )
        )
