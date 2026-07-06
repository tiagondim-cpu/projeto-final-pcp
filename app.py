"""Dashboard interativo do Planejamento Agregado da Produção (Streamlit).

Reutiliza o modelo de PL (`src/modelo.py`) para explorar, ao vivo, como a decisão
ótima e os trade-offs respondem aos parâmetros de custo, capacidade e nível de serviço.

Requer: pip install streamlit
Uso:    streamlit run app.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
from parametros import demanda_esperada, CUSTOS, CAPACIDADE  # noqa: E402
from modelo import resolve_pap  # noqa: E402
from estilo import aplicar_estilo, C_REGULAR, C_EXTRA, C_ESTOQUE, C_DESTAQUE  # noqa: E402

aplicar_estilo()

st.set_page_config(page_title="PCP - Planejamento Agregado", layout="wide")
_logo = pathlib.Path(__file__).resolve().parent / "assets" / "logo_unb.png"
if _logo.exists():
    st.logo(str(_logo))
st.title("Planejamento Agregado da Produção - Dashboard")
st.caption("Fabricante de ventiladores, horizonte de 12 meses. Ajuste os parâmetros e "
           "veja a decisão ótima e os trade-offs se atualizarem.")

D = demanda_esperada()
meses = np.arange(1, 13)

# --- Controles ---
sb = st.sidebar
sb.header("Parâmetros")
sl = sb.slider("Nível de serviço", 0.80, 0.99, 0.95, 0.01)
cv = sb.slider("CV do erro de previsão", 0.00, 0.20, 0.08, 0.01)
salario = sb.slider("Salário (R$/trab/mês)", 2000, 5000, int(CUSTOS["salario_mensal"]), 100)
estoque = sb.slider("Custo de estoque (R$/un/mês)", 2, 15, int(CUSTOS["estoque_mes"]))
contrat = sb.slider("Contratação (R$/trab)", 1000, 6000, int(CUSTOS["contratacao"]), 250)
demiss = sb.slider("Demissão (R$/trab)", 2000, 10000, int(CUSTOS["demissao"]), 250)
he = sb.slider("Hora extra (R$/un)", 15, 60, int(CUSTOS["hora_extra_un"]), 5)
cap_aj = sb.slider("Ajuste máx. de mão de obra (trab/mês)", 2, 12,
                   int(CAPACIDADE["max_contratacoes_mes"]))

custos = {"salario_mensal": salario, "estoque_mes": estoque, "contratacao": contrat,
          "demissao": demiss, "hora_extra_un": he}
capac = {"max_contratacoes_mes": cap_aj, "max_demissoes_mes": cap_aj}

estr = {m: resolve_pap(D, m, custos=custos, capacidade=capac)
        for m in ("misto", "nivel", "perseguicao")}
misto = estr["misto"]

# --- Indicadores ---
st.subheader("Custo por estratégia")
c1, c2, c3 = st.columns(3)
base = misto.custo_total
c1.metric("Misto (ótimo)", f"R$ {base:,.0f}")
c2.metric("Nível", f"R$ {estr['nivel'].custo_total:,.0f}",
          f"{(estr['nivel'].custo_total/base-1)*100:+.1f}%", delta_color="inverse")
c3.metric("Perseguição", f"R$ {estr['perseguicao'].custo_total:,.0f}",
          f"{(estr['perseguicao'].custo_total/base-1)*100:+.1f}%", delta_color="inverse")

col_a, col_b = st.columns(2)

# --- Plano misto ---
with col_a:
    st.markdown("**Plano misto: produção vs demanda**")
    P = np.array(misto.plano["P"]); O = np.array(misto.plano["O"]); I = np.array(misto.plano["I"])
    fig, ax1 = plt.subplots(figsize=(6, 3.4))
    ax1.bar(meses, P, color=C_REGULAR, label="Regular")
    ax1.bar(meses, O, bottom=P, color=C_EXTRA, label="Hora extra")
    ax1.plot(meses, D, "k-o", ms=3, label="Demanda")
    ax1.set_xlabel("Mês"); ax1.set_ylabel("un"); ax1.legend(fontsize=7)
    ax2 = ax1.twinx(); ax2.plot(meses, I, "--", color=C_ESTOQUE, label="Estoque"); ax2.set_ylabel("Estoque")
    st.pyplot(fig)

# --- Fronteira custo x serviço ---
with col_b:
    st.markdown("**Fronteira custo × nível de serviço**")
    niveis = np.arange(0.80, 0.995, 0.02)
    custos_sl = [resolve_pap(D, "misto", custos=custos, capacidade=capac,
                             estoque_seguranca=norm.ppf(s) * cv * D).custo_total
                 for s in niveis]
    fig2, ax = plt.subplots(figsize=(6, 3.4))
    ax.plot(niveis * 100, np.array(custos_sl) / 1e6, "o-", color=C_DESTAQUE)
    ax.axvline(sl * 100, color="r", ls=":", label=f"Escolhido: {sl:.0%}")
    ax.set_xlabel("Nível de serviço (%)"); ax.set_ylabel("Custo (R$ mi)"); ax.legend(fontsize=7)
    st.pyplot(fig2)

# --- Decomposição de custo ---
st.subheader("Decomposição de custo por estratégia")
dec = pd.DataFrame({m: r.custo for m, r in estr.items()}).T.round(0)
st.dataframe(dec.style.format("R$ {:,.0f}"))

# --- Plano com estoque de segurança ---
ss = norm.ppf(sl) * cv * D
plano_ss = resolve_pap(D, "misto", custos=custos, capacidade=capac, estoque_seguranca=ss)
st.info(f"Plano misto com estoque de segurança de {sl:.0%}: "
        f"R$ {plano_ss.custo_total:,.0f} "
        f"(+{(plano_ss.custo_total/base-1)*100:.1f}% vs plano sem estoque de segurança). "
        f"Estoque de segurança no pico: {ss.max():.0f} un.")
