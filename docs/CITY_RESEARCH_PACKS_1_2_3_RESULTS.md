# Execução dos pacotes 1, 2 e 3 — resultado verificável

Data de pesquisa: **16/11/2026**. Base: `main` pós-PRs #55/#58/#59. Plano: `docs/CITY_RESEARCH_PACKS_1_2_3_EXECUTION_PROMPT.md`.

## O que de fato foi enriquecido

| Dimensão | Resultado | Limite para decisão |
|---|---|---|
| Vida cotidiana | Referências históricas de refeição intermediária para casal em 4/12 finalistas; coworking com fonte, preço e ressalvas em 4/12 (reutilização de `data/city_research_round2_2026.json`) | Índice colaborativo não permite comparação de cesta inteira; coworking não significa internet do imóvel |
| Clima | Normais 1991–2020 de **6 estações francesas**: temperatura média e precipitação de set/out/nov, com nome da estação e URL | Não representam microclima do centro ou previsão 2027; 6 finalistas da Alemanha/Bélgica ainda sem série equivalente |
| Bairros | **30 bairros citados por fontes** para 12/12 finalistas; qualidade habitacional e distância por imóvel continuam não verificadas | Não constituem recomendação de aluguel, segurança ou distância verificada a estação |
| Moradia | **35 observações históricas de anúncios** preservadas, incluindo URLs diretas onde existentes e distinção de páginas de catálogo | **Zero** apartamentos confirmados para duas pessoas por 56–60 noites após 04/09/2027, com taxas e internet |
| Mobilidade | **5 referências oficiais ferroviárias** contextualizadas (Mulhouse↔Strasbourg, Metz↔Strasbourg, Nancy→Metz) com tempos publicados e limite de frequência | Nenhum retorno de fim de semana em datas da viagem foi confirmado; 15 destinos da cesta principal não estão completos |
| Reutilização | Catálogo permanente `docs/CITY_RESEARCH_SOURCE_REGISTRY.md` atualizado; novo dataset `data/city_research_packs_2026_11.json` | Novas pesquisas devem ter fonte, período, unidade e limites; proibição de scraping sem licença permanece |

## Invariantes

- Cadastro original de 30 cidades, incluindo 12 finalistas, sem alterações.
- `city_profiles_ui.py` reutiliza os dados existentes, mantendo a matriz documental e o comparador sem novo menu principal.
- Novo `city_research_packs_model.py` é **somente leitura**: valida IDs, fontes, datas, distinção de anúncio direto, climatologia com três meses, tarifas condicionadas e `false` para reservas/voltas ainda não verificadas.
- Nenhuma alteração em `TripPlan`, simulações financeiras, GCS, Drive, credenciais, armazenamento pessoal ou tarifas do motor ferroviário.
- Fatos de preços comerciais antigos foram **reutilizados** a partir do arquivo de 2026; não houve scraping do Numbeo, Flatio ou HousingAnywhere.

## Pesquisa documental — exemplos

- Para Strasbourg, bairros Gare-Tribunal, Bourse-Esplanade-Krutenau e Neudorf constam no [turismo local](https://www.visitstrasbourg.fr/decouvrir-strasbourg/strasbourg-et-alentours/les-quartiers-de-strasbourg/).
- Para Metz, Sablon/Amphithéâtre, Gare/Nouvelle Ville e Centre-Ville constam nos [conselhos de bairro municipais](https://metz.fr/engager-entraider/citoyennete/conseils-quartiers.php).
- [TER Mulhouse–Strasbourg](https://www.ter.sncf.com/grand-est/trajet-mulhouse-strasbourg) informa **53 min** e até **33 A/R diários**, sem garantir esses horários para sábado de 2027.
- [TER Metz–Strasbourg](https://www.ter.sncf.com/grand-est/trajet-metz-strasbourg) informa **1h36** e seis A/R de dia; tarifas Carte Fluo exigem cartão e condições próprios.
- [Meteociel — Strasbourg-Entzheim](https://www.meteociel.fr/obs/clim/normales_records.php?code=67124001) apresenta normais 1991–2020 de estação; no outono, a temperatura média da estação vai de 16,1 °C em setembro a 6,3 °C em novembro.

## Revisão A — engenharia de dados

O esquema novo reutiliza IDs existentes e observações legadas sem sobrescrevê-las. Valida `null` e proteções contra disponibilidade ou retorno inventados. Nenhum fato incompleto entra em ranking ou cálculo financeiro. Fazer integração somente após CI verde.

## Revisão B — crítica de UX (segunda passagem, não agente isolado)

A ficha ganha três seções de interesse prático com evidências e pendências. Cuidado com densidade de texto e com leitura mobile de tabelas climáticas; realizar inspeção real após publicação. **Não declarar revisão UX independente, screenshot ou teste com usuários sem tê-los realizado.**

## Pendências reais para próxima pesquisa

1. Cesta de custo cotidiano para todas as 12 finalistas, em período/unidade comum, com preço direto do prestador ou base oficialmente autorizada.
2. Normais climáticas para as seis finalistas da Alemanha/Bélgica com método análogo, sem misturar cidade e estação sem indicação.
3. Moradias mobiliadas reserváveis no período real de 2027 (datas ainda não estabelecidas, portanto não afirmar disponibilidade).
4. Retorno de sábado/domingo e última milha das 15 rotas da cesta, não apenas duração de ida.
5. Bairros de Offenburg e Aachen identificados com fonte; falta comparar efetivamente imóveis, transporte e adequação dos endereços.
6. Testes visuais reais 375/768/1280 px, teclado, validação de links e revisão independente UX.

**Conclusão rigorosa:** execução **incremental concreta dos três pacotes**, não enriquecimento absoluto de todas as seis dimensões para todas as cidades. Lacunas mantidas como `null` ou pendentes.
