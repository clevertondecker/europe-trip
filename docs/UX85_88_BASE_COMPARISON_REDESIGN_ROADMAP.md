# Nossa Europa 2027 — Decisão de UX | PRs #201 e #203

**Status:** UX85/#201 contém código funcional em validação; UX87/#203 continua como especificação dependente. #202 está absorvido por #201; #204 por #203 (ambos fechados). Sem wizard, novo router, ranking ou seleção paralela.

## Decisão de produto
**Pergunta do usuário:** "Tenho destinos que gostaria de conhecer; quais cidades-base vale investigar para visitá-los?"

**Jornada livre:** destinos desejados → cidades candidatas → comparação compreensível (opcional) → mapa/perfil/simulação (opcionais). Planejar, salvar sem datas ou escolher base definitiva nunca dependem de completar essa sequência.

## Duas entregas e comportamento entre elas
| Entrega | O que fica disponível | Dependência |
|---|---|---|
| **#201 / UX85 + UX86** | Entrada única, confirmação quando necessária, até 4 destaques REC02, busca demais cidades, cartões deduplicados e seleção `CHOICE`. Para **2–5 bases**, uma CTA usa temporariamente o **handoff UX503 existente** com a mesma seleção; já produz comparação real. Uma cidade permite investigação isolada. | `main` atual |
| **#203 / UX87 + UX88** | Com **2–5 bases**, resumo de evidências + matriz **na mesma atividade** sem clique adicional. Região de comparação perto da seleção, feedback não intrusivo, matriz detalhada sob demanda; perfil/mapa/simulação contextual de uma base. Remove a CTA temporária de #201, não o estado. | #201 implementado, testado e integrado |

**Por que o handoff transitório é menor risco:** `rec03b_handoffs.queue_handoff(kind="manual")` já valida escopo, 2–5 bases e `PREVIOUS`. Não requer feature flag, terceira seleção ou nova UI paralela. A etapa temporária exige um clique para entrar no comparador legado; #203 elimina esse clique depois.

## As quatro decisões de UX
1. **Escopo:** `ready` → resultados imediatos; primeira visita/pendência → uma confirmação `confirm_scope`; novos desejos não entram silenciosamente; nada é inferido pelo país.
2. **Catálogo:** destacar apenas referências REC02 sustentadas (até 4 visíveis); demais acessíveis via busca/filtro; não preencher vagas com ranking arbitrário, não duplicar cartões, manter seleção fora do filtro.
3. **Comparação perceptível:** ao selecionar duas bases, mostrar um **resumo perto da seleção**, sem rolagem forçada; manter uma ação curta "Ver comparação" para ir à matriz se ela estiver fora da área visível. No mobile, evitar tabela larga na página; comparação detalhada opcional após um primeiro resumo útil.
4. **Financeiro proporcional:** usar `rec04_candidate_capabilities`. `scenario_selectable` ≠ `detailed_budget_supported` ≠ `official_plan_supported`. Cenário hipotético ≠ cotação local de moradia; custo desconhecido permanece desconhecido.

## Invariantes e riscos conhecidos
- `CHOICE` é a fonte de seleção; `rec03a_scope` é fonte de destinos confirmados. Nenhuma shortlist separada, alteração automática de base oficial, wishlist, `TripPlan`, orçamento ou persistência.
- `reconcile_scope` preserva segurança de revisão e identidade. Escopo de sessão não tem recuperação permanente garantida.
- `historical`, `reference_only`, `local` e `no_time` não são intercambiáveis; tempo mínimo de ida não prova retorno/frequência/última milha e não mede custo completo.
- A comparação UX503 pode usar categorias e coberturas diferentes da REC02: validar catálogo e semântica; não misturar scores ou dividir por zero.
- `app.py` atualmente mostra ajustes avançados e título repetido antes de Comparar bases; corrigir na UX85 sem afetar outras abas.
- #203 deve atualizar a branch com #201 integrado antes de implementar, remover CTA transitória e manter `PREVIOUS/MANUAL_KEYS` apenas para acesso manual legado.

## Cenários de aceite
| Situação | Esperado |
|---|---|
| Primeira visita com wishlist | Uma confirmação, depois cidades |
| Escopo `ready` | Sugestões imediatas, nenhuma confirmação |
| Sem destaques | Sem ranking artificial; pesquisar todas as candidatas |
| Muitas candidatas | Até quatro destaques iniciais; acesso simples às demais |
| Escolha de uma base | Perfil/mapa/simulação individual opcional |
| Duas bases após #201 | Handoff existente com a mesma escolha, sem segundo multiselect de entrada |
| Duas bases após #203 | Resumo comparativo visível perto da seleção, matriz na mesma atividade sem confirmação |
| Quatro/cinco bases | Comparação possível; seleção anterior não é truncada |
| Wishlist/identidade alterada | Reconciliação explícita; sem reaproveitar contexto inválido |
| Sem evidência suficiente | Lacunas claras, nenhuma conclusão artificial |
| Retorno de orçamento | Escopo e seleção válidos restaurados apenas durante a sessão |
| Roteiro independente | Pode incluir/salvar sem base definitiva nem datas |

## Gates
Após revisão dos prompts, implementar primeiro #201 e validar AppTest, suíte, CI e navegador 1440/768/390. Integrar #201 somente após review. Então atualizar e implementar #203; validar novamente o conjunto. **Não fazer merge automático nem marcar documentos como código pronto.**
