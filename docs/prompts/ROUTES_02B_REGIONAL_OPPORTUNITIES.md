# PROMPT 2B/7 — Novos destinos possíveis por corredor e país

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
Identificar oportunidades de conhecer **outros países e destinos** que ficam interessantes quando se muda a região-base. Esta fase complementa a cesta atual, mas não altera automaticamente os desejos persistidos.

## Premissas
Usar o estudo geográfico do PR 2A como fonte de candidatas e os 46 destinos/94 atrações já registrados como primeira fonte de identificação. França, Alemanha, Bélgica, Luxemburgo, Países Baixos e Suíça são **hipóteses de regiões e não itinerários confirmados**. Quando um local for novo, distingui-lo de destino existente.

## Procedimento
1. Ler `ux501_destination_discovery_model.py`, `dq32_macro_opportunities_model.py`, modelo de reconciliação de atrações, documentação do PR #108 e os resultados de 2A. Evitar duplicar destinos/atrativos sob variantes de idioma, grafia ou IDs.
2. Preparar **candidatos com justificativa geográfica**, agrupados por origem (ex.: Metz/Strasbourg; Liège/Maastricht; Basel/Freiburg; Amsterdam/Lille). Informar país, cidade, atrações-exemplo de interesse, fonte oficial da atração, confirmação de existência e sua identidade canônica.
3. Para cada oportunidade, registrar separadamente `discovered`, `rail_service_researched`, `historical_train_time`, `return_feasibility_unknown`, `last_mile_unknown`. Viagem possível não significa bate-volta viável, muito menos viagem em data de 2027.
4. Não exagerar quantidade: propor inicialmente 3–5 oportunidades **por corredor**, com curadoria e diversidade real em vez de criar uma lista ilimitada de atrações.
5. Manter dois modos: `existing_wishlist_destinations` (cesta fixa para comparar todas as bases) e `new_opportunities_by_region` (exploração separada, não usada silenciosamente para favorecer uma base).
6. Política de inclusão: propostas não entram automaticamente em `selected_destinations_for_comparison()` nem `TripPlan`. Somente após aceite explícito do usuário e reconciliação com o catálogo.

## Entrega após aprovação
- Documento e dataset rastreável de oportunidades, com fonte e data, ID canônico ou `proposed`, novas regiões/países e campos de acesso a investigar.
- Plano de publicação discreta das oportunidades no futuro, **sem mudanças na UX 5.0.3 neste PR**.
- Lista de conflitos de identidade, fontes incompletas e possíveis falsas oportunidades.

## Testes e aceite
Sem destino duplicado, sem wishlist alterada, nenhuma rota inventada, proveniência para cada atração, distinção explícita de descobrir/tempo/retorno, testes de origem de dados e destino removido/renomeado.

## Fora de escopo
Cadastrar automaticamente destinos, selecionar atrações, reservar passeios, premiar por número de países, melhorar o comparador visual.


## Contrato de revisão
Este é um documento de instruções. O diff desta PR **não implementa a funcionalidade**. Comentários de outra IA devem ser publicados neste PR, preferencialmente organizados por P0/P1/P2 e com mudanças propostas ao texto; só após aceite será autorizada a implementação.
