# Integração com APIs Públicas Governamentais

Este documento descreve como configurar e usar os clientes de APIs públicas disponíveis no módulo `apps/ingestion/clients/`.

---

## APIs Suportadas

| API | Cliente | Porta | Autenticação |
|-----|---------|-------|-------------|
| Portal da Transparência | `TransparenciaClient` | `transparencia.py` | Token via header |
| PNCP | `PNCPClient` | `pncp.py` | Pública (sem token) |
| Dados Abertos | `DadosAbertosClient` | `dados_abertos.py` | Pública (sem token) |

---

## Configuração

### 1. Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```env
# ── Portal da Transparência (OBRIGATÓRIO para este cliente) ──────────────────
# Token gratuito obtido em: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
TRANSPARENCIA_API_KEY=seu-token-aqui

# ── Configurações opcionais (têm valores padrão) ────────────────────────────
PNCP_BASE_URL=https://pncp.gov.br/api/pncp/v1
DADOS_ABERTOS_BASE_URL=https://dados.gov.br/api/3
API_REQUEST_TIMEOUT=30      # Timeout HTTP em segundos
API_MAX_RETRIES=3           # Tentativas em caso de falha de rede
API_RATE_LIMIT_DELAY=0.5    # Pausa mínima entre requisições (segundos)
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
# ou, com uv:
uv sync
```

Novas dependências adicionadas:
- **`httpx`** — cliente HTTP moderno com suporte a mock em testes
- **`pydantic`** — validação e deserialização das respostas JSON
- **`tenacity`** — retry automático com exponential back-off

---

## Como Usar

### Via Management Commands (CLI)

#### Portal da Transparência — contratos de um município

```bash
# Busca contratos de São Paulo (código IBGE 3550308), primeiras 5 páginas
python manage.py ingerir_transparencia \
  --municipio-ibge 3550308 \
  --municipio-nome "São Paulo" \
  --estado SP \
  --paginas 5
```

#### PNCP — contratos de um órgão público

```bash
# Busca contratos do Ministério da Educação (CNPJ 00394460000141)
python manage.py ingerir_pncp \
  --cnpj-orgao 00394460000141 \
  --municipio-ibge 5300108 \
  --municipio-nome "Brasília" \
  --estado DF \
  --paginas 3
```

### Via Python / Django Shell

```python
# Portal da Transparência
from apps.ingestion.clients import TransparenciaClient

with TransparenciaClient() as client:
    for contrato in client.contratos(codigo_ibge="3550308", paginas=2):
        print(contrato.numero, contrato.valor_inicial, contrato.nome_fornecedor)

# PNCP
from apps.ingestion.clients import PNCPClient

with PNCPClient() as client:
    for contrato in client.contratos_por_orgao("00394460000141", paginas=1):
        print(contrato.numero_contrato, contrato.valor_global)

    # Busca por período
    for contrato in client.contratos_recentes("20240101", "20240131"):
        print(contrato.objeto)

# Dados Abertos
from apps.ingestion.clients import DadosAbertosClient

with DadosAbertosClient() as client:
    for dataset in client.buscar_datasets("contratos municipais"):
        print(dataset.title, dataset.id)
        for recurso in dataset.resources:
            print(f"  - {recurso.name} ({recurso.format}): {recurso.url}")
```

### Via IngestaoAPIService

```python
from apps.ingestion.api_service import IngestaoAPIService

service = IngestaoAPIService()

# Ingere e salva no banco automaticamente
total = service.ingerir_contratos_transparencia(
    codigo_ibge="3550308",
    municipio_nome="São Paulo",
    estado_uf="SP",
    paginas=2,
)
print(f"{total} contratos salvos")
```

---

## Arquitetura do Módulo

```
apps/ingestion/
├── clients/
│   ├── __init__.py          # Exports: TransparenciaClient, PNCPClient, DadosAbertosClient
│   ├── base.py              # BaseAPIClient: retry, rate-limit, paginação, logging
│   ├── schemas.py           # Modelos Pydantic para validar respostas
│   ├── transparencia.py     # Portal da Transparência
│   ├── pncp.py              # PNCP / Compras Públicas (OCDS)
│   └── dados_abertos.py     # Portal Brasileiro de Dados Abertos
├── api_service.py           # IngestaoAPIService: orquestra cliente → banco
├── management/commands/
│   ├── ingerir_transparencia.py
│   └── ingerir_pncp.py
└── tests/
    ├── test_base_client.py
    ├── test_transparencia_client.py
    ├── test_pncp_client.py
    ├── test_dados_abertos_client.py
    └── test_api_service.py
```

---

## Ingestão Unificada por Cidade e Estado

O comando `ingerir_municipio` é a forma mais simples de coletar dados públicos. Ele resolve automaticamente o código IBGE da cidade e busca contratos em **todas as fontes disponíveis** (PNCP + Portal da Transparência).

### Uso básico

```bash
# Apenas cidade e UF — resolve tudo automaticamente:
python manage.py ingerir_municipio --cidade "Colatina" --estado ES

# Com mais páginas e período específico:
python manage.py ingerir_municipio --cidade "São Paulo" --estado SP \
    --paginas 3 --data-inicio 20240101 --data-fim 20241231
```

### Argumentos

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--cidade` | ✅ | Nome da cidade |
| `--estado` | ✅ | UF (2 letras, ex: SP, ES, RJ) |
| `--codigo-ibge` | ❌ | Código IBGE (resolve automaticamente se omitido) |
| `--paginas` | ❌ | Máx. de páginas por fonte (padrão: 1) |
| `--data-inicio` | ❌ | Data inicial YYYYMMDD (padrão: 01/01 do ano atual) |
| `--data-fim` | ❌ | Data final YYYYMMDD (padrão: 31/12 do ano atual) |

### O que acontece internamente

1. Resolve o nome da cidade + UF para código IBGE via API do IBGE
2. Busca contratos no PNCP filtrando pelo município
3. Descobre órgãos federais no município via Portal da Transparência
4. Para cada órgão encontrado, busca contratos na Transparência
5. Salva tudo no banco de dados e exibe um resumo

### Via Python / Django Shell

```python
from apps.ingestion.api_service import IngestaoAPIService

service = IngestaoAPIService()
resultados = service.ingerir_tudo_por_municipio(
    municipio_nome="Colatina",
    estado_uf="ES",
    paginas=2,
)
print(f"PNCP: {resultados['pncp']} contratos")
print(f"Transparência: {resultados['transparencia']} contratos")
```

---

## Rodando os Testes

```bash
# No container Docker:
docker compose exec app python -m pytest apps/ingestion/tests/ -v

# Ou localmente (com .venv ativo):
cd civiscope
python -m pytest apps/ingestion/tests/ -v
```

---

## Tratamento de Erros e Limites

- **Retry automático**: falhas de rede e timeout são re-tentadas até `API_MAX_RETRIES` vezes com back-off exponencial (2s → 4s → 8s...)
- **Rate limit do servidor (429)**: ao receber HTTP 429, o cliente aguarda 60 segundos antes de re-tentar
- **Registros inválidos**: validações Pydantic que falham emitem `WARNING` no log e pulam o item — não interrompem a ingestão
- **Logging**: configure `DJANGO_LOG_LEVEL=DEBUG` no `.env` para ver detalhes de cada requisição

---

## Obtendo o Token da Transparência

1. Acesse: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
2. Informe seu e-mail e confirme o cadastro
3. Copie o token recebido por e-mail para `TRANSPARENCIA_API_KEY` no `.env`
