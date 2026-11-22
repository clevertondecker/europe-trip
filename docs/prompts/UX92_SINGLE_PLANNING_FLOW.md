# UX92 — Planejador progressivo único

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
Planejar combina Visão geral, Meus destinos, Organizar, três opções de calendário, painéis antigos, editores e ferramentas complementares que parecem processos concorrentes.

## Arquivos
`app.py`, `ux_planning_journey_ui.py`, `ux_planning_journey_model.py`, `itinerary_flow_ui.py`, `itinerary_flow_model.py`, `smart_calendar_ui.py`, `ux63_timeline_ui.py`, `ux48_weekend_groups_ui.py`, `ux61_destination_board_ui.py`, `planning_session.py`, `continuity_ui.py` e testes.

## Implementação solicitada
1. **Visão geral**: status resumido, destinos/atrações escolhidos, progresso real, salvamento confirmado, apenas uma CTA **Continuar meu roteiro**. Painéis antigos sob demanda.
2. **Meus destinos**: incluir a partir da wishlist, selecionar atrações, revisar e salvar sem exigir datas, cidade-base definitiva ou reservas. O usuário vê sempre a distinção desejado/incluído/organizado/reservado. Usar o único commit canônico de passeios e IDs existentes.
3. **Organizar**: mostrar por padrão uma única interface de visitas por etapa Itália/temporada europeia, agrupando períodos/datas com edição contextual. Calendário inteligente/completo preservados como modos avançados, não planos alternativos. Períodos/datas são opcionais.
4. Um CTA primário por fase: incluir, revisar, organizar ou salvar. Nunca duplicar editores nem atualizar widgets instanciados em rerun. Manter handoffs a Explorar, Comparar bases e Orçamento sem alterar o plano por acidente.
5. Reconciliação de revisão e salvamento: conflito/erro têm feedback, rascunhos recuperáveis, confirmação real da nuvem e nenhuma perda silenciosa.

## Testes/aceite
0/1/N destinos, inclusão idempotente, Itália/França, mudança de etapas, datas opcionais, edição e retorno, persistência/restauração/falha/conflito, navegação, preservação dos dados CHOICE/REC02/REC03/UX83, AppTests e navegador real. **Fluxo esperado: wishlist → incluir → revisar → organizar se desejar → salvar.**

## Fora de escopo
Não alterar semântica TripPlan nem implementar reservas reais.