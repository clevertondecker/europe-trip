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
| Simulação de passeio | Orçamento → Simulações | Reutilizar DATA8, estimativa isolada, sem integrar totais |
| Handoffs antigos | REC03B e UX128 | Redirecionar à comparação moderna, sem outra página |

## Estratégia
Primeiro commit elimina acesso público ao comparador manual e migra capacidades. Segundo commit remove o renderizador completo e os escritores de filtros antigos, adapta testes à comparação moderna e preserva apenas os tokens de compatibilidade de sessões antigas. Não mergear antes de CI verde e revisão. Validar CI do HEAD exato e QA de navegador se disponível. DATA25 permanece em branch independente.

## Estado
Recorte de destinos legado só vira rascunho se não houver escopo moderno válido; não confirma uma nova escolha. IDs inválidos e descartados não são recuperados; acima de cinco, preservar e pedir remoção. Handoffs de perfil/mapa/planejamento seguem seus contratos. Nenhuma alteração de plano, wishlist, orçamento oficial ou pesquisa. QA visual e CI pendentes.
