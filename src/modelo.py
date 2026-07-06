"""Modelo de Planejamento Agregado da Produção - PL de custo-relevante.

Fonte única do modelo de otimização (usada pelo notebook e pela validação).

Função-objetivo:
    min  sum_t ( cW*W_t + cO*O_t + cI*I_t + cH*H_t + cF*F_t + cB*B_t )

Sujeito a, para cada mês t:
    I_t - B_t = I_{t-1} - B_{t-1} + P_t + O_t - D_t     (balanço de estoque)   [bal_t]
    W_t       = W_{t-1} + H_t - F_t                     (força de trabalho)
    P_t      <= prod * W_t                              (capacidade regular)   [cap_t]
    O_t      <= teto * prod * W_t                       (teto de hora extra)   [ot_t]
    H_t <= maxH,  F_t <= maxF                           (limites de ajuste)
    I_t      >= SS_t                                    (estoque de segurança, opcional)
    B_T = 0                                             (atender toda a demanda)
    variáveis >= 0

Estratégias (modo): "misto", "nivel" (W_t = W_1), "perseguicao" (I_t = 0).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pulp

from parametros import CAPACIDADE, CUSTOS

_VARS = ("W", "P", "O", "I", "B", "H", "F")


@dataclass
class ResultadoPAP:
    """Resultado de um plano agregado."""
    modo: str
    status: str
    custo_total: float
    custo: dict = field(default_factory=dict)      # decomposição por rubrica
    plano: dict = field(default_factory=dict)      # arrays (listas de T meses)
    duais: dict = field(default_factory=dict)      # preços-sombra por restrição


def resolve_pap(demanda, modo: str = "misto", *,
                W0=None, I0=None, custos=None, capacidade=None,
                estoque_seguranca=None) -> ResultadoPAP:
    """Resolve o planejamento agregado para uma série de demanda.

    `estoque_seguranca`: vetor (len T) de estoque mínimo por mês (fronteira
    custo x nível de serviço). Sobrescritas de `custos`/`capacidade` e dos estados
    iniciais permitem análise de sensibilidade sem mexer nos padrões.
    """
    cap = {**CAPACIDADE, **(capacidade or {})}
    cst = {**CUSTOS, **(custos or {})}
    D = [float(x) for x in demanda]
    T = len(D)

    prod = cap["produtividade_por_trab_mes"]
    W0 = cap["trabalhadores_inicial"] if W0 is None else W0
    I0 = cap["estoque_inicial"] if I0 is None else I0
    teto = cap["teto_hora_extra"]
    maxH = cap["max_contratacoes_mes"]
    maxF = cap["max_demissoes_mes"]
    cW, cO, cI = cst["salario_mensal"], cst["hora_extra_un"], cst["estoque_mes"]
    cH, cF, cB = cst["contratacao"], cst["demissao"], cst["backorder"]

    m = pulp.LpProblem(f"PAP_{modo}", pulp.LpMinimize)
    ix = range(1, T + 1)
    v = {nome: {t: pulp.LpVariable(f"{nome}{t}", lowBound=0) for t in ix}
         for nome in _VARS}
    W, P, O, I, B, H, F = (v[n] for n in _VARS)

    m += pulp.lpSum(cW * W[t] + cO * O[t] + cI * I[t]
                    + cH * H[t] + cF * F[t] + cB * B[t] for t in ix)

    for t in ix:
        Iprev = I0 if t == 1 else I[t - 1]
        Bprev = 0 if t == 1 else B[t - 1]
        Wprev = W0 if t == 1 else W[t - 1]
        m += (I[t] - B[t] == Iprev - Bprev + P[t] + O[t] - D[t - 1], f"bal_{t}")
        m += (W[t] == Wprev + H[t] - F[t], f"work_{t}")
        m += (P[t] <= prod * W[t], f"cap_{t}")
        m += (O[t] <= teto * prod * W[t], f"ot_{t}")
        m += (H[t] <= maxH, f"maxH_{t}")
        m += (F[t] <= maxF, f"maxF_{t}")
        if estoque_seguranca is not None:
            m += (I[t] >= float(estoque_seguranca[t - 1]), f"ss_{t}")
    m += (B[T] == 0, "atende_tudo")

    if modo == "nivel":
        for t in ix:
            if t > 1:
                m += (W[t] == W[1], f"nivel_{t}")
    elif modo == "perseguicao":
        for t in ix:
            m += (I[t] == 0, f"pers_{t}")
    elif modo != "misto":
        raise ValueError(f"modo desconhecido: {modo!r}")

    m.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[m.status]

    if status != "Optimal":
        return ResultadoPAP(modo, status, float("nan"))

    plano = {n: [round(v[n][t].value(), 3) for t in ix] for n in _VARS}
    custo = {
        "salario": cW * sum(v["W"][t].value() for t in ix),
        "hora_extra": cO * sum(v["O"][t].value() for t in ix),
        "estoque": cI * sum(v["I"][t].value() for t in ix),
        "contratacao": cH * sum(v["H"][t].value() for t in ix),
        "demissao": cF * sum(v["F"][t].value() for t in ix),
        "atraso": cB * sum(v["B"][t].value() for t in ix),
    }

    def _pi(nome):
        con = m.constraints.get(nome)
        return None if con is None or con.pi is None else round(con.pi, 4)

    duais = {
        "capacidade": {t: _pi(f"cap_{t}") for t in ix},   # valor marginal da cap. regular
        "balanco": {t: _pi(f"bal_{t}") for t in ix},      # custo marginal de +1 un de demanda
        "hora_extra": {t: _pi(f"ot_{t}") for t in ix},    # valor marginal do teto de HE
    }
    return ResultadoPAP(modo, status, pulp.value(m.objective), custo, plano, duais)
