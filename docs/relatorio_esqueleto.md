# Esqueleto do Relatório Final (scaffold para o autor)

> Este arquivo é um andaime: mapeia cada seção obrigatória do enunciado aos números
> e figuras já gerados no notebook. **A redação analítica é sua** (o enunciado exige
> autoria). Use os prompts como guia e escreva com suas palavras. Alvo: 10-20 páginas.
> Todas as figuras estão em `notebooks/projeto_pcp.ipynb` (e no HTML em `reports/`).

## Números-âncora (para citar)

- **Caso:** fabricante de ventiladores, produto agregado, horizonte 12 meses, pico no mês 7.
- **Demanda esperada:** vale 9.180 (mês 1), pico 25.565 (mês 7); média ~17.487 un/mês; anual ~209.845 un.
- **Capacidade:** 180 un/trab/mês; 88 trabalhadores iniciais; cap. regular 15.840 un/mês (17.741 com hora extra). Pico excede até a capacidade com hora extra.
- **Previsão (holdout 12 meses):** SARIMA MAPE 5,4% (escolhido); Holt-Winters 6,4%; Média Móvel 28,9%; SES 34,8%. CV de erro ~8% -> estoque de segurança no pico ~3.373 un.
- **Plano misto (ótimo):** R$ 4.915.334. Nível +5,2% (R$ 255k, estoque em excesso); Perseguição +15,2% (R$ 746k, churn + atraso).
- **Preços-sombra da capacidade:** zero fora da janela de aperto; cresce ~R$ 6/mês rumo ao pico (mês 9: R$ 48/un).
- **Fronteira custo x serviço:** 80% -> +2,0%; 95% -> +3,8%; 99% -> +5,4%.
- **Monte Carlo (2000 cen.):** sem SS serviço médio 98,8% (meta 95% cumprida em 97% dos cenários); com SS 95% -> 99,2% e 99% dos cenários (+~2% de custo).
- **Recomendação:** plano misto com estoque de segurança de 95%.

---

## 1. Resumo executivo (~0,5 pág.) -> C5/C4
Escrever em 4 frases: (a) problema (quanto produzir/contratar/estocar por mês num fabricante sazonal); (b) método (previsão SARIMA + PL de planejamento agregado + Monte Carlo); (c) principal resultado (plano misto R$ 4,92M domina as puras); (d) decisão (adotar misto + SS 95%).

## 2. Contexto e formulação (~2 pág.) -> C1
- Descrever o sistema produtivo (ventiladores, sazonalidade de verão).
- Formular como DECISÃO (não descrição): objetivo, variáveis, hipóteses, restrições, KPIs.
- **Inserir:** Tabela de premissas (de `docs/00_premissas.md`, seção 4).

## 3. Dados e preparação (~2 pág.) -> C3
- Justificar dados simulados (enunciado permite; explicar o processo gerador e a semente).
- **Inserir:** Figura da demanda esperada vs simulada (notebook seção 1) e do histórico (seção 2).

## 4. Modelagem (~3 pág.) -> C2
- Previsão: descrever SES/HW/SARIMA e por que sazonais vencem (conectar à aula do professor).
- PL: apresentar função-objetivo e restrições (copiar de `src/modelo.py` docstring / plan.md 5.2).
- Definir variáveis de decisão, parâmetros, função-objetivo.

## 5. Implementação (~1,5 pág.) -> C3
- Ferramentas (Python, PuLP/CBC, statsmodels), estrutura do repositório, reprodutibilidade (seed).
- **Inserir:** link do repositório e do notebook (GitHub renderiza o .ipynb).

## 6. Resultados e cenários (~4 pág.) -> C4
- **Inserir:** tabela de métricas de previsão + gráfico de backtest (seção 2.2).
- **Inserir:** tabela de decomposição de custo das 3 estratégias + gráficos (seção 4).
- **Inserir:** preços-sombra (5.1), tornado (5.2), fronteira custo x serviço (5.3), histogramas Monte Carlo (5.4).
- Interpretar cada trade-off em linguagem gerencial.

## 7. Decisão e trade-offs (~2 pág.) -> C4
- Recomendação explícita (misto + SS 95%) com justificativa quantitativa.
- Trade-offs: custo x serviço; estoque x estabilidade de mão de obra; onde está o gargalo.
- Riscos e limitações (custos determinísticos, produto agregado, lead time fixo).

## 8. Conclusão (~1 pág.)
- Síntese; implicações para o PCP; extensões (lead time estocástico, MPS/MRP multiproduto, dashboard).
