# PROMPT DE IMPLEMENTAÇÃO — UX 6.1

**Situação:** apenas especificação para revisão; **não implementado**.
**Prioridade:** P0
**Dependência:** Nenhuma dependência funcional; primeiro PR a implementar.

## Papel do agente
Atue como Staff Software Engineer, Senior Python/Streamlit Engineer, UX/Product Engineer e Data Integrity Reviewer.

## Objetivo
Fazer os destinos desejados e salvos em Explorar → Minha lista aparecerem automaticamente na etapa correspondente de Meu roteiro → Meu planejamento, sem convertê-los silenciosamente em passeios do TripPlan.

## O que implementar
1. Criar uma **projeção de leitura** (p.ex. ux61_planning_candidate_projection.py) que combine os itens ativos de ux502_interests com os destinos de build_exploration_discovery(), agrupados por etapa e prioridade; distinguir os que já constam do TripPlan daqueles ainda a organizar.
2. Mostrar, em Meu planejamento, um bloco claro **Destinos da minha lista (N)** com nome, país, prioridade, estado "A organizar" ou "Já incluído no roteiro" e ação contextual para revisar atrações (a ação de confirmação fica para UX 6.2).
3. Preservar os descartados apenas em Minha lista ou seção secundária; nunca contabilizá-los como roteiro. Não mostrar um contador '0 lugares escolhidos' isolado dos interesses, sem explicação.
4. A lista permanece editável em Explorar; o planejamento deve reagir ao cadastro, remoção, mudança de prioridade, recuperação de JSON ou nuvem sem exigir sincronização manual.
5. Se um destino já foi planejado, removê-lo de Minha lista **não** deve excluir o passeio do TripPlan. Apresentar os estados separadamente.
6. Se um destino tiver dados exploratórios sem suporte no catálogo canônico (Obernai/Lucerna), mantê-lo visível e informar que escolher atrações para o roteiro requer UX 6.2. Não inventar atrações, tempos ferroviários ou valores.
7. Tornar o comportamento explícito para as etapas da Itália vs temporada europeia. Nunca classificar uma cidade como italiana por inferência frágil de nome; usar fontes tipadas/IDs verificáveis.
8. Evitar copiar a wishlist para uma segunda sessão: projetar a partir de st.session_state["ux502_interests"] como fonte do interesse.
9. A interface deve funcionar em tela estreita, conservar seleção ao mudar de aba e respeitar navegação por teclado e leitores de tela.

## Pontos atuais de integração
- ux502_destination_interests_model.py e ux502_destination_interests_ui.py
- trip01_supplemental_discovery.py / ux501_destination_discovery_model.py
- itinerary_flow_ui.py e itinerary_flow_model.py
- ux504_guided_journey_model.py / ux504_guided_journey_ui.py
- continuity_ui.py / continuity_archive_model.py
- app.py e planning_session.py

## Critérios de aceite e testes
- Lista salva com Colmar, Obernai, Paris, Basel, Strasbourg (+ sexto destino), aparece no planejador com prioridades corretas; 0 passeios continua honestamente 0 até confirmação, mas não aparenta lista vazia.
- O mesmo resultado após export/import da wishlist e restauração do armazenamento privado.
- Sem duplicatas quando destino figura na lista e no TripPlan; métricas de desejados vs confirmados vs organizados separadas.
- Mudar etapa, país, busca, comparar cidades e voltar não perde lista ou plano.
- Testar 0,1,5,6 e muitos destinos, prioridade descartada, IDs desconhecidos, documento legado, sessão sem login.
- Testes comprovam **nenhuma escrita** em TripPlan, GitHub público, GCS ou matriz de rotas por apenas exibir a lista.

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
