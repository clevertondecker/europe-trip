# UX130 — Descobrir e Minha lista: explorar antes de planejar

**Status: proposta para implementação; nenhum código funcional alterado neste commit.**

## Objetivo e justificativa
Descobrir atualmente apresenta “Adicionar ao roteiro” como ação primária e “Salvar na lista” como secundária, além de “Posso planejar agora”. Isso mistura intenção de conhecer com compromisso de planejamento e pode excluir da análise de bases destinos colocados diretamente no TripPlan. A elegibilidade é uma limitação do catálogo, não uma medida de qualidade turística ou viabilidade logística. Separar exploração de decisão de visita.

## Implementação proposta
- Auditar ux501_destination_discovery_ui.py, ux502_destination_interests_ui.py, itinerary_eligibility.py, UX126, filtros, handoffs de ficha e testes; identificar TODOS os consumidores de _discover_eligible e da chave ux126_eligibility_filter antes de remover.
- Em Descobrir, preservar foto, crédito/licença, nome/bandeira, país, destaques, pesquisa por nome/atração, experiências, paginação e detalhes turísticos/custo contextual DATA8 preservados no UX128.
- Uma ação principal “Quero conhecer” usa add_destination e prioridade interested; após clique, feedback imediato “Na minha lista”, sem nova gravação do TripPlan. Destino descartado mantém ação explícita de reconsiderar. Não inventar comportamento de remoção ao clicar num estado passivo.
- Remover “Adicionar ao roteiro” e “Organizar” como ações de mutação/edição de Descobrir; destino já planejado recebe estado informativo “No roteiro” e, se necessário, link não mutante ao editor proprietário. Preservar os destinos já incluídos mesmo se não constarem na wishlist.
- Remover rádio “Posso planejar agora”, partição por elegibilidade e avisos técnicos dos cards; exibir todos os resultados segundo ordenação de exploração existente, sem ranking artificial. Migrar snapshots de filtro antigos sem perder país, experiências, busca ou paginação. Handoffs antigos de “Descobrir destinos compatíveis” devem abrir Descobrir sem filtro oculto, com texto coerente.
- Minha lista: preservar galeria e prioridades Imperdível/Quero conhecer/Talvez/Descartado. Exibir estado de roteiro de forma compacta quando útil; destacar “Comparar cidades-base” e oferecer “Montar meu roteiro” (ou revisar quando já existir) com os handoffs atuais. Não obrigar comparação antes de planejar.
- Não adicionar outro seletor de cidades, catálogo, painel ou estado persistido. Não repetir avisos sobre lista versus roteiro em cada card. Preservar comparação UX128 e seus destinos de pesquisa.
- Remover callbacks/imports/widgets/CSS exclusivamente obsoletos após auditoria. Manter regra de elegibilidade e modelos compartilhados para Planejar. Se algum fluxo perder acesso a uma ação necessária, mover a ação ao dono antes de retirar a origem; coordenação com UX131.

## Por que esta organização?
Descobrir responde “o que queremos conhecer?”, Minha lista responde “com que prioridade?”, Comparar bases responde “onde ficar?”. Um único CTA reduz ambiguidade e permite explorar destinos mesmo sem dados completos. A lista não é confirmação de visita nem orçamento. Ações sobre roteiro pertencem ao planejamento. O usuário pode comparar ou planejar diretamente, sem wizard rígido.

## Critérios e testes
- Descobrir mostra destinos suportados e de pesquisa, sem filtro oculto após sessão restaurada; busca, categorias, fotos, detalhes, paginação e retorno de perfil preservados.
- Quero conhecer atualiza wishlist uma vez e feedback no mesmo rerun; prioridade/descartado/reconsiderar preservados; nenhuma mutação do TripPlan, orçamento, revisão ou grupos.
- Destino já planejado não é removido ou duplicado, mesmo ausente da lista. Não existe CTA de inclusão direta em Descobrir.
- Minha lista permite comparar e abrir o planejador, com destinos pesquisados preservados. Validar acesso aos fluxos atuais de inclusão antes de remover qualquer entrada.
- AppTest, contratos e QA visual desktop/mobile; atualizar testes de UX126 sem enfraquecer invariantes.
- CI do HEAD final e review antes de merge.

## Dependências
Prioridade 2 após UX129. UX131 complementa a centralização de inclusão; verificar sua solução de acesso antes de publicar UX130, evitando regressão intermediária. DATA25 não é alterado.
