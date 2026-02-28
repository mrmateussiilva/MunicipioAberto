from __future__ import annotations

from datetime import date

from .models import Municipio


class MunicipioService:
    """Centraliza operações de escrita para evitar lógica espalhada em views ou commands."""

    @staticmethod
    def obter_ou_criar(
        *,
        nome: str,
        estado: str,
        codigo_ibge: str,
        populacao: int = 0,
        data_criacao: date | None = None,
    ) -> Municipio:
        municipio, created = Municipio.objects.get_or_create(
            codigo_ibge=codigo_ibge,
            defaults={
                "nome": nome,
                "estado": estado,
                "populacao": populacao,
                "data_criacao": data_criacao or date.today(),
            },
        )
        if not created:
            campos_atualizados: list[str] = []

            if nome and municipio.nome != nome:
                municipio.nome = nome
                campos_atualizados.append("nome")

            if estado and municipio.estado != estado:
                municipio.estado = estado
                campos_atualizados.append("estado")

            if populacao and municipio.populacao != populacao:
                municipio.populacao = populacao
                campos_atualizados.append("populacao")

            if data_criacao and municipio.data_criacao != data_criacao:
                municipio.data_criacao = data_criacao
                campos_atualizados.append("data_criacao")

            if campos_atualizados:
                municipio.save(update_fields=campos_atualizados)

        return municipio
