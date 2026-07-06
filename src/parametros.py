"""Parâmetros do caso - fonte única da verdade (Projeto Final de PCP).

Caso: fabricante brasileiro de ventiladores domésticos (linha branca de pequeno
porte, agregados em um produto equivalente), make-to-stock. Planejamento agregado
de 12 meses com demanda sazonal: o ano de planejamento começa na baixa estação
(inverno), sobe ao pico de verão no mês 7 e volta a cair.

Modelo de custo: CUSTO-RELEVANTE de planejamento agregado (Nahmias / Hopp-Spearman).
O custo de mão de obra é o SALÁRIO por trabalhador por mês (pago independentemente
da produção). A produção regular não tem custo por unidade adicional (já está no
salário); a hora extra é paga por unidade. O custo de material por unidade é tratado
como constante (produção anual ~ demanda anual) e excluído da função-objetivo, prática
padrão em planejamento agregado. Todos os custos em BRL.

Calibração validada em `valida_premissas.py`: nenhuma estratégia pura domina. O plano
misto (PL) vence tanto a estratégia de nível (força constante, estoque caro) quanto a
de perseguição (sem estoque, mas contratação/demissão e atraso no pico). Racional
completo em `docs/00_premissas.md`.
"""
from __future__ import annotations

import numpy as np

HORIZONTE_MESES: int = 12

# --- Demanda -----------------------------------------------------------------
DEMANDA = {
    "nivel_medio_mensal": 17000,   # un/mês
    "amplitude_sazonal": 0.46,     # fração +/- sobre o nível médio
    "mes_pico": 7,                 # mês do horizonte com pico (verão)
    "tendencia_ano": 0.06,         # fração ao ano (crescimento)
    "ruido_cv": 0.08,              # CV do erro de previsão (fração da demanda)
    "distribuicao_erro": "normal",
}

# --- Capacidade / força de trabalho ------------------------------------------
CAPACIDADE = {
    "produtividade_por_trab_mes": 180,  # un/trab/mês (capacidade regular)
    "trabalhadores_inicial": 88,        # trab
    "estoque_inicial": 2000,            # un
    "teto_hora_extra": 0.12,            # fração da capacidade regular
    "max_contratacoes_mes": 4,          # trab/mês
    "max_demissoes_mes": 4,             # trab/mês
}

# --- Custos (BRL) - modelo de custo-relevante --------------------------------
CUSTOS = {
    "salario_mensal": 3500.0,   # R$/trabalhador/mês (com encargos), pago sempre
    "hora_extra_un": 30.0,      # R$/unidade produzida em hora extra
    "estoque_mes": 6.0,         # R$/un/mês mantida em estoque
    "contratacao": 2500.0,      # R$/trabalhador contratado
    "demissao": 5000.0,         # R$/trabalhador demitido
    "backorder": 50.0,          # R$/un/mês de atraso (falta atendida com atraso)
}

# --- Nível de serviço --------------------------------------------------------
NIVEL_SERVICO_ALVO: float = 0.95   # z ~ 1.645 (Normal padrão)
Z_NIVEL_SERVICO: float = 1.645


def demanda_esperada() -> np.ndarray:
    """Série de demanda esperada (sem ruído), un/mês, para t = 1..12.

    D(t) = nível * (1 + amp * sin(2π(t - pico)/12 + π/2)) * (1 + tend * (t-1)/12)

    Vale no mês 1 (início do ano de planejamento, baixa estação) e pico no
    mês `mes_pico`; tendência linear de 0% em t=1 a ~+5,5% em t=12.
    """
    t = np.arange(1, HORIZONTE_MESES + 1)
    nivel = DEMANDA["nivel_medio_mensal"]
    amp = DEMANDA["amplitude_sazonal"]
    pico = DEMANDA["mes_pico"]
    tend = DEMANDA["tendencia_ano"]
    sazonal = 1.0 + amp * np.sin(2 * np.pi * (t - pico) / 12 + np.pi / 2)
    trend = 1.0 + tend * (t - 1) / 12
    return nivel * sazonal * trend


def demanda_simulada(rng: np.random.Generator) -> np.ndarray:
    """Demanda com erro multiplicativo Normal(0, ruido_cv^2), reprodutível."""
    base = demanda_esperada()
    eps = rng.normal(0.0, DEMANDA["ruido_cv"], size=base.shape)
    return base * (1.0 + eps)
