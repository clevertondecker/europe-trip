# UX 5.0.3 — Comparar cidades-base pelos destinos desejados

## Diagnóstico e fontes de verdade
- Base: `main` após UX 5.0.2 (PR #100). `AGENTS_COORDINATION.md` reserva os arquivos compartilhados ao integrador; este PR altera `app.py` exclusivamente para integração.
- `ux502_destination_interests_model.selected_destinations_for_comparison()` é a **única fonte** da cesta ativa; descartados são excluídos, prioridades ordenam os destinos. O comparador não persiste uma cópia.
- `ux501_destination_discovery_model` mantém identidade, nomes e países; `base_research_expanded_model.load_research()` fornece as 30 candidatas e `observed_housing()` preserva as condições históricas de moradia.
- `evidence_query_model.get_rail_evidence()` é o seletor ferroviário canônico. Observações alternativas e datas são preservadas. Não inferimos distância, trajetos de volta, tarifas ou 2027.
- `ux_navigation.py` já possui a aba `Explorar → Comparar`. As análises anteriores permanecem em expander avançado, sem redesenho global.

## Contrato público puro
`compare_wishlist_bases(interests, base_ids, *, discovery=None, research=None, rail=None, exploration=None)`
valida duas a cinco bases únicas no registro de 30 e retorna `destinations`, `base_ids`, `rows`, `summaries`, `discarded_count`, `comparison_ready`, `quality_ranking_available=False`, `official_plan_modified=False`.
Cada linha identifica origem, destino, prioridade, mínimo histórico, tempo típico selecionado, fontes, data, transferência pesquisada, alternativas divergentes e lacunas de retorno/última milha.

## Políticas de apresentação
- Para mesma cidade de origem/destino: **Local — acesso a verificar**, com tempo desconhecido, nunca 0.
- Sem registro ferroviário: **Sem evidência ferroviária catalogada** não quer dizer sem conexão.
- Tempos e tarifas de 2027 permanecem desconhecidos. Não há vencedora automática, nota artificial, otimização, alteração da cidade-base nem alteração do TripPlan.
- Moradia histórica não garante oferta mobiliada/56–60 noites em 2027; amostras não comparáveis são expressamente identificadas.
- Visualização por destino e cartões verticais para leitura em telas estreitas, com expanders para as fontes.
- `Minha lista` navega para a comparação usando a mesma cesta; o retorno não altera desejos. Escolhas de bases ficam apenas em `ux503_bases` na sessão.

## Testes e limitações
Testes puros verificam basket igual, prioridade, exclusão, 2–5 bases, local sem tempo, lacunas, divergências e imutabilidade. AppTest cobre navegação, atualização das preferências, favoritos e proteção do TripPlan. A verificação visual em navegador real não está atestada por essa suíte; validar antes de considerar concluída a responsividade.
