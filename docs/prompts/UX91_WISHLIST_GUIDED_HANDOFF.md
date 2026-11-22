# UX91 — Minha lista enxuta e conectada ao roteiro

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
A wishlist mistura prioridades, salvamento, recuperação, comparação de bases e seleção de passeios. A ação seguinte deve ser inequívoca.

## Arquivos
`ux502_destination_interests_ui.py`, `ux502_destination_interests_model.py`, `ux504_guided_journey_ui.py`, `ux64_navigation_model.py`, `ux_planning_journey_ui.py`, `continuity_ui.py`, `private_continuity_store.py`, testes UX502/UX83.

## Implementação solicitada
1. Abrir em lista compacta: foto miniatura quando existente, nome/país, prioridade, editar/remover, link a detalhes, contagem de desejos e imperdíveis.
2. Um CTA principal contextual **Montar roteiro com meus destinos** (ou **Revisar meu roteiro** se já houver itens) e secundária **Comparar cidades-base**. Mostrar quem é elegível e quem ainda só pode ser pesquisado.
3. Salvo/pendente/erro correspondem ao retorno **real** do armazenamento privado. Manter o contrato de recuperação do PR #206: exportação de emergência em falha/conflito; importação de JSON legado sob demanda e com confirmação de substituição. Não esconder a única cópia segura.
4. Handoff usa wishlist UX502 e mecanismos atuais de planejamento, sem criar outro editor, duplicar visitas, mudar base oficial ou exigir datas. Retorno à wishlist conserva prioridades/filtros.
5. Estado vazio ajuda a começar em Descobrir; dezenas de destinos não criam 34 cartões longos.

## Testes/aceite
Lista vazia, uma e várias prioridades, sincronização bem-sucedida, falha/conflito e sessão expirada, importação legada, ida/volta ao Planejar e confirmação de inclusão. Assertiva forte de nenhuma mutação involuntária no TripPlan; AppTest do fluxo com controles reais. UX90 e UX92 devem consumir a mesma fonte UX502.

## Fora de escopo
Não implementar catálogo UX90, calendário UX92 ou nova persistência.