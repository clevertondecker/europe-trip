# DQ 3.1 — Etapa 1: avaliação exploratória orientada à logística

## Estado anterior (main de 17/11/2026)

O comparador das 30 cidades exibia uma coluna **Nota final = Indisponível** para todas, mesmo com observações documentais. Em `base_coverage_model.py`, a documentação ponderada mede o progresso de itens e **não** a qualidade da cidade. `base_research_expanded_model.py` protege a decisão final exigindo, entre outros elementos, três ofertas mobiliadas disponíveis em 2027; isso permanece correto para a decisão definitiva, mas não deve impedir triagem exploratória.

Dados já existentes e reaproveitados:
- Matriz fixa de **15 destinos**: `five_base_comparison_evidence_2026_11.json`.
- Evidências ferroviárias históricas, com precedência e fontes: `rail_evidence_unified_model.py`.
- Trechos exploratórios complementares com fonte e duração: `exploration_bases_2027.json`.
- Evidência de acesso a atrações e caminhadas oficiais: `dq30_walking_access_model.py`, PRs #85–#87.
- Anúncios históricos e progresso documental: `base_coverage_model.py`.
- Passeios por base consultivos: PR #88, sem alterar TripPlan.

## Entrega nesta branch

**Novo contrato read-only:** `dq31_logistics_evaluation_model.py`, sem criar outro adaptador de trens, catálogo de atrações ou modelo de persistência.

- `validate_weights(weights)`: chaves `logistics`, `living_cost`, `daily_practicality`, soma 100 e valores não negativos; padrão **65/30/5**.
- `select_common_basket(study, selected_destinations=())`: subconjunto **idêntico** do conjunto de 15 destinos para todas as cidades. Fallback exploratório: Strasbourg, Colmar, Basel, Luxembourg City, Bruxelas e Bruges; não altera escolhas oficiais.
- `logistics_comparison(base_ids, selected_destinations=(), weights=None, ...)`: agrega dados existentes preservando fontes, sentido, escopo e ausência de retornos. Retorna `rows`, `basket`, `weights` e `quality_ranking_available=False`.
- `maturity_for_city(...)`: separa quatro rótulos, começando em pesquisa inicial, depois triagem, cobertura ampliada e decisão definitiva. O salto final exige sinal de prontidão de 2027 **que nenhuma cidade atualmente possui**.

**Estrutura de cada rota no resultado** inclui `oneway_train_min`, `return_train_min=null`, `station_to_attraction_evidence`, `attraction_to_attraction_min=null`, `complete_door_to_door_min=null` e `full_two_person_transport_eur=null`. Distâncias Haversine nunca são transformadas em caminhada. Um tempo oficial de acesso em Bruges é informação **do destino**, não uma vantagem própria da cidade-base.

**Interface:** `Explorar → Comparar → Pesos das 30 cidades` agora apresenta uma seção adicional de triagem de logística e moradia histórica, com seleção de cesta idêntica, três presets de prioridades (**65/30/5**, **75/20/5**, **50/45/5**), comparação filtrável, origem dos tempos e lacunas por base. A matriz documental e as decisões oficiais seguem visíveis, preservadas.

### Antes e depois

| Indicador | Antes | Depois |
|---|---|---|
| Triagem com mesmos destinos | Apenas matriz documental fixa de 15 | Subconjunto comum de 1–15 destinos, escolhido na UI |
| Prioridade de logística/custo | Pesos documentais 30/25/20/10/10/5 | Pesos explícitos de **65/30/5** e dois presets adicionais para pesquisa exploratória |
| Maturidade antes da decisão final | Sem nível de avaliação intermediário | Pesquisa inicial → triagem exploratória → cobertura fundamentada → decisão |
| Observações ferroviárias históricas | Parcialmente dispersas | Reaproveitadas com links; ida não equivale a retorno |
| Caminhada estação–atração | DQ3.0 separado | Exposta para destino quando há evidência; não é cálculo porta a porta |
| Faltas de informações em visitas | Nota final indisponível | Campos desconhecidos permanecem `null` e bloqueios específicos aparecem por cidade |
| Ranking final | Indisponível | **Continua indisponível**, corretamente, até dados comparáveis |
| Disponibilidade de aluguel em 2027 | Não comprovada | **Não inventada**, mantida para etapa definitiva |
| Mudanças em TripPlan/orçamento/reservas | Nenhuma | Nenhuma |

## Limitações fundamentais

Os pesos de 65/30/5 **expressam prioridades de pesquisa**; não autorizam somar minutos, euros e checklists em uma nota de qualidade. Tampouco é válido renormalizar só as informações conhecidas para transformar cobertura baixa em ótima pontuação. A interface informa cobertura e lacunas para ajudar a estreitar a shortlist sem emitir um ranking enganoso.

Um rótulo de `comparacao_fundamentada` no modelo é um **gate de cobertura exploratória**, não uma afirmação de que viagens e valores estão validados. Requisitos definitivos permanecem intactos.

A cesta padrão é uma sugestão quando nenhum dos passeios escolhidos pertence aos 15 destinos: seus conteúdos podem ser alterados pelo usuário na interface, sem modificar `TripPlan`.

## Exemplos e limitações de evidência

- **Mulhouse/Strasbourg:** comparam-se tempos conhecidos dos mesmos destinos e amostras de moradia sem assumir que uma diferença de tempo seja viabilidade completa.
- **Lille:** aproveita conexões historicamente documentadas para Bruxelas/Bruges; sem retorno, custos completos ou roteamento pedestre verificado.
- **Offenburg:** pode mostrar a ligação documentada a Strasbourg; trem ICE, TER e serviços regionais não são confundidos.
- **Freiburg:** se faltam tempos registrados em determinado destino, o campo fica `null`; isso **não** significa falta de trens.

## Próximo pacote: dados necessários

1. Pesquisa dirigida dos destinos prioritários para 5–8 bases e **mesmas datas/tipos de serviço**, com ida, retorno, frequência e conexões.
2. Acessos públicos verificados, distâncias e tempos pedestres calculados por motor autorizado; vincular trechos atração–atração sem supor Haversine.
3. Comparação homogênea de custos históricos para duas pessoas (tarifas normais e moradia mobiliada), distinguindo hipótese e contrato.
4. Verificação posterior de hospedagens, disponibilidade e reservas em 2027, quando houver datas disponíveis.

Não houve pesquisa em massa, novo motor pedestre, mudança de CSS, alteração de datas, plano ou nota definitiva. Testes: `tests/test_dq31_logistics_evaluation.py` mais suíte pré-existente.
