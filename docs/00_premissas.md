# Premissas do Caso - Planejamento Agregado da Produção

> Documento base da Fase 0. Todos os números aqui são a fonte da verdade,
> espelhados em `src/parametros.py` e verificados por `src/valida_premissas.py`.

## 1. Contexto produtivo

Fabricante brasileiro de **ventiladores domésticos** (linha branca de pequeno porte),
com o portfólio agregado em um produto equivalente. Produção *make-to-stock* com
força de trabalho ajustável. A demanda é fortemente sazonal, com pico no verão.

O ano de planejamento começa na **baixa estação** (mês 1 = inverno), sobe até o
**pico de verão no mês 7** e volta a cair, fechando o horizonte de 12 meses em baixa.
Essa fase (vale no início, pico no meio) é o que cria a decisão interessante: é
preciso decidir *quando* antecipar produção em estoque e *quanto* variar a força de
trabalho para atravessar o pico.

## 2. Decisão de PCP

Definir, para cada um dos 12 meses, **quanto produzir** (regular e em hora extra),
**qual o tamanho da força de trabalho** (contratar/demitir) e **quanto manter em
estoque**, de modo a **minimizar o custo total relevante**, atendendo à demanda com
nível de serviço-alvo e respeitando a capacidade.

## 3. Modelo de custo (custo-relevante de planejamento agregado)

Seguindo a formulação padrão (Nahmias; Hopp & Spearman), o custo de mão de obra é o
**salário por trabalhador por mês**, pago independentemente da produção. A produção
regular não tem custo unitário adicional (já está no salário); a **hora extra** é paga
por unidade. O **custo de material por unidade** é tratado como constante (a produção
anual é aproximadamente igual à demanda anual) e, por isso, **excluído da função-
objetivo** - prática padrão, pois não altera a decisão. Os custos que importam para a
decisão são: salário, hora extra, estoque, contratação, demissão e atraso.

## 4. Tabela de premissas

### 4.1 Demanda

| Parâmetro | Valor | Unidade |
|---|---|---|
| Nível médio mensal | 17.000 | un/mês |
| Amplitude sazonal | +/- 46 | % sobre o nível médio |
| Mês de pico | 7 | mês do horizonte (verão) |
| Tendência | +6 | % ao ano |
| Ruído (CV do erro de previsão) | 8 | % da demanda prevista |
| Distribuição do erro | Normal | erro multiplicativo i.i.d. |

**Série esperada (sem ruído), un/mês:**
9.180, 10.279, 13.221, 17.255, 21.328, 24.367, **25.565**, 24.604, 21.746, 17.765, 13.745, 10.790.
Vale no mês 1 (9.180), pico no mês 7 (25.565). Média ~17.487 un/mês; total anual ~209.845 un.

Fórmula (t = 1..12):
`D(t) = 17000 * (1 + 0,46 * sin(2π(t-7)/12 + π/2)) * (1 + 0,06 * (t-1)/12)`

### 4.2 Capacidade e força de trabalho

| Parâmetro | Valor | Unidade |
|---|---|---|
| Produtividade por trabalhador | 180 | un/trab/mês |
| Trabalhadores iniciais | 88 | trab |
| Estoque inicial | 2.000 | un |
| Teto de hora extra | 12 | % da capacidade regular |
| Máximo de contratações | 4 | trab/mês |
| Máximo de demissões | 4 | trab/mês |

Capacidade regular inicial = 180 x 88 = **15.840 un/mês**; com hora extra máxima =
**17.741 un/mês**. O pico de 25.565 un supera a capacidade regular em 61% e fica
**acima até do teto com hora extra** - logo, atravessar o pico exige antecipar produção
em estoque e/ou ampliar a força de trabalho ao longo dos meses anteriores. 7 dos 12
meses excedem a capacidade regular inicial.

### 4.3 Custos (BRL)

| Parâmetro | Valor | Unidade | Racional |
|---|---|---|---|
| Salário | 3.500 | R$/trab/mês | remuneração + encargos de um montador de linha branca |
| Hora extra | 30 | R$/un | ~1,5x o custo unitário de mão de obra regular (R$ 3.500/180 ≈ 19,4) |
| Estoque | 6 | R$/un/mês | armazenagem + capital de um bem durável de baixo valor |
| Contratação | 2.500 | R$/trab | recrutamento, exames, treinamento, EPIs |
| Demissão | 5.000 | R$/trab | aviso prévio, multa de 40% do FGTS, verbas rescisórias |
| Atraso (backorder) | 50 | R$/un/mês | penalidade de ruptura; ~8x o custo de estoque, desincentiva sem proibir |

## 5. Nível de serviço e ligação com a previsão

Nível de serviço-alvo de **95%** (z = 1,645 na Normal padrão). O erro de previsão
(CV = 8%) alimenta o **estoque de segurança**: no pico, sigma ≈ 0,08 x 25.565 ≈ 2.045 un,
logo SS ≈ 1,645 x 2.045 ≈ **3.364 un**. Esse é o fio que integra Previsão de Demanda
(Fase 2) -> Gestão de Estoque/Nível de Serviço (Fase 5) -> Planejamento Agregado. A
análise de Monte Carlo (Fase 5) propagará esse erro para custo e serviço.

## 6. Verificação de não-trivialidade

Verificação independente por Programação Linear (`src/valida_premissas.py`), não por
conta de guardanapo. As três estratégias são o mesmo PL com restrições distintas
(nível: força de trabalho constante; perseguição: estoque de antecipação nulo).

| Estratégia | Custo total | Gap vs misto | Modo de falha |
|---|---|---|---|
| **Misto (ótimo do PL)** | R$ 4.915.334 | - | equilibra estoque, força de trabalho e hora extra |
| Nível | R$ 5.170.426 | +5,2% (R$ 255.092) | estoque caro (máx 24.874 un; R$ 765k de estoque) |
| Perseguição | R$ 5.661.200 | +15,2% (R$ 745.866) | contratação/demissão + atraso R$ 603k (não rampa no pico) |

**Conclusão:** nenhuma estratégia pura domina. O nível paga estoque em excesso; a
perseguição paga churn de mão de obra e atraso porque os limites de +/-4 trab/mês
impedem acompanhar o salto sazonal (~68 trabalhadores entre vale e pico). O plano
misto pré-constrói estoque na baixa, rampa moderadamente a força de trabalho e usa
hora extra apenas no pico, vencendo ambas. Isso garante que a comparação de
estratégias e a análise de sensibilidade sejam substantivas (o PL "ganha o pão").

## 7. Plano misto de referência (ótimo determinístico)

| Mês | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Demanda | 9180 | 10279 | 13221 | 17255 | 21328 | 24367 | 25565 | 24604 | 21746 | 17765 | 13745 | 10790 |
| Trabalhadores | 88 | 88 | 92 | 96 | 100 | 104 | 104 | 104 | 104 | 100 | 96 | 96 |
| Prod. regular | 13999 | 15840 | 16560 | 17280 | 18000 | 18720 | 18720 | 18720 | 18720 | 17765 | 13744 | 10790 |
| Hora extra | 0 | 0 | 0 | 0 | 0 | 2246 | 2246 | 2246 | 2246 | 0 | 0 | 0 |
| Estoque | 6819 | 12380 | 15720 | 15745 | 12416 | 9016 | 4418 | 780 | 0 | 0 | 0 | 0 |

Este plano é o ponto de partida determinístico; as Fases 4-5 farão a comparação formal
de cenários, a análise de sensibilidade e a propagação do erro de previsão.
