# Nossa Europa 2027 — Roadmap UX85–UX88 | Comparar cidades-base

## Problema validado
A tela pública Explorar > Comparar bases mistura duas atividades (Cidades sugeridas e Comparação personalizada), confirmação de escopo, matriz histórica, pesquisas pendentes, cards longos, seleção de bases e handoffs para mapa, perfil, orçamento e roteiro. A ordem atual esconde o objetivo principal.

## Jornada-alvo
1. Confirmar ou revisar os destinos da temporada europeia (sem inferir etapa pelo país).
2. Conhecer bases candidatas com resumo documental curto, sem ranking global.
3. Selecionar 2–3 bases para comparar lado a lado (até 5 no avançado).
4. Avaliar matriz de tempos conhecidos, lacunas e limitações em escopo idêntico.
5. Investigar uma base no mapa/perfil e simular custo; salvar qualquer decisão apenas pelo fluxo canônico.

## Quatro PRs, implementação serial
- UX85 — Entrada única guiada, escopo e shell de navegação (P1)
- UX86 — Cards de candidatas + seleção sem duplicação (P2; depende de UX85)
- UX87 — Matriz lado a lado + evidência sob demanda (P3; depende de UX85/UX86)
- UX88 — Ações contextuais, simulação REC04 e validação responsiva (P4; depende de UX87)

Cada branch nasce da main atual apenas com o prompt. Implementar a sequência de forma serial e atualizar cada branch a partir da main após integração do PR anterior. As quatro propostas ficam em draft até o usuário fazer review dos prompts. NÃO interpretar CI verde dos prompts como CI da implementação.

## Contratos não negociáveis
- Preservar ux64_navigation_model.PUBLIC_TASKS e TARGETS, ux502_interests, rec03a_scope/DRAFT/ACTIVITY/INTENT/IDENTITY, rec03b_handoffs CHOICE/CONTEXT/PREVIOUS/MANUAL_KEYS, ux503_bases/ux503_visible_destinations, REC04 e TripPlan.
- Projeções recomendadas pela REC02 NÃO provam viabilidade, custo total, última milha, retorno ou horários de 2027. Histórico, referência indicativa, acesso local e no_time são quatro conceitos distintos. Sem substituir desconhecido por zero, sem ranking arbitrário nem alegar reserva.
- Nenhuma seleção de pesquisa altera base oficial, wishlist, roteiro ou orçamento persistidos. Alterações só em callbacks explícitos canônicos.
- Design System UX81: page_header, section_heading, kpi_cards, next_action variantes fortes e compactas; nunca criar tema paralelo nem usar CSS global frágil.
- Conteúdo importante antes de detalhes técnicos; mantenha acessibilidade WCAG AA, desktop/tablet/mobile 1440/768/390, foco/teclado e ausência de overflow na página.

## Testes e gates por PR
Executar python -m compileall -q . e python -m unittest discover -s tests -v; verificar GitHub Actions no HEAD. Testar alternâncias manual/guiado, escopo editado/stale, OAuth/identidade, seleção, recuperação de filtros, categoria de evidência, fontes e REC03B/REC04. Exigir navegação real em navegador para validação visual; se indisponível registrar explicitamente.
