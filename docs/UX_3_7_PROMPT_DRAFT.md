# Prompt — UX 3.7: Das pesquisas aos próximos passos

**Estado:** RASCUNHO A · NÃO FINALIZADO (aguarda revisão UX independente)  
**Evidências:** `base_coverage_model.py`, `base_weight_coverage_ui.py`, `outing_cost_evidence.py`, `city_decision_ui.py`, `ux_navigation.py`, `AGENTS_COORDINATION.md` e [issue #31](https://github.com/clevertondecker/europe-trip/issues/31).  
**Pré-requisito:** auditar o calendário UX 3.5 real; não replicar alertas diários já existentes.

## Problema e objetivo

A aplicação já distingue trajetos observados, tarifas históricas e dados não pesquisados. Entretanto, o usuário ainda precisa decidir **qual pesquisa resolver primeiro** para escolher base, organizar Itália e França e tornar os passeios realizáveis.

**Resultado humano:** ver, no contexto de cada decisão importante, *o que impede avançar, por que importa, onde procurar e o que pode ser decidido sem certeza absoluta*.

## Prompt de implementação proposto

1. Construir um **grafo leve de decisões**, ancorado em entidades já existentes: cidade-base oficial e alternativas, duração, etapa, passeio, data planejada, hospedagem, ligação ferroviária e orçamento. Cada pendência indica `assunto`, `impacto`, `referência`, `fonte`, `atualizado_em`, `dado_faltante`, `próxima_ação`, `status`, `natureza_da_incerteza`. Não criar mais uma tabela genérica sem vínculos.
2. **Priorizar por decisão desbloqueada**, não por contagem de links, quantidade de avisos ou score inventado. Por exemplo: antes de confirmar um bate-volta, verificar trem de retorno, último trecho e tempo mínimo; antes de comparar base, exigir aluguel para dois por janela equivalente.
3. Mostrar no **Resumo** somente 3–5 próximos passos relevantes; em **Meu roteiro → Organizar viagem**, mostrar pendências específicas da visita/data; em **Explorar → Comparar**, mostrar insuficiências que impedem comparar as bases; em **Orçamento**, mostrar falta de custos com impacto. Não criar aba principal nova.
4. Um item de pendência deve **abrir diretamente o destino/passeio/alternativa** que o originou e permitir voltar com uma ação ao contexto anterior. O filtro de pesquisa e estado de edição permanecem intactos.
5. Distinguir **pendente de pesquisa**, **pesquisado historicamente**, **verificação atual necessária**, **decidido pelo viajante**, **reserva manual declarada**. Não equiparar ausência de fonte a impossibilidade.
6. Reaproveitar dados versionados de `base_coverage_model`, `base_city_rail_evidence_expanded` e `outing_cost_evidence`. Nenhuma fonte histórica de 2026 deve ser apresentada como confirmação para 2027.
7. Permitir marcar `não relevante para nós` de forma **reversível** e contextual, sem excluir dados oficiais ou esconder risco de agenda. Em decisões críticas, a dispensa deve trazer explicação.
8. Criar **vista por decisão** em vez de vários checklists duplicados. Estilo progressivo: resumo curto + `Ver justificativa e fonte` somente sob demanda.

## Guardrails

- Não alterar `TripPlan` ou decisões do Drive automaticamente. Se houver persistência de pendências, usar o storage privado aprovado em UX 3.6 ou backup local com consentimento.
- **Sem avisos alarmistas** nem excesso de badges; o usuário precisa compreender implicação prática, não uma suposta nota de maturidade.
- Não interpretar legislação/autorizações de permanência como garantidas; requisitos legais precisam de fonte oficial atual e status informativo.
- Não transformar o produto em leitor de notícias ou rastreador genérico.
- Pendências de segurança e retorno não desaparecem só porque uma etapa foi marcada `organizada` no calendário.

## Aceite

- Ao comparar Offenburg e Mulhouse, um trajeto sem retorno documentado cria **uma** pendência contextual, mesmo se houver várias atrações no destino.
- Selecionar uma pendência abre a decisão correspondente e voltar restaura o editor sem retornar ao início.
- Dados ferroviários sem pesquisa não geram `sem ligação`, `impossível` ou custo 0.
- A mesma pendência não aparece com contagens conflitantes em três páginas.
- Após resolver a fonte (sem alterar o plano), a pendência muda de status corretamente; quando fonte fica obsoleta, reabre.
- Top 3 próximos passos no resumo provêm de bloqueios reais do plano, não de itens aleatórios do catálogo.
- Avaliar com usuários leigos: identificar em até duas ações o dado mais importante para uma decisão e explicar a diferença entre `não pesquisado` e `não viável`.
- Testes de módulo puro, versionamento de fonte, integração Streamlit, teclado/mobile, regressão de calendário e orçamento.

## Alternativa menor / condição de rejeição

Se a UX 3.5 já oferecer indicadores suficientes e a navegação contextual funcionar, reduzir para um **componente reutilizável de próximos passos** com links internos. Não criar novo sistema de workflow, pontuação, feed ou notificações se apenas duplicar informação.

**Entregável futuro:** PR específico, evidências rastreáveis, testes, sem merge automático.
