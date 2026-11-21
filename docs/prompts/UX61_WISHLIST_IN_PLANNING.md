# UX 6.1 — Uma visão dos destinos, sem segunda lista

**Situação:** PROMPT REVISADO; ainda não implementado. **Prioridade P0.**
**Veredito do review adversarial:** REDESENHAR (a versão anterior sugeria simplesmente duplicar a wishlist no planejamento).
**Dependências:** nenhuma alteração de contrato necessária; UX 6.2 amplia os estados/ações depois. UX 6.4 migra o endereço de navegação de `Meu roteiro` para `Planejar`.

## Papel
Atue como Principal Product Designer, Staff Python/Streamlit Engineer, Arquiteto de Domínio e Test Engineer.

## Problema real e decisão
O usuário salva Colmar, Obernai, Paris, Basel e Strasbourg na wishlist e vê `0 lugares escolhidos` em Meu planejamento. Mostrar **duas listas independentes** resolve o sintoma, mas cria redundância. Construir **uma projeção compartilhada de destinos com estados compostos**, reutilizada tanto na lista quanto no painel Planejar, com ações contextuais diferenciadas. Não fazer uma segunda tabela persistida.

## Proposta de UX
- Em **Planejar → Visão geral/Meus destinos** (com compatibilidade para `Meu roteiro → Meu planejamento` até UX 6.4), renderizar **um único conjunto de cartões/linhas** de destinos, filtrável por `Todos`, `Quero conhecer`, `No roteiro` e `Organizados`, por etapa/país e prioridade, com busca e paginação para até 200 itens.
- Cada cartão pode exibir: foto com fallback e crédito, nome, país, prioridade, base sob estudo quando houver; estado `Quero conhecer`, `No roteiro`, `Atrações selecionadas`, `Organizado`. Estados não devem ser mutuamente excludentes; não inventar `Reservado`.
- Mostrar métricas distintas `6 destinos desejados`, `0 visitas no roteiro`, `0 com período/data`; não apresentar `0 passeios` como se a lista estivesse vazia.
- Destinos já confirmados no TripPlan aparecem uma vez, com detalhes de atração/período quando existirem. Remover interesse não apaga visita; remover visita (com confirmação, na UX 6.2) não apaga interesse.
- Se houver nenhum destino, exibir estado vazio com uma ação `Explorar cidades`. Se houver dezenas, usar filtros e paginação sem repetição ou expander por cartão.
- Ações **somente de navegação**, nesta fase: `Ver atrações`, `Comparar bases`, `Continuar planejando`. Não oferecer falsa ação `Adicionar ao roteiro` até UX 6.2 implementar a confirmação real. Pode indicar `Visita a planejar`.
- A lista deve atualizar imediatamente após adicionar/remover/alterar prioridade ou importar/restaurar, sem botão `Sincronizar`. Preservar contexto ao alternar etapa Itália/temporada europeia, país e filtros. Não inventar etapa por heurística de país; as cidades da wishlist são destinos de exploração, e Itália usa catálogo de estágio diferente. `Sem etapa definida` é preferível à classificação falsa.
- Orçamento e logística podem ser consultados como contexto; nenhuma informação pesquisada equivale a logística confirmada.

## Modelo e limites
1. Criar função pura de projeção, p.ex. `build_destination_board(wishlist, trip_plan, discovery, canonical_catalog)`. **Não** materializar lista em outra chave de `st.session_state`. `wishlist` continua em `ux502_interests`, `TripPlan` em `advisor_plan`.
2. Indexar por `destination_id` estável, evitando duplicatas e respeitando `canonical_place`/aliases **somente** onde registrados. A projeção deve aceitar Obernai/Lucerna da `trip01_supplemental_discovery.py` para leitura e apontar restrições canônicas explicitamente.
3. Ler `packages` e `flexible_visits` do plano atual para status; não mexer no schema do TripPlan agora. UX 6.2 adicionará suporte a visita sem atrações.
4. Preservar entradas descartadas e alterações de prioridade apenas na wishlist; cartão de destino `descartado` fica oculto por padrão, consultável no filtro avançado.
5. Reutilizar `ux502_destination_interests_model.py`, `trip01_supplemental_discovery.py`, `itinerary_flow_ui.py` / `ux504_guided_journey_model.py`. Não criar novo editor nem novo repositório de dados.
6. Acesso antigo `Explorar → Passeios → Minha lista` e `Meu roteiro → Meu planejamento` permanece funcional; o novo painel deve consumir a **mesma projeção**.

## Cenários Given / When / Then
- **GIVEN** wishlist com 5 ou 6 destinos incluindo Obernai **WHEN** abro Meu planejamento **THEN** os interesses aparecem sem recadastro, há 0 visitas se TripPlan vazio, e nenhum commit.
- **GIVEN** Colmar existe na wishlist e no TripPlan **WHEN** renderizo as duas superfícies **THEN** aparece uma única entrada por destino e os dois aspectos de estado são visíveis.
- **GIVEN** removo Colmar da wishlist mas ele já estava no roteiro **WHEN** reabro o painel **THEN** a visita persiste.
- **GIVEN** descarto uma cidade **WHEN** aplico filtro padrão **THEN** ela não conta como candidata ativa nem é eliminada do backup.
- **GIVEN** restauro arquivo privado ou importo JSON **WHEN** reabro o painel **THEN** mesma ordenação/IDs/prioridades; nenhuma duplicata.
- **GIVEN** wishlist vazia, 1 item ou 200 itens **WHEN** consulto via desktop/mobile **THEN** estado vazio, paginação e ações contextuais coerentes.
- **GIVEN** navego para Comparar e volto **WHEN** retorno **THEN** busca, página e estágio são preservados onde pertinentes sem mutar o TripPlan.

## Testes e entrega futura
Testes unitários de projeção pura e deduplicação; `streamlit.testing.v1.AppTest` (rotas antigas, estados de auth, mudanças de prioridade, buscas, import/export, troca de etapa, 0/1/6/200 itens); asserts de nenhuma gravação em TripPlan, GCS, GitHub ou rotas ferroviárias em render/navegação. Responsividade + uso de label/teclado. Capturas antes/depois e tabela de métricas. Atualizar documentação do estado sem promover pesquisa a reserva.

## Direção de produto aprovada (UX 6.0)
**Arquitetura-alvo:** três áreas principais: **Explorar**, **Planejar** (início + destinos + agenda + decisões) e **Orçamento**. A sequência sugerida é orientativa, **não obrigatória**: pesquisar, comparar cidades-base, organizar e simular custos podem ocorrer em qualquer ordem. Orçamento resumido acompanha a jornada, inclusive durante a descoberta. Ferramentas técnicas/legadas ficam em contexto ou em expansão avançada, não desaparecem.

**Semântica canônica:** `Quero conhecer` = interesse na wishlist; `No roteiro` = visita explicitamente confirmada no TripPlan, com **zero ou mais atrações** após evolução contratual UX 6.2; `Atrações escolhidas` é detalhe opcional; `Organizado` = período/data definidos; `Reservado` exige evidência externa. Ler uma tela não significa aceitar opção, concluir comparação ou fazer reserva.

**Segurança:** TripPlan permanece autoridade das visitas planejadas; wishlist permanece fonte de interesse. Um destino pode estar em ambos, mas sua **visualização deve ser única** com estado composto, sem cópias mutáveis ou um segundo editor. Preservar IDs, autenticidade de fontes, base/roteiro oficiais, isolamento de simulações, datas reais do plano e snapshots ferroviários (30×46), sem inventar tarifas, horários/retornos ou dados 2027. Não escrever remotamente por navegar, pesquisar, favoritar ou abrir editor. Persistência privada em GCS é distinta de login Google e publicação pública do GitHub.

**Regra de execução:** PR **somente de especificação** nesta etapa. Na futura implementação, reconciliar branch com a `main` mais recente, executar validações, testar AppTest e obter review antes do merge. Nunca fazer merge somente de prompt.
