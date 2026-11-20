# PROMPT DE IMPLEMENTAÇÃO — UX 6.3

**Situação:** apenas especificação para revisão; **não implementado**.
**Prioridade:** P1
**Dependência:** Implementar após UX 6.1/UX 6.2 e com rebase de main; não alterar os modelos de persistência sem migração revisada.

## Papel do agente
Atue como Staff Software Engineer, Senior Python/Streamlit Engineer, UX/Product Engineer e Data Integrity Reviewer.

## Objetivo
Unificar a experiência de organizar destinos por período, data e agrupamentos de fim de semana, preservando os calendários avançados existentes.

## O que implementar
1. Em Meu roteiro → Organizar viagem, criar uma visão padrão única 'Organizar dias' que consome exclusivamente passeios confirmados no TripPlan, vindos do fluxo UX 6.2 ou anteriores. Destinos somente desejados podem aparecer como contexto, **não** como eventos marcados.
2. Apresentar três opções progressivas para cada passeio: 'Decidir depois', 'Período flexível', 'Data específica'. Ao mudar uma opção, não apagar marcações confirmadas sem mostrar as consequências e receber confirmação.
3. Disponibilizar ferramenta contextual de agrupar passeios em viagem/fim de semana (UX 4.8/4.9), reutilizando ux48_weekend_groups_model/UI, em vez de duplicar agrupamentos em um segundo estado.
4. Mostrar fases com data e duração provenientes do TripPlan: Itália 10 dias + temporada europeia 60 dias na configuração de teste, sem hardcode de datas; validar fronteira de fases e alterações de duração/partida.
5. Preservar alternativa 'Calendário completo' como avançada, mas com nomenclatura e navegação compreensíveis. 'Calendário inteligente' deve ser recurso contextual, não um segundo universo de eventos.
6. UX de avisos: conflito de datas, múltiplos passeios no mesmo dia, dia de descanso, viagem com pernoite, deslocamento ainda não comprovado e tempo ferroviário desconhecido. Nunca afirmar disponibilidade ou duração não pesquisada.
7. Para os 60 dias trabalhando remotamente, expor claramente critérios editoriais de final de semana vs dia útil, sem inferir dias de folga; atividades durante expediente só mediante opção explícita.
8. Reutilizar scheduling existente (schedule_package, schedule_italy_visit, commit_outing) e as restrições de stage, sempre aplicando mudanças por ação confirmada. Reabrir calendário deve preservar seleção e contexto.

## Pontos atuais
- itinerary_flow_ui.py: _render_organize, _reconcile_organize_state
- ux48_weekend_groups_ui.py / ux48_weekend_groups_model.py
- smart_calendar_ui.py / smart_calendar_model.py / calendar_model.py
- itinerary_flow_model.py, planning_session.py e continuidade privada
- app.py e ux_navigation.py

## Critérios de aceite e testes
- Fluxo com dois destinos sem data, um com período, outro com data, um fim de semana agrupado; todas as telas concordam.
- Mudar o período para data e voltar preserva o que deve ser preservado ou solicita revisão explícita; não criar ou remover passeios inadvertidamente.
- Testar 10/60 dias, mudança para outra duração válida, limites de etapas e de calendário, navegação, ausência de trens/retorno, dias de descanso, edição e exclusão de agrupamentos.
- Auditoria de não duplicação no TripPlan; roundtrip backup JSON, carregamento privado, AppTest e regressão completa.
- Componentes avançados continuam acessíveis, mas não competem com a ação principal.

## Contexto e regras obrigatórias
Repositório: https://github.com/clevertondecker/europe-trip
Produto: Nossa Europa 2027 (Streamlit/Python), lua de mel na Itália + temporada europeia.
Este PR foi aberto **somente com este prompt**, para review do escopo. Ainda não há implementação funcional. Após aprovação explícita, implementar **nesta branch** e executar testes/CI. Não fazer merge de PR apenas documental.
- TripPlan continua a única fonte autoritativa de passeios confirmados no plano; preferências e pesquisas não são reservas.
- Preservar IDs existentes, compatibilidade de dados/arquivos, isolamento de fontes, fluxos de autenticação, regressões e segurança.
- Sem inventar custos, trens, horários, disponibilidade de 2027, fotos/licenças ou estado de decisão.
- Evitar novos editores paralelos, duplicação de estado de Streamlit e alterações não solicitadas no planejamento oficial.
- Verificar os contratos e os testes existentes antes de editar; adicionar testes de domínio + AppTest; testar troca de etapa Itália/França, restauração, navegação e histórico onde aplicável.
- Rever a branch contra main antes de implementar, pois estes cinco PRs são independentes e poderão ser executados sequencialmente.
- Entregar implementação + explicação da UX + testes + riscos e limitações. Não fazer merge até revisão e autorização posteriores.
