# DATA24C+D+E — Auditoria das bases finalistas para D-004

## Objetivo
Produzir uma auditoria técnica direcionada à decisão pendente de cidade-base (D-004), reunindo moradia, vida cotidiana e trabalho remoto no mesmo gerador e relatório técnico iniciado por DATA24A (#253). Amplia o escopo original de moradia para incorporar vida cotidiana e trabalho remoto, consolidando os antigos PRs #258 e #259. Não criar página, dashboard, ranking ou inventário concorrente no aplicativo.

## Escopo e fontes
- Identificar as finalistas da D-004 nas fontes oficiais e estudos existentes. Registrar IDs, origem, data e critérios do recorte; não assumir todas as 34 bases nem confundir candidatas com decisão oficial. Não inventar finalistas ou modificar D-004; se a fonte não definir o recorte de forma inequívoca, documentar a lacuna e solicitar confirmação antes de atribuir prioridades.
- Moradia: reutilizar observed_housing, housing_short_stay_research_model e evidências UX506/REC04; distinguir preço mensal de temporada, datas, duração 56–60 noites, duas pessoas, bairros, internet, taxas/caução, disponibilidade e contrato. Não misturar amostras nem inferir 2027.
- Vida cotidiana: reutilizar round2, city packs, market e perfil canônico; alimentação, cesta local, transporte urbano, clima e serviços quando documentados. Preservar unidades, pessoas, período, fontes e datas; distinguir premissas do orçamento de evidência local.
- Trabalho remoto: reutilizar UX113/REC04 e evidências canônicas sobre coworking, modalidade, preço, horário/acesso e compatibilidade com expediente. Internet residencial separada. Distinguir compatível, incompatível e indeterminado; não inferir fuso ou disponibilidade.
- Cruzar lacunas com auditoria ferroviária de DATA24A e com necessidades explícitas da D-004 quando relevante. Não recalcular orçamento oficial nem alterar premissas. Mostrar quais pesquisas destravam a escolha, quais são complementares e quais já têm evidência suficiente, com justificativa; sem pontuação ou ranking artificial.

## Entrega
Um único conjunto de extensões ao gerador docs/audits/data24_research_coverage.md, com seções e denominadores explícitos para o recorte D-004, contagens, fontes, datas, condições e lacunas acionáveis para DATA25–28. Ausência não equivale a zero; distinguir desconhecido e não aplicável. Sem novos dados de pesquisa neste PR. Sem mudanças em UI, decisões oficiais, pendências, TripPlan, orçamento, persistência ou wishlist.
Testar reutilização dos contratos, recorte, estados desconhecidos, unidades, rastreabilidade, determinismo, ausência de mutação e integração ao snapshot. Executar suíte e confirmar CI verde no HEAD exato; declarar limitações de QA. Não iniciar DATA25–28.

## Dependências e prioridade
Depende da infraestrutura e relatório de DATA24A. Implementação após UX126B, UX127, DATA24A, UX125 e avaliação de DATA24B. #258 e #259 foram encerrados como consolidados neste PR; preservar seu histórico. Manter draft até revisão, sem merge sem autorização específica.

**Status:** especificação consolidada; implementação pendente.
