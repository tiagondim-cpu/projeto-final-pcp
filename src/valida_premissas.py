"""Validação de não-trivialidade das premissas (Fase 0).

Usa `src/modelo.py` como fonte única do PL. Confirma que o plano misto vence as
duas estratégias puras (nível e perseguição), que falham por motivos distintos.

Uso: python src/valida_premissas.py
Código de saída 0 se a instância for não-trivial; 1 caso contrário.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from parametros import CAPACIDADE, demanda_esperada  # noqa: E402
from modelo import resolve_pap  # noqa: E402

D = demanda_esperada()
prod = CAPACIDADE["produtividade_por_trab_mes"]
W0 = CAPACIDADE["trabalhadores_inicial"]
teto = CAPACIDADE["teto_hora_extra"]


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

    res = {modo: resolve_pap(D, modo) for modo in ("misto", "nivel", "perseguicao")}
    for modo, r in res.items():
        print(f"[{modo:11s}] status={r.status:8s} total=R$ {r.custo_total:,.0f}")
        print("              " + "  ".join(f"{k}=R$ {x:,.0f}" for k, x in r.custo.items()))
        W_ = [round(w) for w in r.plano["W"]]
        print(f"              W[{min(W_)}-{max(W_)}]  "
              f"contratacoes={sum(r.plano['H']):.0f}  "
              f"demissoes={sum(r.plano['F']):.0f}  "
              f"estoque_max={max(r.plano['I']):.0f}  "
              f"atraso_max={max(r.plano['B']):.0f}")

    c_misto = res["misto"].custo_total
    gap_niv = (res["nivel"].custo_total - c_misto) / c_misto
    gap_per = (res["perseguicao"].custo_total - c_misto) / c_misto

    print("\n--- Plano MISTO recomendado (mes 1..12) ---")
    p = res["misto"].plano
    for nome in ("W", "P", "O", "I", "B", "H", "F"):
        print(f"{nome:>2}:", [round(x) for x in p[nome]])

    print("\n--- Conclusao ---")
    print(f"Custo misto  = R$ {c_misto:,.0f}")
    print(f"Gap nivel        = {gap_niv * 100:5.2f}%  "
          f"(R$ {res['nivel'].custo_total - c_misto:,.0f} a mais)")
    print(f"Gap perseguicao  = {gap_per * 100:5.2f}%  "
          f"(R$ {res['perseguicao'].custo_total - c_misto:,.0f} a mais)")

    domina = (c_misto <= res["nivel"].custo_total + 1) and (c_misto <= res["perseguicao"].custo_total + 1)
    ambos = (0.02 <= gap_niv <= 0.35) and (0.02 <= gap_per <= 0.35)
    estresse = (meses_acima >= 4) and ok_pico
    nao_trivial = domina and ambos and estresse
    print(f"\nMisto <= puras? {domina} | ambos os gaps em [2%,35%]? {ambos} | "
          f"capacidade estressada? {estresse}")
    print("RESULTADO:", "NAO-TRIVIAL (OK)" if nao_trivial else "REVISAR PARAMETROS")
    return 0 if nao_trivial else 1


if __name__ == "__main__":
    raise SystemExit(main())
