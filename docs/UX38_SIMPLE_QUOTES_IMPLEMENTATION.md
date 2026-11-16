# UX 3.8 — Cotações pesquisadas, sem pagamentos

## Escopo da entrega

Novo registro privado de **pesquisas de preços** em `quote_research_model.py` e `quote_research_ui.py`. O acesso ocorre apenas nas abas existentes **Orçamento → Detalhamento** (CRUD, favoritas, comparações de escopo idêntico) e **Resumo financeiro** (prévia prudente de hospedagem). Não existe registro de pagamento, reserva, fluxo de caixa ou compromisso assumido.

## Modelagem e segurança

- `PrivateQuoteStore` reutiliza `PrivateArchiveStore`, identidade de proprietário verificada pela UX3.6 e o bucket existente. O objeto separado é `ux36/owners/<hash>/ux38_quotes.json`. Nunca escreve no GitHub público.
- `schema_version=1`, UUID, `plan_id`, revisão de coleção e `ifGenerationMatch`; limite de 60 cotações / 350 KB, operações explícitas; conflito exige recarregar. Sem migração destrutiva de backups e sem alteração do `TripPlan`.
- Preços decimais serializados como **texto**; moedas BRL, EUR, CHF; tipo de unidade e quantidade explícitos; indicação de fonte opcional sem fingir que foi verificada. Datas da pesquisa e períodos não são garantias de disponibilidade em 2027.
- Preferida/favorita é somente marcação local de pesquisa; não equivale a reserva ou aprovação de despesa.

## Comparação financeira limitada e segura

- Em **Resumo financeiro**, para cotação de **estadia francesa completa** coincidente com o plano atual, cidade-base oficial e dois viajantes, exibe-se **diferença hipotética contra a verba já prevista de moradia**, nunca soma da cotação à verba. EUR exige câmbio ilustrativo **informado explicitamente**; CHF não entra na projeção sem câmbio específico; BRL pode ser comparado diretamente.
- Cotações alternativas só apresentam diferença numérica quando possuem **mesma categoria, cidade, unidade, moeda, quantidade, viajantes e período**. Outros itens ficam listados sem efeito numérico no orçamento.
- Não usar `travel_fares_by_visit()` como cotação real de ida e volta, porque esse helper faz hipótese usando o preço de ida. Nenhum custo ferroviário desconhecido vira zero.
- `calculate_scenario`, `unified_budget`, `finance_margin_metrics` e orçamentos R$ 60 mil/R$ 70 mil são somente leitura.

## Testes

`tests/test_ux38_simple_quotes.py`: CRUD, validação Decimal, período, moeda, comparações legítimas e ilegítimas, prevenção de dupla contagem, CAS, importação inválida, preservação do plano e AppTest de ambas as abas.

**Limitações declaradas:** sem monitoramento de preço, nenhuma disponibilidade/validade 2027 confirmada, comparação de orçamento somente da estadia completa da França, sem teste de GCS de produção. Validar em navegador real e duas sessões autenticadas após autorização de publicação.

**Dependência:** PR de auditoria pós-merge; se ele descobrir defeitos críticos, corrigir e revalidar antes de mesclar a UX3.8. Nenhum merge automático.
