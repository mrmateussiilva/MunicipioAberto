from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterator


@dataclass(slots=True)
class ContratoCSVRow:
    municipio_nome: str
    municipio_estado: str
    municipio_codigo_ibge: str
    municipio_populacao: int
    empresa_nome: str
    empresa_cnpj: str
    empresa_data_abertura: date
    objeto: str
    valor: Decimal
    data_assinatura: date
    data_publicacao: date
    fonte_dados: str
    numero_processo: str


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


class ContratoCSVParser:
    """Parser explícito para manter o formato de entrada previsível e versionável."""

    REQUIRED_FIELDS = {
        "municipio_nome",
        "municipio_estado",
        "municipio_codigo_ibge",
        "municipio_populacao",
        "empresa_nome",
        "empresa_cnpj",
        "empresa_data_abertura",
        "objeto",
        "valor",
        "data_assinatura",
        "data_publicacao",
        "fonte_dados",
        "numero_processo",
    }

    def parse(self, file_path: str | Path) -> Iterator[ContratoCSVRow]:
        with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing = self.REQUIRED_FIELDS.difference(reader.fieldnames or [])
            if missing:
                raise ValueError(f"CSV sem colunas obrigatorias: {', '.join(sorted(missing))}")

            for row in reader:
                yield ContratoCSVRow(
                    municipio_nome=row["municipio_nome"].strip(),
                    municipio_estado=row["municipio_estado"].strip(),
                    municipio_codigo_ibge=row["municipio_codigo_ibge"].strip(),
                    municipio_populacao=int(row["municipio_populacao"]),
                    empresa_nome=row["empresa_nome"].strip(),
                    empresa_cnpj=row["empresa_cnpj"].strip(),
                    empresa_data_abertura=_parse_date(row["empresa_data_abertura"]),
                    objeto=row["objeto"].strip(),
                    valor=Decimal(row["valor"]),
                    data_assinatura=_parse_date(row["data_assinatura"]),
                    data_publicacao=_parse_date(row["data_publicacao"]),
                    fonte_dados=row["fonte_dados"].strip(),
                    numero_processo=row["numero_processo"].strip(),
                )
