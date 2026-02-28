from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.analise.services import AnaliseContratosService


class Command(BaseCommand):
    help = "Executa as analises iniciais de contratos e gera indicadores."

    def handle(self, *args: object, **options: object) -> None:
        resultados = AnaliseContratosService().executar()
        for tipo, quantidade in resultados.items():
            self.stdout.write(f"{tipo}: {quantidade}")

        self.stdout.write(self.style.SUCCESS("Analises executadas com sucesso."))
