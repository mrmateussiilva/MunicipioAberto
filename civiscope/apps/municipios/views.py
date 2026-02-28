"""Views for the municipios app."""

from __future__ import annotations

import logging

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render

from apps.ingestion.api_service import IngestaoAPIService

from .models import Municipio

logger = logging.getLogger(__name__)


ESTADOS_BR = [
    ("AC", "AC — Acre"),
    ("AL", "AL — Alagoas"),
    ("AP", "AP — Amapá"),
    ("AM", "AM — Amazonas"),
    ("BA", "BA — Bahia"),
    ("CE", "CE — Ceará"),
    ("DF", "DF — Distrito Federal"),
    ("ES", "ES — Espírito Santo"),
    ("GO", "GO — Goiás"),
    ("MA", "MA — Maranhão"),
    ("MT", "MT — Mato Grosso"),
    ("MS", "MS — Mato Grosso do Sul"),
    ("MG", "MG — Minas Gerais"),
    ("PA", "PA — Pará"),
    ("PB", "PB — Paraíba"),
    ("PR", "PR — Paraná"),
    ("PE", "PE — Pernambuco"),
    ("PI", "PI — Piauí"),
    ("RJ", "RJ — Rio de Janeiro"),
    ("RN", "RN — Rio Grande do Norte"),
    ("RS", "RS — Rio Grande do Sul"),
    ("RO", "RO — Rondônia"),
    ("RR", "RR — Roraima"),
    ("SC", "SC — Santa Catarina"),
    ("SP", "SP — São Paulo"),
    ("SE", "SE — Sergipe"),
    ("TO", "TO — Tocantins"),
]


def _consultar_municipios(query: str, estado_filter: str):
    qs = Municipio.objects.annotate(
        num_contratos=Count("contratos"),
        total_contratos_valor=Sum("contratos__valor"),
    )

    if query:
        qs = qs.filter(
            Q(nome__icontains=query) | Q(estado__iexact=query)
        )

    if estado_filter:
        qs = qs.filter(estado=estado_filter)

    return list(qs.order_by("estado", "nome"))


def busca(request):
    """Tela de busca por cidade ou estado."""
    query = request.GET.get("q", "").strip()
    estado_filter = request.GET.get("estado", "").strip().upper()
    action = request.GET.get("action", "").strip().lower()

    municipios = []
    total_contratos = 0
    total_valor = None
    sync_count = None
    sync_error = ""
    sync_enabled = bool(query and estado_filter)

    if query or estado_filter:
        if action == "sync":
            try:
                if not (query and estado_filter):
                    raise ValueError(
                        "Informe cidade e UF para sincronizar dados públicos."
                    )

                sync_count = IngestaoAPIService().ingerir_contratos_pncp_por_municipio(
                    municipio_nome=query,
                    estado_uf=estado_filter,
                    paginas=1,
                )
            except Exception as exc:  # noqa: BLE001
                sync_error = str(exc)
                logger.warning(
                    "Falha ao sincronizar contratos públicos para %s/%s: %s",
                    query,
                    estado_filter,
                    exc,
                )

        municipios = _consultar_municipios(query, estado_filter)

        total_contratos = sum(m.num_contratos for m in municipios)
        total_valor = sum(
            m.total_contratos_valor or 0 for m in municipios
        )

    estados = [
        {"value": uf, "label": label, "selected": uf == estado_filter}
        for uf, label in ESTADOS_BR
    ]

    return render(
        request,
        "municipios/busca.html",
        {
            "municipios": municipios,
            "query": query,
            "estado_filter": estado_filter,
            "estados": estados,
            "total_contratos": total_contratos,
            "total_valor": total_valor,
            "sync_count": sync_count,
            "sync_error": sync_error,
            "sync_enabled": sync_enabled,
        },
    )



def autocomplete_cidades(request):
    """Retorna JSON com sugestões de cidades para o autocomplete."""
    from django.http import JsonResponse

    query = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip().upper()

    if len(query) < 2:
        return JsonResponse([], safe=False)

    qs = Municipio.objects.filter(nome__icontains=query)

    if estado:
        qs = qs.filter(estado=estado)

    qs = qs.order_by("estado", "nome")[:10]

    results = [
        {"nome": m.nome, "estado": m.estado, "codigo_ibge": m.codigo_ibge}
        for m in qs
    ]
    return JsonResponse(results, safe=False)


def detalhe_municipio(request, codigo_ibge):
    """Detalhe de um município e seus contratos."""
    municipio = get_object_or_404(Municipio, codigo_ibge=codigo_ibge)
    contratos = municipio.contratos.select_related("empresa").order_by(
        "-data_assinatura"
    )
    total_valor = contratos.aggregate(total=Sum("valor"))["total"]

    return render(
        request,
        "municipios/detalhe.html",
        {
            "municipio": municipio,
            "contratos": contratos,
            "total_valor": total_valor,
        },
    )
