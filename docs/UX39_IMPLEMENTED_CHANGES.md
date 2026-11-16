# UX 3.9 — Refino de navegação, acessibilidade e continuidade (proposta)

## Base e dependência

Branch criada sobre `main` após PR #52, com auditoria documentada separadamente em `audit/ux39-user-journeys-2026-11`. Nenhum contrato de `TripPlan`, modelo financeiro, schema JSON de GCS, evidência ferroviária ou configuração de OAuth foi modificado. Alterações restritas a UI, CSS, README e testes.

## Antes e depois com evidência de código

| Jornada / problema | Antes | Depois | Verificação |
|---|---|---|---|
| Edição de cotações | Uma única família de chaves `ux38_edit_*` para itens diferentes; risco de conteúdo anterior permanecer em widget | `_form_namespace(quote)` distingue cada cotação por UUID e preserva campos do próprio item | `test_quote_form_keys_are_distinct_per_quote` |
| Cidade de uma cotação | Input `Cidade/destino (ID)` exigia código interno | Selectbox com nomes canônicos de bases/destinos, mantendo IDs legados e opção sem cidade | `test_location_picker_uses_names_and_keeps_legacy_value` |
| Resumo financeiro | Para carregar cotações era preciso ir a Detalhamento e voltar | Resumo reutiliza `_availability()`, leitura privada sob demanda, sem escrita automática | `test_summary_uses_same_contextual_loader_as_details`, AppTest |
| Comparar bases | Quatro `st.metric` por cidade alternativa | Uma frase linear com as mesmas quatro contagens, bom para telas estreitas e leitores de tela | AppTest de comparação + contagens existentes |
| Documento inicial | README descrevia workspace antigo de novembro | Documentação das quatro áreas atuais, cotações, estudos, backup e limites | Revisão de diff |
| Mobile / acessibilidade | Já havia CSS responsivo, mas alvo de toque de segmented control de 42 px em telas estreitas | Alvo mínimo de 44 px para botões relevantes, foco visível e suporte a redução de movimento, sem alteração global de layout | Inspeção de CSS; **screenshots ainda necessários** |

## Revisões

**Revisão A — engenharia e produto (sobre alterações concretas):** A proposta preserva dados canônicos, modelos financeiros e acesso GCS. A principal melhoria de confiabilidade visual está em separar chaves de widgets para cotações; o resumo inclui somente leitura explicitamente solicitada. A UI não agrega novas abas ou controle de pagamentos. Testes automatizados validam contratos de estado e navegação, não layouts reais.

**Revisão B — análise crítica com critérios de UX (não revisão por agente independente):**
- **Aprovar conceitualmente** seletor por nome, leitura do Resumo sem desvio, texto linear nos dados comparativos.
- **Alertar:** seleção de destino pode conter muitos lugares; medir em celular. Se a lista for difícil, implementar busca/agrupamento simples, sem duplicar tela.
- **Alertar:** CSS usa seletores nativos `data-testid`; verificar a versão Streamlit no navegador porque tais seletores podem mudar.
- **Vetar no escopo 3.9:** migração de schemas, mudança de cálculos, nova navegação principal e dashboards genéricos.
- **Gate pendente:** **não há evidência de aprovação de um segundo agente isolado para o SHA final**; obter revisão externa especializada de UX quando disponível. Uma segunda análise do mesmo assistente não atende independência estrita.

## Verificação e limites

Rodar `python -m compileall -q .` e `python -m unittest discover -s tests -v` no CI. Testar desktop (1280px), tablet (768px), celular (375px) e teclado em navegador real autorizado, incluindo retorno Orçamento → Meu roteiro, comparação de cidades, cadastro/edição de duas cotações e confirmação do status privado entre duas sessões. Não inventar tempo de execução ou ganhos sem medir.

O antigo plano `docs/UX_3_9_PROMPT_DRAFT.md` em PR #41 permanece histórico; não reimplementar UX 3.5–3.8. `UX 3.10` não foi iniciada por falta de evidência de necessidade.

**Publicação:** PR draft; nenhum merge/deploy sem aprovação do proprietário.
