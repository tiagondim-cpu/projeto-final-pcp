"""Configuração global do projeto (reprodutibilidade - critério C3).

Toda geração de números aleatórios no projeto deve passar por `get_rng()`,
garantindo que qualquer execução reproduza exatamente os mesmos resultados.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# Semente global única. Não usar np.random.seed disperso pelo código:
# sempre obter o gerador via get_rng().
SEED: int = 42


def get_rng(seed: int = SEED) -> np.random.Generator:
    """Retorna um gerador aleatório reprodutível (NumPy Generator)."""
    return np.random.default_rng(seed)


# Caminhos do projeto (independentes do diretório de execução).
ROOT: Path = Path(__file__).resolve().parents[1]
DATA_RAW: Path = ROOT / "data" / "raw"
DATA_PROCESSED: Path = ROOT / "data" / "processed"
DOCS: Path = ROOT / "docs"
REPORTS: Path = ROOT / "reports"
NOTEBOOKS: Path = ROOT / "notebooks"
