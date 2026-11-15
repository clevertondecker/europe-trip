# Gerenciador visual de passeios — Nossa Europa 2027

Data da implementação: 15/11/2026 · Streamlit / Python, sem LLM.

## O que foi implementado (8 steps)
1. **Edição isolada:** `scenario_editor_model.py` representa uma proposta em edição com vínculo ao ID/revisão do plano oficial e três rascunhos independentes, um por estilo. Inclui controle de obsolescência, desfazer até 10 edições e proteção de passeios já aprovados.
2. **Cards individuais:** `scenario_board_ui.py` renderiza cada destino do cenário com foto cadastrada/licenciada, nome, país, resumo das atrações incluídas, trem histórico estação-a-estação, subtotal conhecido para duas pessoas, pendências e links às fontes. Quando não há foto válida, utiliza texto neutro.
3. **Quadro e categorias de gasto:** seção **Passeios incluídos nos estilos de viagem** contém quadro por perfil (Econômico / Equilibrado / Aproveitar ao máximo), indicadores de destinos, atrações, gastos conhecidos, margem e provisão. Detalhes por destino mostram transporte e ingressos, custos condicionais e pendentes. Detalhamento agregado de trens e ingressos separado de alimentação, transporte local e hospedagem ainda não cotados.
4. **Ações:** cada card permite **Editar atrações** e **Remover passeio** quando ainda não aprovado. **Adicionar outro passeio** abre seletor do catálogo com fotografia e atrações. Passeios oficiais ficam bloqueados para edição no rascunho, devendo ser alterados em **Explorar atrações**. Há botão para desfazer e restaurar sugestão original.
5. **Recálculo financeiro:** todas as alterações recalculam `attractions_model.package_cost()` e `advisor_finance.advisor_projection()`, sem uma segunda implementação de orçamento. Trem cobrado uma única vez por destino e não por atração; EUR/CHF separados. Cálculos usam dados históricos, não tarifa garantida de 2027.
6. **Antes/depois:** simulações mostram delta nos custos conhecidos em moeda original e BRL e permitem visualizar composição alterada. **Redução do subtotal não é economia garantida**: a verba de excursões do orçamento-base permanece provisionada, e somente excedente conhecido impacta o total projetado.
7. **Revisão e confirmação:** `recommended_itineraries.approve_profile_scenario()` aplica mudança somente após dois passos explícitos: **Revisar e aplicar este roteiro** e **Confirmar aplicação**. Rascunhos não alteram `advisor_plan` e nunca geram escrita no GitHub sozinhos. A aprovação efetiva passa pela política de salvamento Google/GitHub atual. Propostas obsoletas não são aplicadas.
8. **Testes:** `tests/test_scenario_board.py` verifica ações puras, ausência de dupla tarifa, atualização, undo, aprovação e revisão obsoleta. `tests/test_scenario_board_ui.py` testa interação real Streamlit de remover e desfazer sem alterar plano oficial. Compilação dos novos módulos integrada ao GitHub Actions.

## Como utilizar
1. Abra https://nossa-europa-2027.streamlit.app/ → **Roteiro → Consultor inteligente**.
2. Na seção **Passeios incluídos nos estilos de viagem**, escolha o perfil desejado.
3. Navegue pelos cards com fotografias; em **Ver despesas, ingressos e fontes**, confira valores históricos e pendências.
4. Clique **Remover passeio** ou **Editar atrações deste passeio**, ou em **Adicionar outro passeio** para buscar lugares no catálogo.
5. Observe as métricas, o detalhamento de despesas e as diferenças de custos. Se precisar, clique **Desfazer última edição**.
6. Quando estiver satisfeito, escolha **Revisar e aplicar este roteiro**, revise o aviso e depois **Confirmar aplicação**.
7. Para persistir após a aprovação, use **Salvar planejamento** (ou a opção previamente autorizada de salvamento automático).

## Convenções e limitações importantes
- Valores são históricos (principalmente 2026); horários, reservas, bilhetes e retornos para 2027 não estão confirmados.
- O orçamento total mantém uma provisão de excursões. Retirar uma visita pode reduzir o subtotal conhecido sem reduzir o valor total projetado.
- Um destino com duas atrações envolve **uma visita/uma passagem de trem conhecida**; múltiplas viagens ao mesmo lugar em datas diferentes ainda não são modeladas pelo editor.
- Gastos locais, refeições extras e pernoites sem valores verificados aparecem como pendentes, não como R$ 0.
- Passeios já oficialmente escolhidos são bloqueados para remoção no editor de propostas: não serão apagados pelo aceite. Para modificá-los use a aba Explorar atrações.
- A aplicação tem aparência de *cards Jira*, sem dependência de biblioteca de drag-and-drop.
- O repositório é público; planos salvos podem ser visualizados por terceiros. Não incluir dados confidenciais.
- O Google Drive permanece somente leitura; a decisão D-004 da cidade-base permanece em aberto.
- Os testes CI + Streamlit AppTest não substituem inspeção visual do Streamlit hospedado.

## Arquivos criados/alterados
`scenario_editor_model.py`, `scenario_board_ui.py`, `discovery_ui.py`, `tests/test_scenario_board.py`, `tests/test_scenario_board_ui.py`, `.github/workflows/validate.yml`.
