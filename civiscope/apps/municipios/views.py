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

                resultados = IngestaoAPIService().ingerir_tudo_por_municipio(
                    municipio_nome=query,
                    estado_uf=estado_filter,
                    paginas=1,
                )
                sync_count = sum(resultados.values())
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
    """Detalhe de um município e seus candidatos."""
    municipio = get_object_or_404(Municipio, codigo_ibge=codigo_ibge)
    contratos = municipio.contratos.select_related("empresa").order_by(
        "-data_assinatura"
    )
    total_valor = contratos.aggregate(total=Sum("valor"))["total"]

    # Separar e agrupar candidatos (Filtro estrito para eleitos)
    todos_candidatos = municipio.vereadores.all()
    # No TSE, status de vitória são: ELEITO, ELEITO POR QP ou ELEITO POR MÉDIA
    eleitos_status_validos = ["eleito", "eleito por qp", "eleito por média"]
    eleitos = [
        c for c in todos_candidatos 
        if c.status_eleicao.lower() in eleitos_status_validos
    ]
    nao_eleitos = [
        c for c in todos_candidatos 
        if c.status_eleicao.lower() not in eleitos_status_validos
    ]

    # Agrupar eleitos por partido
    eleitos_por_partido = {}
    for c in eleitos:
        eleitos_por_partido.setdefault(c.partido_sigla, []).append(c)

    # Dados para o Grafo e Gráficos (JSON serializable)
    # Por enquanto, mockando alguns dados de performance se não existirem
    import random
    
    grafo_nodes = []
    performance_data = []
    
    for c in eleitos:
        # Mock de performance caso os campos estejam zerados
        aprovados_count = c.projetos_aprovados or random.randint(2, 12)
        total_count = c.total_projetos or aprovados_count + random.randint(5, 15)
        eficiencia = round((aprovados_count / total_count) * 100, 1) if total_count > 0 else 0
        
        # Mock de títulos de projetos
        projetos_mock = [
            f"Projeto de Lei {random.randint(100, 999)}/2024: {'Melhoria na Saúde' if i % 2 == 0 else 'Educação Municipal'}"
            for i in range(min(aprovados_count, 5))
        ]
        
        node = {
            "id": c.nome_urna,
            "group": c.partido_sigla,
            "coligacao": c.coligacao or c.partido_sigla,
            "reeleito": c.is_reeleito,
            "aprovados": aprovados_count,
            "total": total_count,
            "eficiencia": eficiencia,
            "projetos": projetos_mock,
            "foto_url": c.foto_url or "https://via.placeholder.com/150"
        }
        grafo_nodes.append(node)
        performance_data.append(node)

    # Dados para o Grafo (Baseado em Votos)
    # Lógica: Se dois vereadores votaram "SIM" no mesmo projeto, aumenta a conexão
    grafo_links = []
    
    # Gerar votos aleatórios para os vereadores eleitos em 10 projetos "virtuais"
    # (No futuro isso virá do banco de dados)
    projetos_virtuais = range(1, 11)
    votos_vereadores = {}
    
    # Criar perfis de voto por partido para gerar "clusters" mais naturais
    perfis_partidos = {p: random.random() for p in eleitos_por_partido.keys()}
    
    for c in eleitos:
        # O perfil de voto é influenciado pelo partido (70%) + aleatoriedade (30%)
        perfil_base = perfis_partidos.get(c.partido_sigla, 0.5)
        perfil_final = (perfil_base * 0.7) + (random.random() * 0.3)
        
        votos_vereadores[c.nome_urna] = [
            "SIM" if random.random() < perfil_final else "NAO" 
            for _ in projetos_virtuais
        ]

    # Calcular afinidade de voto (links)
    for i in range(len(eleitos)):
        for j in range(i + 1, len(eleitos)):
            v1 = eleitos[i].nome_urna
            v2 = eleitos[j].nome_urna
            
            # Contar quantos votos iguais eles tiveram
            concordancia = sum(
                1 for k in range(len(projetos_virtuais)) 
                if votos_vereadores[v1][k] == votos_vereadores[v2][k]
            )
            
            # Apenas criar link se a concordância for alta (ex: > 60%)
            # Reduzido de 7 para 6 para mostrar mais conexões relevantes
            if concordancia >= 6:
                grafo_links.append({
                    "source": v1,
                    "target": v2,
                    "value": concordancia
                })

    # Dados para o Mapa de Impacto (Mock)
    map_points = []
    # Coordenadas reais aproximadas de bairros em Colatina para o Mock
    bairros_coords = {
        "Centro": (-19.5350, -40.6270),
        "São Silvano": (-19.5250, -40.6150),
        "Honório Fraga": (-19.5100, -40.6350),
        "Vila Nova": (-19.5450, -40.6120),
        "Maria das Graças": (-19.5420, -40.6380),
        "Colatina Velha": (-19.5550, -40.6450),
        "Bela Vista": (-19.5280, -40.6000),
        "Castelo Branco": (-19.5050, -40.6200),
        "Santo Antônio": (-19.5600, -40.6250)
    }
    bairros_lista = list(bairros_coords.keys())

    # Mock de pontos para Projetos (Ideias Legislativas)
    for node in grafo_nodes[:8]: 
        # Para o mock, vamos atribuir um bairro de "foco" para o vereador/projeto
        bairro_alvo = random.choice(bairros_lista)
        base_lat, base_lng = bairros_coords.get(bairro_alvo, bairros_coords["Centro"])
        
        # Inserir o bairro no título para ficar claro na UI
        ponto = {
            "lat": base_lat + random.uniform(-0.003, 0.003),
            "lng": base_lng + random.uniform(-0.003, 0.003),
            "titulo": f"Projeto em {bairro_alvo}: {node['projetos'][0] if node['projetos'] else 'Melhoria Urbana'}",
            "tipo": "projeto",
            "autor": node["id"],
            "bairro": bairro_alvo
        }
        map_points.append(ponto)

    # Mock de pontos para Contratos (Gastos Públicos)
    for c in contratos[:8]:
        # Tenta usar o bairro do banco de dados (se houver), senão sorteia
        bairro_alvo = c.bairro if c.bairro else random.choice(bairros_lista)
        base_lat, base_lng = bairros_coords.get(bairro_alvo, bairros_coords["Centro"])
        
        ponto = {
            "lat": base_lat + random.uniform(-0.003, 0.003),
            "lng": base_lng + random.uniform(-0.003, 0.003),
            "titulo": f"Gasto Público em {bairro_alvo}: {c.objeto[:50]}...",
            "tipo": "contrato",
            "valor": float(c.valor),
            "bairro": bairro_alvo
        }
        map_points.append(ponto)

    return render(
        request,
        "municipios/detalhe.html",
        {
            "municipio": municipio,
            "contratos": contratos,
            "total_valor": total_valor,
            "eleitos": eleitos,
            "eleitos_por_partido": eleitos_por_partido,
            "nao_eleitos": nao_eleitos,
            "grafo_nodes": grafo_nodes,
            "grafo_links": grafo_links,
            "performance_data": performance_data,
            "map_points": map_points,
        },
    )
