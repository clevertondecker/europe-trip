# Nossa Europa 2027 — Roadmap de simplificação: UX85 + UX87 (revisado)

**Revisão adversarial:** 2026-11-22. Esta é uma especificação, sem implementação funcional nesta série de PRs.

## Decisão de arquitetura

A meta não é um wizard de quatro etapas. É eliminar decisões redundantes, reaproveitando os estados atuais. A jornada pública deve ser **uma única atividade Explorar > Comparar bases** na qual resultados são úteis antes de configurar ferramentas avançadas.

- **PR #201 / UX85 revisado (incorpora UX86 / #202):** entrada única, escopo confirmado sem burocracia, cidades mostradas uma vez e seleção no próprio resultado.
- **PR #203 / UX87 revisado (incorpora UX88 / #204):** mesma seleção alimenta imediatamente a matriz; ações de perfil, mapa, simulação e retorno são opcionais e contextuais.
- **PRs #202 e #204:** especificações originais absorvidas; históricos preservados, sem implementação adicional independente. Não abrir novos PRs.

## Caminho mais curto

**Tenho destinos na wishlist → Comparar bases → Vejo cidades plausíveis e as razões.**

- Escopo REC02 já válido: **zero confirmações** para ver sugestões.
- Escopo ausente/inválido: os interesses ativos são uma **proposta editável**, não uma decisão autoaprovada; **uma** confirmação `confirm_scope`. A etapa `europe_season` nunca é inferida silenciosamente do país.
- Duas cidades selecionadas: mostrar comparação **na mesma atividade**, sem segundo formulário, segundo modo ou CTA para abrir outra página.
- Uma cidade selecionada: perfil/mapa/custo ficam opcionais e independentes da comparação.
- Planejar e Orçamento continuam alcançáveis sem escolher base e sem completar qualquer fluxo linear.

## Testes de aceitação da simplicidade

| Situação | Resultado observável |
|---|---|
| Primeiro acesso com wishlist | Proposta de escopo editável, 1 CTA, sem rádio de modo |
| Escopo válido retomado | Cidades exibidas imediatamente; sem confirmação repetida |
| Wishlist alterada | Novos destinos aguardam revisão; atuais reconciliados conforme modelo |
| Cidade com dados limitados | Lacunas visíveis, sem ranking ou zeros falsos |
| Uma cidade selecionada | Investigar/simular opcionalmente; sem necessidade de segunda base |
| Duas cidades selecionadas | Matriz atualizada na página, sem navegar/manual duplicado |
| Quatro ou cinco cidades | Comparação possível segundo contrato existente |
| Retorno de perfil/mapa/orçamento | Seleção e escopo válidos preservados no contexto de sessão |
| Identidade/plano mudou | Contexto inválido tratado, sem dados antigos reaproveitados |
| Retorno ao roteiro | Inclusão e salvamento sem datas seguem disponíveis |

## Contratos e riscos
- `TripPlan`, wishlist, recomendações REC02, `confirm_scope/reconcile_scope`, REC03A/REC03B, REC04, REC05 e UX64 permanecem intactos.
- Nenhum ranking global ou equivalência indevida entre `historical`, `reference_only`, `local` e `no_time`.
- `app.py` deve parar de antepor ajustes de simulação, barra de atividade legada e título duplicado aos resultados de comparação.
- Evitar novo `shortlist` ou estados paralelos; usar `rec03b_handoffs.CHOICE` para bases e `rec03a_scope` para destinos.
- Escopo e seleção de pesquisa são transitórios; não prometer persistência permanente nem decidir cidade-base oficial.
- QA: compilação, suíte unittest, CI por HEAD, AppTest de continuidade e inspeção real de navegador a 1440/768/390. CI de PR documental não vale como implementação validada.

## Sequência e status
1. Usuário revisa e aprova a proposta simplificada dos PRs #201 e #203.
2. Implementar e testar **#201**; só então considerar merge.
3. Atualizar **#203** com a `main` após #201; implementar matriz e handoffs, testá-los, e entregar para review.
4. Sem merge automático. Não alterar PRs históricos sem necessidade.
