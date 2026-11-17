# PROMPT 1/7 — Contratos e validação de evidências ferroviárias

> STATUS: **SOMENTE PROPOSTA PARA REVISÃO POR OUTRA IA.** Este PR contém apenas este prompt, não código funcional nem pesquisa nova. Não executar implementação, merge ou deploy antes de avaliação/autorizações explícitas. Depois de aprovado, executar na mesma branch ou conforme coordenação dos agentes.
>
> Projeto: Nossa Europa 2027 — `clevertondecker/europe-trip`. Referência obrigatória: auditoria de cobertura **PR #108** (30 bases, 46 destinos, 94 atrações; 1.380 pares base–destino, dos quais 54 com tempo histórico, 25 parciais, 1.271 não pesquisados e 30 locais). Como #108 pode ainda não estar na main, consultar o PR/branch e não presumir integração.
>
> Antes de programar: sincronizar `main`, verificar PRs concorrentes e CI, ler `AGENTS_COORDINATION.md`, `evidence_query_model.py`, `rail_evidence_unified_model.py`, `ux503_destination_base_comparison_model.py`, os dados de origem e testes. Respeitar ownership: integrador único para arquivos compartilhados. Cada PR deverá ter diff focado, validação de fontes, testes, documentação e CI verde.
>
> **Restrições gerais:** viagem somente APÓS 04/09/2027, sazonalidade set.–nov. 2027; não inventar horários, preços, tempos, rotas, conexões, retornos ou alugueis de 2027. Ausência de dados ≠ ausência de transporte. Tempo estação–estação ≠ porta–porta. Preservar `TripPlan`, base oficial, desejos/prioridades, backups, persistência, navegação legada e a semântica de `get_rail_evidence()`. Nenhum ranking automático por volume de evidências.
>
> **A revisão por outra IA deve entregar:** (a) pontos P0/P1/P2, com explicação; (b) contratos existentes reutilizados; (c) dados/fontes ausentes e como verificar sem pressuposições; (d) riscos de regressão ou duplicação; (e) sugestões de teste e escopo; (f) parecer "apto para implementação / ajustar prompt". NÃO executar código apenas porque este PR foi aberto.


## Objetivo
Construir a capacidade **aditiva, rastreável e reutilizável** para pesquisas ferroviárias e acessos sem reimplementar regras nem alterar dados consolidados. Evitar que os PRs de pesquisa usem campos incompatíveis.

## Diagnóstico e desenho exigidos
1. Inspecionar os esquemas em `data/five_base_comparison_evidence_2026_11.json`, `data/base_city_rail_evidence_expanded_2026_11.json`, `data/dq30_mobility_pilot_2026_11.json`, `data/base_destination_routes_2027.json`, `data/exploration_bases_2027.json` e a auditoria #108.
2. Identificar no código a autoridade para alias/identidade de cidades e estações (`canonical_place`), precedência de evidência e observações alternativas. **Não alterar a semântica de `get_rail_evidence()`**.
3. Propor um contrato versionado de **observação de rota**, não de "conexão garantida": IDs canônicos origem/destino + estação de partida/chegada (com ID, operador e país quando verificados), escopo de viagem, duração mínima/representativa (nulos permitidos), transfers opcionais, serviço/dia pesquisado, source_url, checked_at, observed_at, unidade, período e status `historical_observation|operator_summary|partial|unknown|local`. Proteger distinção entre horário exato, exemplos e alegações gerais de operador.
4. Propor **referências de acesso às atrações** por `destination_id` + `canonical_attraction_id` + estação, com modo, distância/duração verificadas, fonte e data. Nunca derivar uma caminhada da distância em linha reta.
5. Validadores puros: identidade, fontes HTTPS, tempo estritamente positivo quando presente, nulos honestos, datas reais, duplicação com chaves de identidade corretas, múltiplas observações conflitantes preservadas, impossibilidade de afirmar `valid_for_2027` sem fonte e dia aplicável.
6. Compatibilidade: explicar como ligar essa estrutura ao adaptador atual, e quando **não** alterar o adaptador por falta de integração aprovada. Dados novos não substituem evidência anterior sem auditoria de precedência.

## Entrega após aprovação
- Documento ADR com contrato, campos, status e exemplos completos de registros válido, parcial, local e divergente.
- Módulo puro de validação/projeção e testes, se indispensável, sem segunda lógica ferroviária; relatório de compatibilidade com os esquemas existentes.
- Arquivos sugeridos: novo `route_research_evidence_model.py`, `tests/test_route_research_evidence_model.py`, `docs/ROUTE_RESEARCH_CONTRACTS.md`. Mudanças em arquivos de ownership do integrador **somente** via integrador.

## Critérios de aceite
Validação de fontes/identidade e nulos, tratamento explícito de dados divergentes, preservação do TripPlan e das observações antigas, zero novas rotas ou estimativas. Testes cobrem erro de origem/destino, alias, fonte ausente, valores zero/negativos, data impossível, duplicados, fontes contraditórias e estados locais.

## Fora de escopo
Coletar tempos, recomendar cidade-base, calcular notas, automatizar itinerário, integrar UI ou alterar persistência.


## Contrato de revisão
Este é um documento de instruções. O diff desta PR **não implementa a funcionalidade**. Comentários de outra IA devem ser publicados neste PR, preferencialmente organizados por P0/P1/P2 e com mudanças propostas ao texto; só após aceite será autorizada a implementação.
