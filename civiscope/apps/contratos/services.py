from __future__ import annotations

from datetime import date
from decimal import Decimal

from apps.empresas.models import Empresa
from apps.municipios.models import Municipio

from .models import Contrato


class ContratoService:
    @staticmethod
    def criar(
        *,
        municipio: Municipio,
        empresa: Empresa,
        objeto: str,
        valor: Decimal,
        data_assinatura: date,
        data_publicacao: date,
        fonte_dados: str,
        numero_processo: str,
    ) -> Contrato:
        contrato, _ = Contrato.objects.get_or_create(
            municipio=municipio,
            empresa=empresa,
            numero_processo=numero_processo,
            defaults={
                "objeto": objeto,
                "valor": valor,
                "data_assinatura": data_assinatura,
                "data_publicacao": data_publicacao,
                "fonte_dados": fonte_dados,
            },
        )
        return contrato
