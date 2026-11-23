# UX111 — Seleção de cidades-base com feedback e retorno à comparação

## Contexto
Em Explorar → Comparar bases, o usuário escolhe de 2 a 5 cidades através dos cartões existentes. A comparação UX87 é renderizada **acima** dos cartões. Depois de marcar outro cartão, o usuário não percebe facilmente que a cidade entrou nem como voltar à tabela atualizada.

## Contrato de implementação
- Reutilizar exclusivamente `CHOICE` para identidade da seleção, nunca criar multiselect concorrente, segundo modelo ou nova persistência.
- Feedback textual compacto de inclusão/remoção no cartão e painel próximo aos cartões; contagem dinâmica 0–5 e vagas restantes.
- Permitir remoção individual nos botões nativos com sincronização do checkbox no rerun.
- Exibir painel com cidades selecionadas e ação **Ver comparação atualizada** (somente com 2+ cidades).
- Inserir alvos HTML simples `#ux111-comparison` e `#ux111-picker` para navegação no mesmo documento, sem JavaScript arbitrário; testar manualmente o clique no Streamlit real, porque AppTest não prova scrolling.
- Manter barra superior `selected_context()` como projeção somente-leitura do `CHOICE`, explicitando contagem.
- Não alterar `TripPlan`, pesquisa REC02/REC03/REC04/REC05, DATA23, UX87, matriz, preços, cidades oficiais, fontes ou escopo.
- Respeitar paginação e filtros; lista completa permanece no checkbox existente, sem criá-la novamente.
- Responsividade e teclado: testar 1440, 768, 390 px, foco em âncoras e remoção; CSS apenas namespace UX111.

## Aceite funcional
1. Strasbourg + Colmar → adicionar Lille → exibir três cidades, confirmação e CTA para comparação UX87 atualizada.
2. Remover Colmar → atualizar CHOICE, checkbox e painéis mantendo Strasbourg e Lille.
3. Quinta cidade aceita; sexta desabilitada até remoção.
4. Uma cidade permite investigação individual, mas não o CTA de comparação.
5. Troca de busca/página e escopo não contamina os resultados nem modifica o plano oficial.
6. `fixed_city=None` e handoffs de perfil/mapa/simulação continuam funcionando.

## Verificações
- `python -m compileall -q .`
- `python tools/validate_research_data.py`
- `python -m unittest discover -s tests -v`
- Checar o HEAD exato na CI; evidência de AppTest não substitui teste visual/browser da âncora.
- Manter PR draft até CI verde, depois revisão final sem merge automático.
