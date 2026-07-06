"""Gera as figuras do relatorio (PNGs) a partir do modelo e dos dados.

Reproduz as analises do notebook e salva figuras em reports/figuras/.
Uso: python tools/gera_figuras.py
"""
from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from parametros import (demanda_esperada, serie_historica, CUSTOS, CAPACIDADE,
                        HORIZONTE_MESES, NIVEL_SERVICO_ALVO, Z_NIVEL_SERVICO)
from config import get_rng
from modelo import resolve_pap
from estilo import aplicar_estilo, C_REGULAR, C_EXTRA, C_ESTOQUE, C_DESTAQUE, C_REF

FIG = ROOT / "reports" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)
aplicar_estilo()
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

meses = np.arange(1, HORIZONTE_MESES + 1)
D = demanda_esperada()
h = HORIZONTE_MESES


def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(FIG / nome, bbox_inches="tight")
    plt.close(fig)
    print("fig:", nome)


# --- 1. Demanda ---
rng = get_rng()
D_sim = D * (1 + rng.normal(0, 0.08, size=len(D)))
cap_reg = CAPACIDADE["produtividade_por_trab_mes"] * CAPACIDADE["trabalhadores_inicial"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(meses, D, "o-", label="Esperada (forecast adotado)")
ax.plot(meses, D_sim, "s--", alpha=0.8, label="Simulada (ruido 8%)")
ax.axhline(cap_reg, color=C_REF, ls=":", label=f"Cap. regular inicial ({cap_reg:.0f})")
ax.set(xlabel="Mes", ylabel="Demanda (un)", title="Demanda mensal do ano de planejamento")
ax.legend(fontsize=8)
salvar(fig, "fig01_demanda.png")

# --- 2. Backtest de previsao ---
serie = pd.Series(serie_historica(5, get_rng()))
train, test = serie.iloc[:-h], serie.iloc[-h:]
y_tr = train.values.astype(float)
prev = {}
prev["Media Movel(3)"] = np.repeat(pd.Series(y_tr).rolling(3).mean().iloc[-1], h)
prev["SES"] = SimpleExpSmoothing(y_tr).fit().forecast(h)
prev["Holt-Winters"] = ExponentialSmoothing(y_tr, trend="add", seasonal="mul",
                                             seasonal_periods=12).fit().forecast(h)
prev["SARIMA"] = np.asarray(SARIMAX(y_tr, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12),
                                    enforce_stationarity=False,
                                    enforce_invertibility=False).fit(disp=False).forecast(h))
mape = lambda a, b: float(np.mean(np.abs((np.asarray(a) - np.asarray(b)) / np.asarray(a))) * 100)
tab = pd.DataFrame({n: {"MAE": mean_absolute_error(test.values, v),
                        "RMSE": root_mean_squared_error(test.values, v),
                        "MAPE": mape(test.values, v)} for n, v in prev.items()}).T.sort_values("RMSE")
print("\n== Metricas de previsao (holdout) ==")
print(tab.round(1).to_string())
melhor = tab.index[0]
cv_erro = tab.loc[melhor, "RMSE"] / test.mean()
print(f"melhor={melhor} | cv_erro={cv_erro*100:.1f}%")

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(range(len(y_tr)), y_tr, color="gray", alpha=0.5, label="Treino")
tx = range(len(y_tr), len(y_tr) + h)
ax.plot(tx, test.values, "k-o", label="Real (holdout)")
for n, v in prev.items():
    ax.plot(tx, v, "--", label=n)
ax.axvline(len(y_tr) - 0.5, color="red", ls=":")
ax.set(xlabel="Mes (indice)", ylabel="Demanda (un)", title="Backtest: previsao vs real no holdout")
ax.legend(fontsize=8, ncol=2)
salvar(fig, "fig02_backtest.png")

# --- 3. Plano misto ---
res = resolve_pap(D, "misto")
P = np.array(res.plano["P"]); O = np.array(res.plano["O"]); I = np.array(res.plano["I"])
fig, ax1 = plt.subplots(figsize=(8, 4))
ax1.bar(meses, P, color=C_REGULAR, label="Producao regular")
ax1.bar(meses, O, bottom=P, color=C_EXTRA, label="Hora extra")
ax1.plot(meses, D, "k-o", label="Demanda")
ax1.set(xlabel="Mes", ylabel="Unidades", title="Plano agregado misto: producao vs demanda")
ax2 = ax1.twinx(); ax2.plot(meses, I, "--^", color=C_ESTOQUE, alpha=0.85, label="Estoque"); ax2.set_ylabel("Estoque (un)")
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
salvar(fig, "fig03_plano_misto.png")

# --- 4. Cenarios ---
estr = {m: resolve_pap(D, m) for m in ("misto", "nivel", "perseguicao")}
print("\n== Custo por estrategia ==")
for m, r in estr.items():
    print(f"  {m:11s} R$ {r.custo_total:,.0f}  gap={(r.custo_total/estr['misto'].custo_total-1)*100:+.1f}%")
cats = ["salario", "hora_extra", "estoque", "contratacao", "demissao", "atraso"]
x = list(estr.keys())
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
bottom = np.zeros(len(x))
for cat in cats:
    vals = np.array([estr[m].custo[cat] for m in x]); a1.bar(x, vals, bottom=bottom, label=cat); bottom += vals
a1.set(ylabel="R$", title="Decomposicao de custo por estrategia"); a1.legend(fontsize=7, ncol=2)
for m, r in estr.items():
    a2.plot(meses, r.plano["I"], marker="o", label=m)
a2.set(xlabel="Mes", ylabel="Estoque (un)", title="Trajetoria de estoque"); a2.legend(fontsize=8)
salvar(fig, "fig04_cenarios.png")

fig, ax = plt.subplots(figsize=(8, 4))
for m, r in estr.items():
    ax.plot(meses, r.plano["W"], marker="o", label=m)
ax.set(xlabel="Mes", ylabel="Trabalhadores", title="Trajetoria da forca de trabalho"); ax.legend(fontsize=8)
salvar(fig, "fig05_forca_trabalho.png")

# --- 5. Precos-sombra ---
dcap = res.duais["capacidade"]
valor = [(-dcap[t] if dcap[t] is not None else 0.0) for t in meses]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(meses, valor, color=C_DESTAQUE)
ax.set(xlabel="Mes", ylabel="R$ por unidade de capacidade",
       title="Preco-sombra da capacidade regular (economia por +1 un)")
salvar(fig, "fig06_precos_sombra.png")
print("\n== Precos-sombra capacidade ==", [round(v) for v in valor])

# --- 6. Tornado ---
base = res.custo_total; delta = 0.20
linhas = []
for p in ["salario_mensal", "hora_extra_un", "estoque_mes", "contratacao", "demissao", "backorder"]:
    lo = (resolve_pap(D, "misto", custos={p: CUSTOS[p]*(1-delta)}).custo_total/base-1)*100
    hi = (resolve_pap(D, "misto", custos={p: CUSTOS[p]*(1+delta)}).custo_total/base-1)*100
    linhas.append((p, lo, hi))
linhas.append(("demanda", (resolve_pap(D*(1-delta), "misto").custo_total/base-1)*100,
               (resolve_pap(D*(1+delta), "misto").custo_total/base-1)*100))
linhas.sort(key=lambda r: abs(r[2]-r[1]))
fig, ax = plt.subplots(figsize=(8, 4.5))
for i, (n, lo, hi) in enumerate(linhas):
    ax.barh(i, hi-lo, left=min(lo, hi), color=C_REGULAR)
ax.set_yticks(range(len(linhas))); ax.set_yticklabels([r[0] for r in linhas])
ax.axvline(0, color="k", lw=0.8)
ax.set(xlabel="Variacao do custo total (%) para parametro +/- 20%", title="Tornado: sensibilidade do custo otimo")
salvar(fig, "fig07_tornado.png")

# --- 7. Fronteira ---
niveis = [0.80, 0.85, 0.90, 0.95, 0.975, 0.99]
front = [(sl*100, resolve_pap(D, "misto", estoque_seguranca=norm.ppf(sl)*cv_erro*D).custo_total) for sl in niveis]
front = pd.DataFrame(front, columns=["sl", "custo"])
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(front["sl"], front["custo"]/1e6, "o-", color=C_DESTAQUE)
ax.set(xlabel="Nivel de servico (%)", ylabel="Custo total (R$ milhoes)", title="Fronteira custo x nivel de servico")
salvar(fig, "fig08_fronteira.png")
print("\n== Fronteira ==")
for _, r in front.iterrows():
    print(f"  {r['sl']:.0f}%: R$ {r['custo']:,.0f} (+{(r['custo']/base-1)*100:.1f}%)")

# --- 8. Monte Carlo ---
def simula(plan, N=2000):
    pt = np.array(plan.plano["P"]) + np.array(plan.plano["O"])
    fixo = plan.custo["salario"] + plan.custo["hora_extra"] + plan.custo["contratacao"] + plan.custo["demissao"]
    cI, cB = CUSTOS["estoque_mes"], CUSTOS["backorder"]; I0 = CAPACIDADE["estoque_inicial"]; rng = get_rng()
    tot = np.empty(N); fill = np.empty(N)
    for i in range(N):
        d = D * (1 + rng.normal(0, cv_erro, size=len(D))); inv = I0; hold = falta = unmet = 0.0
        for t in range(len(d)):
            inv += pt[t] - d[t]
            if inv >= 0: hold += inv
            else: unmet += -inv; falta += -inv; inv = 0.0
        tot[i] = fixo + cI*hold + cB*falta; fill[i] = 1 - unmet/d.sum()
    return tot, fill

ss95 = norm.ppf(NIVEL_SERVICO_ALVO) * cv_erro * D
plano_ss = resolve_pap(D, "misto", estoque_seguranca=ss95)
c_base, f_base = simula(res); c_ss, f_ss = simula(plano_ss)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
a1.hist(c_base/1e6, bins=40, alpha=0.6, label="Sem SS"); a1.hist(c_ss/1e6, bins=40, alpha=0.6, label="Com SS 95%")
a1.set(xlabel="Custo realizado (R$ milhoes)", ylabel="Frequencia", title="Distribuicao do custo (2000 cenarios)"); a1.legend(fontsize=8)
a2.hist(f_base*100, bins=40, alpha=0.6, label="Sem SS"); a2.hist(f_ss*100, bins=40, alpha=0.6, label="Com SS 95%")
a2.axvline(95, color="r", ls=":", label="Meta 95%")
a2.set(xlabel="Nivel de servico realizado (%)", title="Distribuicao do servico"); a2.legend(fontsize=8)
salvar(fig, "fig09_montecarlo.png")
print("\n== Monte Carlo ==")
print(f"  sem SS: custo R$ {c_base.mean():,.0f} | servico {f_base.mean():.1%} | >=95% em {(f_base>=0.95).mean():.0%}")
print(f"  com SS: custo R$ {c_ss.mean():,.0f} | servico {f_ss.mean():.1%} | >=95% em {(f_ss>=0.95).mean():.0%}")
print("\nOK figuras geradas em", FIG)
