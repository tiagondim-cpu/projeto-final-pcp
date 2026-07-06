"""Validação de não-trivialidade das premissas (Fase 0) - modelo de custo-relevante.

Confirma, de forma independente e reprodutível, que o caso é NÃO-TRIVIAL: o plano
misto (PL) vence as DUAS estratégias puras, que falham por motivos distintos.

Função-objetivo (custo-relevante de planejamento agregado):
    min  sum_t ( cW*W_t + cO*O_t + cI*I_t + cH*H_t + cF*F_t + cB*B_t )

As três estratégias são o MESMO PL com restrições adicionais:
  - misto:       tudo livre (sujeito aos limites operacionais);
  - nivel:       força de trabalho constante (W_t = W_1);
  - perseguicao: estoque de antecipação nulo (I_t = 0).

Uso: python src/valida_premissas.py
Código de saída 0 se a instância for não-trivial; 1 caso contrário.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pulp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from parametros import (  # noqa: E402
    CAPACIDADE,
    CUSTOS,
    HORIZONTE_MESES,
    demanda_esperada,
)

T = HORIZONTE_MESES
prod = CAPACIDADE["produtividade_por_trab_mes"]
W0 = CAPACIDADE["trabalhadores_inicial"]
I0 = CAPACIDADE["estoque_inicial"]
teto = CAPACIDADE["teto_hora_extra"]
maxH = CAPACIDADE["max_contratacoes_mes"]
maxF = CAPACIDADE["max_demissoes_mes"]
cW = CUSTOS["salario_mensal"]
cO = CUSTOS["hora_extra_un"]
cI = CUSTOS["estoque_mes"]
cH = CUSTOS["contratacao"]
cF = CUSTOS["demissao"]
cB = CUSTOS["backorder"]

D = demanda_esperada()


def resolve(modo: str):
    m = pulp.LpProblem(f"PAP_{modo}", pulp.LpMinimize)
    ix = range(1, T + 1)
    P = {t: pulp.LpVariable(f"P{t}", lowBound=0) for t in ix}
    O = {t: pulp.LpVariable(f"O{t}", lowBound=0) for t in ix}
    W = {t: pulp.LpVariable(f"W{t}", lowBound=0) for t in ix}
    H = {t: pulp.LpVariable(f"H{t}", lowBound=0) for t in ix}
    F = {t: pulp.LpVariable(f"F{t}", lowBound=0) for t in ix}
    I = {t: pulp.LpVariable(f"I{t}", lowBound=0) for t in ix}
    B = {t: pulp.LpVariable(f"B{t}", lowBound=0) for t in ix}

    m += pulp.lpSum(cW * W[t] + cO * O[t] + cI * I[t]
                    + cH * H[t] + cF * F[t] + cB * B[t] for t in ix)

    for t in ix:
        Iprev = I0 if t == 1 else I[t - 1]
        Bprev = 0 if t == 1 else B[t - 1]
        Wprev = W0 if t == 1 else W[t - 1]
        m += I[t] - B[t] == Iprev - Bprev + P[t] + O[t] - D[t - 1]
        m += W[t] == Wprev + H[t] - F[t]
        m += P[t] <= prod * W[t]
        m += O[t] <= teto * prod * W[t]
        m += H[t] <= maxH
        m += F[t] <= maxF
    m += B[T] == 0  # servir toda a demanda até o fim do horizonte

    if modo == "nivel":
        for t in ix:
            if t > 1:
                m += W[t] == W[1]
    elif modo == "perseguicao":
        for t in ix:
            m += I[t] == 0

    m.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[m.status]
    if status != "Optimal":
        return status, float("nan"), {}, {}
    val = {nome: {t: v[t].value() for t in ix}
           for nome, v in (("P", P), ("O", O), ("W", W),
                           ("H", H), ("F", F), ("I", I), ("B", B))}
    custo = {
        "salario": cW * sum(val["W"].values()),
        "hora_extra": cO * sum(val["O"].values()),
        "estoque": cI * sum(val["I"].values()),
        "contratacao": cH * sum(val["H"].values()),
        "demissao": cF * sum(val["F"].values()),
        "atraso": cB * sum(val["B"].values()),
    }
    return status, pulp.value(m.objective), custo, val


def main() -> int:
    print("=== Validacao de nao-trivialidade (Fase 0, modelo de custo-relevante) ===\n")

    cap_reg = prod * W0
    cap_he = cap_reg * (1 + teto)
    print(f"Demanda esperada (un/mes): {np.round(D).astype(int).tolist()}")
    print(f"Vale={D.min():.0f} (mes {int(D.argmin()) + 1})  "
          f"Pico={D.max():.0f} (mes {int(D.argmax()) + 1})  "
          f"Media={D.mean():.0f}  Anual={D.sum():.0f}")
    print(f"Cap. regular inicial = {cap_reg:.0f} un/mes | com HE = {cap_he:.0f} un/mes")
    meses_acima = int((D > cap_reg).sum())
    ok_pico = D.max() > cap_he
    print(f"Meses acima da cap. regular: {meses_acima}/12 | "
          f"pico supera cap. com HE? {ok_pico}\n")

    res = {}
    for modo in ("misto", "nivel", "perseguicao"):
        status, total, custo, val = resolve(modo)
        res[modo] = (status, total, custo, val)
        print(f"[{modo:11s}] status={status:8s} total=R$ {total:,.0f}")
        print("              " + "  ".join(f"{k}=R$ {v:,.0f}" for k, v in custo.items()))
        if val:
            W_ = [round(val["W"][t]) for t in range(1, T + 1)]
            print(f"              W[{min(W_)}-{max(W_)}]  "
                  f"contratacoes={sum(val['H'].values()):.0f}  "
                  f"demissoes={sum(val['F'].values()):.0f}  "
                  f"estoque_max={max(val['I'].values()):.0f}  "
                  f"atraso_max={max(val['B'].values()):.0f}")

    c_misto = res["misto"][1]
    gap_niv = (res["nivel"][1] - c_misto) / c_misto
    gap_per = (res["perseguicao"][1] - c_misto) / c_misto

    print("\n--- Plano MISTO recomendado (mes 1..12) ---")
    v = res["misto"][3]
    for nome in ("W", "P", "O", "I", "B", "H", "F"):
        print(f"{nome:>2}:", [round(v[nome][t]) for t in range(1, T + 1)])

    print("\n--- Conclusao ---")
    print(f"Custo misto  = R$ {c_misto:,.0f}")
    print(f"Gap nivel        = {gap_niv * 100:5.2f}%  (R$ {res['nivel'][1] - c_misto:,.0f} a mais)")
    print(f"Gap perseguicao  = {gap_per * 100:5.2f}%  (R$ {res['perseguicao'][1] - c_misto:,.0f} a mais)")

    domina = (c_misto <= res["nivel"][1] + 1) and (c_misto <= res["perseguicao"][1] + 1)
    ambos = (0.02 <= gap_niv <= 0.35) and (0.02 <= gap_per <= 0.35)
    estresse = (meses_acima >= 4) and ok_pico
    nao_trivial = domina and ambos and estresse
    print(f"\nMisto <= puras? {domina} | ambos os gaps em [2%,35%]? {ambos} | "
          f"capacidade estressada? {estresse}")
    print("RESULTADO:", "NAO-TRIVIAL (OK)" if nao_trivial else "REVISAR PARAMETROS")
    return 0 if nao_trivial else 1


if __name__ == "__main__":
    raise SystemExit(main())
