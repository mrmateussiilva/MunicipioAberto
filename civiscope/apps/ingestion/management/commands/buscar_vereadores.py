"""Management command: buscar_vereadores

Usage:
    python manage.py buscar_vereadores --cidade "Colatina" --estado ES
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.clients.tse import TSEClient
from apps.ingestion.clients.ibge import IBGEClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Busca os vereadores eleitos em mandato atual (2025-2028) para um município."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cidade",
            required=True,
            help="Nome da cidade.",
        )
        parser.add_argument(
            "--estado",
            required=True,
            help="UF do estado (ex: ES, SP).",
        )
        parser.add_argument(
            "--ano",
            type=int,
            default=2024,
            help="Ano da eleição (padrão: 2024 para mandato atual).",
        )

    def handle(self, *args, **options):
        cidade: str = options["cidade"].strip()
        estado: str = options["estado"].strip().upper()
        ano: int = options["ano"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"🔎 Buscando vereadores eleitos: {cidade}/{estado} ({ano}) ...")
        )

        try:
            tse = TSEClient()
            
            # 1. Identificar ID da eleição
            self.stdout.write("  - Identificando eleição...")
            eleicao_id = tse.get_eleicao_id(ano)
            
            # 2. Descobrir código TSE do município
            self.stdout.write(f"  - Localizando código TSE para {cidade}/{estado}...")
            tse_code = tse.buscar_municipio_tse_code(eleicao_id, estado, cidade)
            
            # 3. Listar vereadores eleitos
            self.stdout.write("  - Consultando candidatos eleitos...")
            vereadores = tse.get_vereadores_eleitos(ano, tse_code, eleicao_id)
            
            if not vereadores:
                self.stdout.write(self.style.WARNING(f"Nenhum vereador eleito encontrado para {cidade}/{estado}."))
                return

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(f"✅ Encontrados {len(vereadores)} vereadores eleitos:"))
            self.stdout.write("━" * 60)
            
            # Ordenar por nome de urna
            vereadores.sort(key=lambda x: x.nome_urna)
            
            for v in vereadores:
                reeleito_str = " (Reeleito)" if v.st_reeleicao else ""
                self.stdout.write(
                    f"• {v.nome_urna.ljust(25)} | {v.partido.sigla.ljust(10)} | {v.descricao_totalizacao}{reeleito_str}"
                )
            
            self.stdout.write("━" * 60)
            self.stdout.write(self.style.SUCCESS(f"Total: {len(vereadores)} vereadores."))

        except Exception as exc:
            logger.exception("Erro ao buscar vereadores")
            raise CommandError(f"Falha na busca: {exc}")
