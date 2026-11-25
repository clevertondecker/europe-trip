# UX128 — Unificação do comparador

## Auditoria e decisão de migração
A experiência pública passa a usar exclusivamente REC03A/UX87/UX97. O motor UX503, as projeções, DATA24 e os dados são compartilhados e permanecem intactos.

| Capacidade legada | Equivalente/destino | Decisão |
|---|---|---|
| Seleção de cidades e destinos | CHOICE e SCOPE/DRAFT | Migrar seleções antigas válidas sem substituir escolhas modernas; remover acesso público paralelo |
| KPIs e matriz | UX87/UX97 | Não duplicar |
| Datas, transferências, observações e fontes | Painel existente UX87 | Preservar por destino, sem outra matriz |
| Regras e horários de atrações | Detalhes de Descobrir/DATA8 | Reutilizar renderizador enriquecido |
| Moradia e rotina | UX113 e UX124; auditoria DATA24 | Preservar modelos, não duplicar tabela |
| Simulação de passeio | Descobrir → detalhes do destino | Reutilizar DATA8 contextual, não criar terceiro total em Orçamento |
| Handoffs antigos | REC03B e UX128 | Redirecionar à comparação moderna, sem outra página |

## Estratégia
Primeiro commit elimina acesso público ao comparador manual e migra capacidades. Segundo commit remove o renderizador completo e os escritores de filtros antigos, adapta testes à comparação moderna e preserva apenas os tokens de compatibilidade de sessões antigas. Não mergear antes de CI verde e revisão. Validar CI do HEAD exato e QA de navegador se disponível. DATA25 permanece em branch independente.

## Estado
Recorte de destinos legado só vira rascunho se não houver escopo moderno válido; não confirma uma nova escolha. IDs inválidos e descartados não são recuperados; acima de cinco, preservar e pedir remoção. Handoffs de perfil/mapa/planejamento seguem seus contratos. Nenhuma alteração de plano, wishlist, orçamento oficial ou pesquisa. QA visual e CI pendentes.


## Review — cobertura UX506, simulador e migração
- **O que já sabemos para decidir?**: aposentar o bloco agregado. Cobertura turística (contagem de catálogo, ingresso histórico, horários/regras e piloto) passa ao detalhe de cada destino em Descobrir; DATA8 mantém a pesquisa enriquecida separada. Pendências por par e estado temporal passam ao painel UX87, reutilizando UX506, sem montar outra matriz. Moradia permanece UX113/UX124 e auditoria D-004. Os desconhecidos não são gratuitos nem confirmação de 2027.
- **UX506** permanece em produção como contrato de associação temporal e de prontidão; sua projeção agregada é preservada nesta entrega para compatibilidade de contratos e testes de overlays. Não criar outra tela. **UX505** é aposentado junto aos testes específicos do texto/contadores antigos; os testes de jornada, categorias e não mutação modernos permanecem.
- Simulador DATA8 volta ao contexto do destino, dentro dos detalhes existentes. Não altera orçamento oficial/simulado e não é montado na página Simulações.
- Compatibilidade de sessão: MANUAL, intent manual, kind manual/restore_manual, filtros ux503/ux504 e retorno pendente são somente leitores de estado efêmero antigo; nenhum CTA público gera esses estados. Remover os adaptadores em PR posterior após um ciclo de deploy validado, encerramento das sessões pré-UX128 e verificação dos consumidores; nunca persistir esse estado. O bootstrap consome chaves antes dos widgets, com retorno imediato em sessão moderna. Não executar migração dentro de render_suggestions.
- CI do HEAD final e QA visual pendentes; não mergear por resultado de commit anterior.
