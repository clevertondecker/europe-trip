# UX 4.8 — Navegação atual + Destinos prioritários + Fins de semana

## Decisão de escopo
A pedido do usuário, **um único PR**, dividido por commits auditáveis, reúne três entregas:
1. Retirar o expansor visual `Acesso a ferramentas antigas deste roteiro`, sem excluir o adaptador `ux_navigation.from_legacy` ou as telas especializadas modernas.
2. Completar o catálogo canônico com `brussels`, `bruges_be` e `rotterdam`, cinco atrações verificadas por destino, coordenadas e páginas de origem.
3. Oferecer em `Meu roteiro → Organizar viagem` um planejador opcional de viagens de fim de semana que **referencia** destinos já incluídos, sem duplicar atrações ou somar tarifas.

## Catálogo
As atrações vêm de [Visit Brussels](https://www.visit.brussels/en/visitors/what-to-do/must-see-attractions), [Visit Bruges](https://www.visitbruges.be/en/things-to-do/sights) e [Visit Rotterdam](https://visitrotterdam.com/things-to-do-in-rotterdam.html), consultadas em 16/11/2026. Fotos não foram adicionadas sem confirmação de crédito/licença. Os campos de ingressos são **unknown/null**, duração uma hipótese editorial e nenhuma reserva foi declarada.

A matriz `data/base_destination_routes_2027.json` foi ampliada de 44 (4×11) para 56 (4×14) registros. Os 12 trechos novos não possuem rota completa documentada desde cada base: tempos, tarifas, retornos e última milha ficam **null**, com fonte de referência para pesquisa ferroviária posterior. Evidências históricas de operadores não são horários reserváveis de 2027.

## Arquitetura de fins de semana
`ux48_weekend_groups_model.py` define um sidecar versionado `{schema_version,plan_id,groups,rest_weekends}`. Os grupos contêm `id`, `name`, `destinations` (IDs canônicos em ordem), `period`, `start_date` opcional (sábado), `nights` (hipótese), `base_city` de referência, `notes`, `status` (`estudo` ou `planejado`, **não reservado**).

**Não houve extensão do schema do TripPlan**: `packages`, `flexible_visits`, `assignments`, revisão, datas, Itália e orçamento continuam iguais. Agrupamentos não incluem lista própria de atrações, nem preços. A organização por sábado/ domingo vem de `calendar_model.calendar_plan`, apenas quando existe data real no cenário ativo. Viagens sem data ficam em `Viagens planejadas`, sem falsa reserva de fim de semana.

**Conflitos/política de remoção (correções P1/P2):** destino só pode pertencer a um agrupamento por vez; datas agendadas no TripPlan não são alteradas. A ocupação de viagem com N pernoites cobre ao menos sábado/domingo e se estende até o dia posterior à última noite. Descansos cobrem sábado/domingo e são rejeitados caso qualquer um dos dias seja indisponível ou tenha atribuição oficial. Grupos sobrepostos são rejeitados, inclusive nas extensões de pernoite. Remover destino do agrupamento não afeta passeio canônico. Se o passeio é removido pelo editor oficial, `reconcile_removed_outings` desassocia o destino ao renderizar o planejador; um grupo vazio é excluído. Se data oficial mudou ou dois grupos passaram a conflitar, a reconciliação global mantém os grupos e limpa somente a data de rascunho incompatível, sem descartar destinos ou observações.

**Persistência (correção P1):** o sidecar continua fora do schema do `TripPlan`, mas agora integra o arquivo de continuidade privado (local e, quando configurado, GCS privado). O botão existente de salvar planejamento também grava o arquivo privado quando disponível. Sem bucket privado, o sistema avisa explicitamente que é necessário exportar backup; não publica os agrupamentos no GitHub público. Backups de continuidade antigos sem `weekend_groups` seguem importáveis, inicializando uma lista vazia. A importação de JSON isolado por `plan_id` permanece disponível.

## UX
`app.py` deixa de renderizar o menu de navegação duplicado, mantendo roteamento de deep-links legados internamente. Guias e links de evidências continuam acessíveis pelas tarefas modernas, incluindo `Melhorar meu roteiro → Guias especializados` e `Minha viagem → Decisões`. Calendário legado de parâmetros continua sem novo caminho visual.

`smart_calendar_ui.render_smart_calendar` inclui `render_weekend_planner` na seção `Organizar viagem`, junto ao calendário existente. Não cria página, mecanismo financeiro, CSS ou editor paralelo de atrações.

## Testes e aceite
- `tests/test_ux48_priority_destinations.py`: 3 novos destinos, validação e integração ao contrato UX 4.5, edição/remoção.
- `tests/test_ux48_weekend_groups.py`: grupos únicos e múltiplos, ordem, período, pernoite, conflitos, descanso, rascunho exportável/importável, limpeza de órfãos, AppTest e ausência do menu legado.
- Executar toda a suíte existente com CI, inclusive UX4.5/4.7 e finanças.
- A revisão **visual real** em 375/768/1280px fica pendente até navegador habilitado. Testes Streamlit AppTest não comprovam pixels.
- Sem merge ou deploy automático; aguardar aprovação.

## Revisão de correções P1/P2
- Backup/recuperação: arquivo privado e backup manual incluem os grupos; salvamento explícito usa storage privado quando configurado.
- Validação: descanso considera o domingo e conflitos oficiais; viagens de três noites bloqueiam quatro dias.
- Reconciliação: verifica grupos em conjunto, preservando os dados do agrupamento em conflitos supervenientes.
- Edição: botões para mover destinos para cima/baixo, sem removê-los do grupo.
- Regressões adicionadas em `tests/test_ux48_weekend_groups.py`.
