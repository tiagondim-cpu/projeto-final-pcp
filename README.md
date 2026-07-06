# Projeto Final de PCP - Planejamento Agregado da Produção

Projeto individual da disciplina Planejamento e Controle da Produção (EPR/FT/UnB),
Prof. João Gabriel de Moraes Souza.

## Tema

**Eixo central:** Planejamento Agregado da Produção resolvido por Programação Linear (horizonte de 12 meses).
**Integrações obrigatórias:**
- Previsão de Demanda (Holt-Winters / SARIMA) alimentando a demanda do plano.
- Gestão de Estoques e Nível de Serviço (estoque de segurança dimensionado pelo erro de previsão; análise custo x serviço).

A saída do modelo é uma decisão operacional: quanto produzir (regular e extra), quanto contratar/demitir e quanto estocar em cada mês, minimizando o custo total sob capacidade e nível de serviço-alvo.

## Estrutura do repositório

```
projeto_final/
├── README.md
├── requirements.txt        # dependências com versões fixadas (reprodutibilidade)
├── .gitignore
├── src/
│   ├── config.py           # SEED global, gerador aleatório, caminhos
│   └── parametros.py        # tabela de premissas em código (fonte única da verdade)
├── notebooks/              # notebook principal (pipeline ponta a ponta)
├── data/
│   ├── raw/                # dados gerados/brutos (versionados)
│   └── processed/          # dados tratados
├── docs/
│   └── 00_premissas.md     # contexto do caso e tabela de premissas
└── reports/               # relatório PDF e notebook exportado em HTML
```

## Configuração do ambiente

```bash
python -m pip install -r requirements.txt
```

Requer Python 3.11+ (desenvolvido em 3.13).

## Reprodutibilidade (critério C3)

- Semente global única em `src/config.py` (`SEED = 42`); toda aleatoriedade usa `get_rng()`.
- Parâmetros do caso centralizados em `src/parametros.py` (nada de números soltos no notebook).
- Dados gerados são salvos em `data/raw/` e versionados.
- Dependências com versões fixadas em `requirements.txt`.
- Notebook exportado para HTML com `jupyter nbconvert --to html` (entregável obrigatório).

## Como reproduzir os resultados

1. `python -m pip install -r requirements.txt`
2. Abrir e executar `notebooks/` do topo ao fim (Run All).
3. Exportar: `jupyter nbconvert --to html notebooks/<nome>.ipynb --output-dir reports/`
