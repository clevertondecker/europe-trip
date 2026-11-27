# UX132C4 — Seletor de comparação somente após confirmação do escopo

## Problema observado
Em produção, Comparar bases exibe Área da pesquisa antes de confirmar destinos; ambas as opções levam ao mesmo formulário. O usuário interpreta a mudança como botão sem efeito.

## Solução incremental
- Montar o seletor ux112_active_view apenas quando o escopo estiver pronto, não houver edição pendente e a análise tiver sido carregada. Posicioná-lo após o resumo dos destinos confirmados e antes dos resultados.
- Antes da confirmação, formulário único, CTA claro; na edição, preservar cancelamento e rascunho. Não limpar shadow, CHOICE, filtros ou handoffs. Respeitar modo anterior válido, inclusive intenção manual; primeiro acesso padrão Explorar alternativas. Manter deselect como no-op. Escopo vazio ou desatualizado não executa REC02 nem apresenta seletor.
- Sem alteração em motor, datasets, TripPlan, wishlist, persistência, orçamento ou navegação pública. Nenhum novo fluxo ou widget duplicado.
- Adaptar testes que interagiam com seletor indisponível antes da confirmação para testar sua ausência e preservação do modo; manter demais assertions. AppTest com entrada inicial, confirmação, alternância, edição/cancelamento/reconfirmação, navegação, intenção manual e escopo pendente. Suite completa e CI antes do merge, QA visual quando disponível. PR independente do DATA26A #274, manter draft.
