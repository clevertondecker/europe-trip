# UX91 — Minha lista enxuta e conectada ao roteiro

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
A wishlist mistura prioridades, salvamento, recuperação, comparação de bases e seleção de passeios. A ação seguinte deve ser inequívoca.

## Arquivos
`ux502_destination_interests_ui.py`, `ux502_destination_interests_model.py`, `ux504_guided_journey_ui.py`, `ux64_navigation_model.py`, `ux_planning_journey_ui.py`, `continuity_ui.py`, `private_continuity_store.py`, testes UX502/UX83.

## Implementação solicitada
1. Abrir em **lista compacta, inclusive para dezenas de destinos**: nome/localização, prioridade editável, elegibilidade resumida e miniatura opcional quando existente; detalhes e remoção como ações secundárias discretas, sem cartão fotográfico extenso ou múltiplos botões por item.
2. Um CTA principal contextual **Montar roteiro com meus destinos** (ou **Revisar meu roteiro** se já houver itens) e secundária **Comparar cidades-base**. Mostrar quem é elegível e quem ainda só pode ser pesquisado.
3. Reutilizar integralmente a UI e os contratos reais do #206 e do arquivo completo privado: status salvo, alterações pendentes, falha/conflito de versão, exportação de emergência, importação JSON legado e restauração de backup completo **com prévia e confirmação**. Não criar outro componente de persistência e não tratar store configurado como escrita confirmada. Não esconder a única cópia segura.
4. Handoff usa wishlist UX502 e mecanismos atuais de planejamento, sem criar outro editor, duplicar visitas, mudar base oficial ou exigir datas. Retorno à wishlist conserva prioridades/filtros.
5. Estado vazio ajuda a começar em Descobrir; dezenas de destinos não criam 34 cartões longos.

## Testes/aceite
Lista vazia, uma e várias prioridades, sincronização bem-sucedida, falha/conflito e sessão expirada, importação legada, ida/volta ao Planejar e confirmação de inclusão. Assertiva forte de nenhuma mutação involuntária no TripPlan; AppTest do fluxo com controles reais. UX90 e UX92 devem consumir a mesma fonte UX502.

## Fora de escopo
Não implementar catálogo UX90, calendário UX92 ou nova persistência.
## Regra de próximo passo por estado (aceite P1)
- Destinos elegíveis não incluídos: **Montar roteiro com meus destinos**.
- Roteiro já iniciado: **Revisar meu roteiro**, inclusive quando existem destinos adicionais.
- Nenhum destino elegível: explicar condição e mostrar **Continuar descobrindo** como ação principal, sem botão de incluir sem efeito.
- **Comparar cidades-base** é opcional e secundário, não uma etapa obrigatória.

## Matriz de implementação mínima
- **Já existe:** prioridades UX502, handoff de montagem/revisão, mecanismos de nuvem e recuperação do #206. **Ajustar:** ordem, densidade e CTA conforme estado.
- **Preservar:** edição, restauração confirmada, rascunhos, fallback offline. **Desnecessário:** nova persistência ou editor alternativo.
