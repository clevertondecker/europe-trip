# DATA24B — Lacunas contextuais, sem dashboard

Depende de DATA24A (#253); implementar somente após UX125 (#256) e validar os ajustes já realizados no UX126B (#254). Não constitui pré-requisito para UX125. Auditar antes de modificar: UX126 já exibe status e reason do contrato itinerary_eligibility; não criar outra elegibilidade. Em Descobrir, melhorar apenas lacuna acionável comprovadamente insuficiente, sem repetir CTA, sem bloquear wishlist, sem inventar requisitos. Na ficha UX124, usar os mesmos pares e prioridades de Logística para mostrar trajetos desejados sem tempo pesquisado e filtro explícito quando necessário, não outra matriz global nem ranking. Preservar fontes, local, indicativo, divergências, sem wishlist, etapas, retorno e persistência. Não calcular auditoria global durante rerun. Testar AppTest, paridade com elegibilidade/UX124, vazios e nenhuma mutação. Se já satisfaz o objetivo, registrar evidência e evitar mudança cosmética. Não tocar navegação legada de UX125.

## Entrega
Implementar sequencialmente após pré-requisitos. Antes de implementar, atualizar base com alterações integradas ou estabelecer stack revisável; evitar conflitos em app.py e no gerador. Manter draft até código, suíte completa e checks do HEAD confirmados; não mergear sem autorização. Documentar limitações e evidência de testes. DATA25–28 serão definidos a partir dos resultados, não neste PR.

**Status:** implementação aprovada na CI 45658850305 (HEAD e590ae88, 1390 testes, 2 ignorados, zero falhas); ajustes de revisão posteriores exigem nova CI.

## Auditoria de equivalência

- Descobrir: `ux501_destination_discovery_ui` usa `itinerary_eligibility` e apresenta o `reason` para pesquisa/ outra etapa; UX126B já separa ações do roteiro e da wishlist. Nenhuma alteração necessária.
- UX124: Visão geral já indica a quantidade sem tempo e lista imperdíveis sem referência. Logística não oferecia filtro exclusivo para os destinos desejados sem tempo. Adicionado `Sem tempo (lista)`, derivado de `route_scope`, apenas prioridades ativas e categoria `no_time`, sem novo cálculo, ranking ou auditoria global. Mantidos fontes, ordem, detalhes, locais e indicativos nos outros recortes.
- Cobertura: testes unitários de paridade/ordem/locais/indicativos/descartados e AppTest de seleção/vazio; nenhuma alteração no plano, catálogo, persistência ou navegação. QA visual não realizado.