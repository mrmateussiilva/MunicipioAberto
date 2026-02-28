from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet, Sum

from apps.contratos.models import Contrato

from .models import Indicador


class AnaliseContratosService:
    """Executa análises heurísticas e registra indicadores estatísticos.

    Os critérios abaixo são deliberadamente conservadores: o objetivo é sinalizar
    padrões para revisão humana, nunca afirmar irregularidade.
    """

    TIPO_CONCENTRACAO = "concentracao_contratos_empresa"
    TIPO_EMPRESA_RECENTE = "empresa_criada_proxima_ao_contrato"
    TIPO_REPETICAO = "repeticao_contratos_curto_periodo"

    def executar(self) -> dict[str, int]:
        with transaction.atomic():
            Indicador.objects.filter(
                tipo__in=[
                    self.TIPO_CONCENTRACAO,
                    self.TIPO_EMPRESA_RECENTE,
                    self.TIPO_REPETICAO,
                ]
            ).delete()

            resultados = {
                self.TIPO_CONCENTRACAO: self._analisar_concentracao_por_empresa(),
                self.TIPO_EMPRESA_RECENTE: self._analisar_empresa_recente(),
                self.TIPO_REPETICAO: self._analisar_repeticao_contratos(),
            }
        return resultados

    def _analisar_concentracao_por_empresa(self) -> int:
        total_indicadores = 0
        contratos = (
            Contrato.objects.select_related("municipio", "empresa")
            .values("municipio_id", "empresa_id")
            .annotate(valor_total=Sum("valor"))
        )

        totais_por_municipio = {
            item["municipio_id"]: item["valor_total"]
            for item in Contrato.objects.values("municipio_id").annotate(valor_total=Sum("valor"))
        }

        for item in contratos:
            total_municipio = totais_por_municipio.get(item["municipio_id"])
            valor_total = item["valor_total"]
            if not total_municipio or not valor_total:
                continue

            participacao = (Decimal(valor_total) / Decimal(total_municipio)) * Decimal("100")
            if participacao < Decimal("50"):
                continue

            contrato_referencia = (
                Contrato.objects.filter(
                    municipio_id=item["municipio_id"],
                    empresa_id=item["empresa_id"],
                )
                .order_by("-data_assinatura", "-id")
                .first()
            )
            if contrato_referencia is None:
                continue

            Indicador.objects.create(
                contrato=contrato_referencia,
                tipo=self.TIPO_CONCENTRACAO,
                score=participacao.quantize(Decimal("0.01")),
                descricao=(
                    "Empresa concentra parcela relevante do valor contratado no municipio "
                    f"({participacao:.2f}% do total observado)."
                ),
            )
            total_indicadores += 1

        return total_indicadores

    def _analisar_empresa_recente(self) -> int:
        total_indicadores = 0
        contratos: QuerySet[Contrato] = Contrato.objects.select_related("empresa")

        for contrato in contratos:
            diferenca = (contrato.data_assinatura - contrato.empresa.data_abertura).days
            if 0 <= diferenca <= 180:
                Indicador.objects.create(
                    contrato=contrato,
                    tipo=self.TIPO_EMPRESA_RECENTE,
                    score=Decimal(max(1, 181 - diferenca)),
                    descricao=(
                        "Empresa aberta em periodo proximo a data de assinatura do contrato "
                        f"({diferenca} dias de diferenca)."
                    ),
                )
                total_indicadores += 1

        return total_indicadores

    def _analisar_repeticao_contratos(self) -> int:
        total_indicadores = 0
        contratos = Contrato.objects.select_related("empresa", "municipio").order_by(
            "municipio_id",
            "empresa_id",
            "objeto",
            "data_assinatura",
            "id",
        )

        anterior: Contrato | None = None
        for contrato in contratos:
            if (
                anterior
                and anterior.municipio_id == contrato.municipio_id
                and anterior.empresa_id == contrato.empresa_id
                and anterior.objeto == contrato.objeto
                and contrato.data_assinatura - anterior.data_assinatura <= timedelta(days=30)
            ):
                intervalo = (contrato.data_assinatura - anterior.data_assinatura).days
                Indicador.objects.create(
                    contrato=contrato,
                    tipo=self.TIPO_REPETICAO,
                    score=Decimal(max(1, 31 - intervalo)),
                    descricao=(
                        "Contrato com mesmo objeto, municipio e empresa repetido em curto periodo "
                        f"({intervalo} dias)."
                    ),
                )
                total_indicadores += 1

            anterior = contrato

        return total_indicadores
