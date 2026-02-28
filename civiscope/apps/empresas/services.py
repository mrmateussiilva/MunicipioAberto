from __future__ import annotations

from datetime import date

from apps.municipios.models import Municipio

from .models import Empresa


class EmpresaService:
    @staticmethod
    def obter_ou_criar(
        *,
        nome: str,
        cnpj: str,
        data_abertura: date,
        municipio: Municipio | None = None,
    ) -> Empresa:
        empresa, _ = Empresa.objects.get_or_create(
            cnpj=cnpj,
            defaults={
                "nome": nome,
                "data_abertura": data_abertura,
                "municipio": municipio,
            },
        )
        return empresa
