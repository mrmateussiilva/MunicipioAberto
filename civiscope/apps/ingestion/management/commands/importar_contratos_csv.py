from __future__ import annotations

from django.core.management.base import BaseCommand, CommandParser

from apps.ingestion.jobs import importar_contratos_em_lote


class Command(BaseCommand):
    help = "Importa contratos públicos municipais a partir de um arquivo CSV."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("arquivo", type=str, help="Caminho para o arquivo CSV.")

    def handle(self, *args: object, **options: object) -> None:
        arquivo = str(options["arquivo"])
        total = importar_contratos_em_lote(arquivo)
        self.stdout.write(self.style.SUCCESS(f"{total} contratos importados com sucesso."))
