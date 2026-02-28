# civiscope

Ferramenta open source para ingestão, organização e análise de dados públicos municipais, com foco em contratos públicos e geração de indicadores estatísticos.

## Aviso legal

Este projeto organiza dados públicos e gera indicadores estatísticos. Não realiza acusações ou afirmações legais. Todos os dados devem ser verificados nas fontes oficiais.

## Objetivo

O `civiscope` foi estruturado para apoiar análise técnica de dados públicos municipais, com separação clara entre domínios, camada de serviços e base pronta para crescer como projeto open source.

O sistema:

- ingere dados de contratos a partir de CSV;
- organiza entidades como municípios, empresas, sócios e contratos;
- executa análises automáticas para identificar padrões estatísticos e registros incomuns;
- persiste indicadores sem produzir juízo acusatório.

## Stack

- Python 3.11+
- Django 5+
- PostgreSQL
- Docker / Docker Compose

## Estrutura

```text
civiscope/
├── manage.py
├── civiscope/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── municipios/
│   ├── empresas/
│   ├── contratos/
│   ├── socios/
│   ├── ingestion/
│   └── analise/
└── fixtures/
```

## Como rodar localmente

1. Crie e ative um ambiente virtual com Python 3.11 ou superior.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

4. Ajuste as variáveis de banco PostgreSQL no `.env`.
5. Rode as migrações:

```bash
cd civiscope
python manage.py migrate
```

6. Carregue os dados de exemplo:

```bash
python manage.py loaddata fixtures/exemplo_inicial.json
```

7. Inicie o servidor:

```bash
python manage.py runserver
```

## Comandos úteis

Importar contratos a partir de um CSV:

```bash
python manage.py importar_contratos_csv caminho/para/arquivo.csv
```

Executar as análises automáticas:

```bash
python manage.py rodar_analise
```

## Docker

O repositório inclui `Dockerfile` e `docker-compose.yml` para subir a aplicação Django e um PostgreSQL 16 no mesmo ambiente.

Para subir a stack:

```bash
docker compose up --build
```

O serviço `app` aguarda o `postgres`, executa `migrate` automaticamente e então sobe o servidor em `http://localhost:8000`.

### Alternativa para ambientes sem bridge networking

Se o Docker falhar ao criar a rede bridge (erro com `failed to add the host <=> sandbox pair interfaces`), use a variante com rede do host em Linux:

```bash
cp .env.example .env
docker compose -f docker-compose.host.yml up --build
```

Essa variante usa `network_mode: host`, evita a rede bridge do Compose e conecta a aplicação ao PostgreSQL em `127.0.0.1`.

## Como contribuir

- Abra uma issue descrevendo problema, melhoria ou nova análise.
- Mantenha regras de negócio em `services.py`, evitando acoplamento em `models.py`.
- Preserve a separação por domínio e a organização modular.
- Adicione testes e documentação junto com novas funcionalidades.

## Diretrizes de arquitetura

- Configurações separadas por ambiente (`base.py`, `dev.py`, `prod.py`).
- Regras de negócio centralizadas em serviços por app.
- Apps separados por domínio para facilitar evolução e manutenção.
- Estrutura preparada para novas rotinas de ingestão e análises adicionais.
