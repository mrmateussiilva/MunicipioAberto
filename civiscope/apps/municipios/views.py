"""Views for the municipios app."""

from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render

from .models import Municipio


def busca(request):
    """Tela de busca por cidade ou estado."""
    query = request.GET.get("q", "").strip()
    estado_filter = request.GET.get("estado", "").strip().upper()

    municipios = []
    total_contratos = 0
    total_valor = None

    if query or estado_filter:
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

        municipios = qs.order_by("estado", "nome")
        total_contratos = sum(m.num_contratos for m in municipios)
        total_valor = sum(
            m.total_contratos_valor or 0 for m in municipios
        )

    # Lista de estados únicos para o filtro
    estados = (
        Municipio.objects.values_list("estado", flat=True)
        .distinct()
        .order_by("estado")
    )

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
        },
    )


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
