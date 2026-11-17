# UX 5.0.2 — Destinos desejados e prioridades

## Auditoria / autoridade
- `TripPlan.preferences` guarda **atrações**, não destinos. `mandatory_destinations`/`excluded_destinations` têm outra semântica; favoritos UX 4.1 são **cidades-base**. Não reutilizar.
- `private_continuity_store.PrivateArchiveStore` salva o **arquivo privado único** por proprietário, com geração GCS e controle otimista; nunca grava a coleção no GitHub público.
- Autoridade na sessão: `ux502_interests`. Widgets são projeções; o arquivo de continuidade (local ou privado) leva o mesmo documento versionado. Não há segundo backend.
- O schema de arquivo de continuidade segue **v1**, com propriedade opcional `destination_interests`; backups legados importam com `empty_interests()`. O `TripPlan` permanece v1 e intocado.

## Contrato
`{kind: "nossa-europa-destination-interests", schema_version: 1, revision: N, items: [{destination_id, priority}]}`.
Prioridades: `must_visit`, `interested`, `maybe`, `discarded`. IDs são validados contra a descoberta consolidada. `selected_destinations_for_comparison(interests)` devolve IDs ativos na ordem da prioridade, descartados excluídos. Nenhuma evidência de trem é inferida.

## Recuperação e status
- Uma importação local precisa de confirmação; não altera servidor. Exportação JSON da lista é independente do backup completo.
- O backup completo e o arquivo privado incluem a lista. A restauração GCS ocorre somente se proprietário autenticado e bucket configurado. Não há promessa de disponibilidade da nuvem.
- Salvar privado chama o fluxo existente `save_private_now`, preservando `ifGenerationMatch`; erros e conflitos conservam o conteúdo na sessão. O status só vira salvo após resposta confirmada.
- `ux501_interest_session` não é incorporado automaticamente nem sobrescreve a lista existente; ação explícita inclui apenas ausentes.
- Campos do roteiro, base, calendário, preços e backup anterior permanecem isolados.

## Limites
Não há comparação logística, viagens agendadas ou mudança automática de cidade-base. Testes abrangem domínio, archive legado, round-trip e navegação AppTest. A inspeção visual em navegador real não foi executada neste PR.
