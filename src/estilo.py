"""Identidade visual da UnB aplicada ao projeto (design system institucional).

Cores oficiais extraídas do Guia da Marca UnB: verde (Pantone 348) e azul
(Pantone 654), com apoios (lima, teal, verde-claro). Usado por figuras, notebook e
dashboard para manter a identidade visual consistente.
"""
from __future__ import annotations

# Cores institucionais da UnB
UNB = {
    "verde": "#00822E",        # primária (Pantone 348)
    "verde_escuro": "#005A1C",
    "lima": "#98C000",
    "verde_claro": "#BAD266",
    "azul": "#003A7A",         # secundária (Pantone 654)
    "azul_escuro": "#003366",
    "teal": "#00A0A7",
    "cinza": "#5B6770",
    "tinta": "#1A1A1A",
}

# Ciclo de cores para gráficos
CICLO = [UNB["verde"], UNB["azul"], UNB["lima"], UNB["teal"],
         UNB["verde_claro"], UNB["azul_escuro"]]

# Cores semânticas dos gráficos do projeto
C_REGULAR = UNB["azul"]       # produção regular
C_EXTRA = UNB["lima"]         # hora extra
C_ESTOQUE = UNB["verde"]      # estoque
C_DESTAQUE = UNB["verde"]     # barras de destaque
C_REF = "#B23A3A"             # linhas de referência (limite/meta)


def aplicar_estilo() -> None:
    """Aplica a identidade visual UnB ao matplotlib (chamar antes de plotar)."""
    import matplotlib as mpl
    mpl.rcParams.update({
        "axes.prop_cycle": mpl.cycler(color=CICLO),
        "axes.edgecolor": "#9AA0A6",
        "axes.labelcolor": UNB["tinta"],
        "axes.titlecolor": UNB["azul"],
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.color": "#E8EAED",
        "grid.linewidth": 0.7,
        "text.color": UNB["tinta"],
        "xtick.color": UNB["cinza"],
        "ytick.color": UNB["cinza"],
        "figure.facecolor": "white",
        "legend.frameon": False,
    })
