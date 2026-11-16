# Execução · Pacotes 1, 2 e 3 — Pesquisa prática de cidades-base (Nossa Europa 2027)

## Contrato

**Produto:** Nossa Europa 2027 (Streamlit). **Base:** `main`, após PRs #55, #58, #59. **Data de análise:** 16/11/2026. **Jornada:** casal, sem automóvel, trabalhando remotamente durante aproximadamente 56–60 noites na Europa após 04/09/2027.

Atuar como analista de dados europeu, pesquisador de moradia temporária, especialista ferroviário, desenvolvedor Python/Streamlit e revisor QA. Não presumir segunda revisão UX independente nem navegação real sem evidência.

**Objetivo:** tornar úteis as fichas de todas as 30 cidades, dando profundidade às 12 finalistas e aproveitando integralmente os dados já registrados.

## Pré-auditoria

1. Ler `AGENTS_COORDINATION.md`, `docs/CITY_RESEARCH_SOURCE_REGISTRY.md` e `docs/CITY_RESEARCH_ENRICHMENT_STATUS.md`.
2. Conferir `data/city_profiles_enriched.json`, `data/base_city_research_expanded_2026_11.json`, `data/city_research_round2_2026.json`, `data/base_city_rail_evidence_expanded_2026_11.json`, `data/base_destination_routes_2027.json`, `base_coverage_model.py` e UI das fichas.
3. Manter os 30 IDs oficiais, 12 finalistas, histórico, datas e `TripPlan` inalterados. Nada de dados privados, novas abas de topo, pagamentos ou rankings inventados.

## Pacote 1 — Rotina, custo cotidiano e clima

1. Nas 12 finalistas, identificar dados oficiais de preços para supermercado, refeição simples, restaurante para casal, café, bilhete e passe urbano. Extrair valores **somente** quando fonte específica, moeda, unidade, período e condição estiverem disponíveis. Fonte colaborativa é referencial, nunca cesta completa automaticamente.
2. Reaproveitar quatro pesquisas legadas (`mulhouse`, `strasbourg`, `metz`, `nancy`), conservando qualidade: restaurante para dois publicado via Numbeo em 2026 e coworkings de fontes diversas, com observações de contrato, horário e impostos. Não visitar/raspar Numbeo em lote.
3. Pesquisar internet, bibliotecas, coworkings e transporte local para o restante das finalistas. Se apenas indicação de fornecedor, registrar presença da referência, **não** conexão adequada no imóvel.
4. Para clima, utilizar normais 1991–2020 por estação de Météo-France/DWD/IRM/KMI ou reanálise comum ERA5-Land; extrair temperatura média e chuva de setembro, outubro, novembro em **perímetro equivalente** e registrar origem, estação/município, método, licença. Se arquivo bruto estiver inacessível, manter `null`; não inventar série a partir de previsão de 2027.
5. Acrescentar à interface apenas campos preenchidos, com "Sem dado comparável" para o restante; jamais colocar zero no cálculo oficial.

## Pacote 2 — Moradia temporária e bairros

1. Reaproveitar todas as amostras históricas de aluguel por cidade (URLs de anúncio específico versus páginas de catálogo); destacar a quantidade de **anúncios individuais**, o status de 56–60 noites, ocupação de dois adultos, internet, taxas, caução, condições de cancelamento.
2. Verificar anúncios individualmente quando disponíveis, sem raspagem de plataformas fechadas nem supor oferta futura.
3. Pesquisar bairros **nominalmente** em portais municipais e operadores de transporte; ex.: Strasbourg (Gare/Tribunal, Krutenau, Neudorf), Metz (Sablon/Amphithéâtre, Gare/Nouvelle Ville), Nancy (Poincaré/Foch e Charles III), Lille (Vieux-Lille, Lille-Centre, Wazemmes), Dijon (Montchapet), Freiburg etc. Somente adicionar locais sustentados por URLs reais.
4. Bairro a pesquisar NÃO significa bairro aprovado, seguro ou imóvel disponível. Diferenciar acesso ferroviário **a confirmar**, áreas de lazer e perfil urbano. Sem scores.
5. Enriquecer fichas com bairros investigáveis e avisos de 2027.

## Pacote 3 — Mobilidade real aos fins de semana

1. Continuar a usar a cesta fixa de 15 destinos, sem sobrescrever matriz de rotas. Priorizar conexões comprovadas de operadoras e tempos ou frequências explicitamente publicados.
2. Registrar separadamente `origin`, `destination`, `source_url`, `observed_at`, `duration_minutes`, `frequency_description`, `round_trips_per_day`, `sample_period`, `return_sample_verified`, `last_mile_verified`, `ticket_conditions` e `valid_for_2027=false`.
3. Dados de um serviço de ida **não** confirmam bate-volta. "Até 33 A/R diários" não significa 33 saídas em sábado ou disponibilidade futura. Tarifa Carte Fluo não equivale à tarifa cheia; não duplicar promoção de duas pessoas automaticamente.
4. Apresentar oportunidades e ressalvas com links no perfil e não tocar no motor financeiro.
5. Priorizar rotas das 12 finalistas; se faltarem dados de volta em dia de interesse, registrar pendência, não "impossível".

## Modelo, interface e governança

- Criar **somente um dataset complementar versionado** por `city_id`, sem copiar a matriz ferroviária inteira ou sobrescrever o arquivo canônico das 30 cidades.
- Dados públicos: evidências têm URL, data, período, geografia/unidade, tipo, limitações e fonte. Links de índices gerais são **diretórios para futura pesquisa**, não comprovação de valores.
- Integrar à `city_profiles_ui.py`: separar "Vida cotidiana", "Bairros e moradia" e "Viagens de fim de semana"; itens pesquisados e faltantes ficam claramente distintos.
- Atualizar `docs/CITY_RESEARCH_SOURCE_REGISTRY.md` apenas com fontes concretas e papéis definidos, sem copiar integralmente conteúdo proprietário.
- Testar 30 IDs, 12 finalistas, independência de `TripPlan`, ausência de preço 2027, normal climática só com fonte/ano/método, links válidos, dados de ida versus volta, comparações sem custos presumidos, e smoke Streamlit AppTest.
- Revisão de engenharia, crítica UX separada e CI. Teste visual de 375/768/1280px e sessões reais permanecem pendentes até serem executados.
- Abrir PR(s) para revisão. **Sem merge ou deploy sem aprovação do proprietário.**

## Critérios de conclusão

Publicar contagens reais por dimensão: dados históricos de refeição, coworkings, bairros com fonte municipal, anúncios com URL própria, moradia confirmada 2027, normais climáticas efetivamente extraídas, rotas com frequência e retornos realmente verificados. Nunca anunciar três pacotes "completos" se faltarem dados específicos. A pesquisa deve ser continuável usando o catálogo permanente, com a próxima fonte ou lacuna sugerida para cada cidade.
