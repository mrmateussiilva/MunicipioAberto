from __future__ import annotations

from decimal import Decimal

from apps.empresas.models import Empresa

from .models import Socio


class SocioService:
    @staticmethod
    def criar(
        *,
        nome: str,
        empresa: Empresa,
        percentual_participacao: Decimal,
        cpf: str | None = None,
    ) -> Socio:
        return Socio.objects.create(
            nome=nome,
            empresa=empresa,
            percentual_participacao=percentual_participacao,
            cpf=cpf,
        )
