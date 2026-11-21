# UX 6.4 — Nova arquitetura de informação em três áreas

**Status:** PROMPT REVISADO; sem implementação. **P1**.
**Veredito do review:** REDESENHAR. A especificação antiga impunha 4 áreas; a direção aprovada é **Explorar · Planejar · Orçamento**.
**Dependências:** UX 6.1 e 6.2 definem a visão/estado dos destinos; UX 6.3 define a organização. Refazer navegação por último, mantendo aliases durante a transição. UX 6.5 provê indicador global, sem depender de nova navegação.

## Papel
Atue como Principal Product Designer, Senior UX Researcher, Staff Streamlit/Python Engineer e Compatibility Reviewer.

## Critério central
Usuário deve conseguir descobrir, planejar, organizar e revisar orçamento **sem aprender nomes de módulos** ou seguir um wizard linear. Três áreas de primeiro nível:
1. **Explorar** — Descobrir cidades/passeios, Minha lista, Comparar bases, Mapa. Pesquisa avançada de cidades-base e guias no contexto da busca, não em uma área "Roteiro" paralela.
2. **Planejar** — Visão geral da viagem e próxima ação contextual, Meus destinos/visitas, Organizar (timeline + calendário). Pendências, decisões, propostas italianas e sugestões aparecem como conteúdos contextuais.
3. **Orçamento** — Visão financeira e Simulações; detalhamento e fontes expansíveis. Um *resumo de orçamento* acompanha Explorar/Planejar; custo não é um passo final obrigatório.

Não introduzir uma quarta área `Ferramentas`: recursos antigos ficam em expander/atalhos apropriados. O painel inicial deve ser `Planejar → Visão geral`. Mudança visual não altera decisões no TripPlan.

## Migração explícita de todas as 13 abas atuais
| Atual | Novo destino recomendado | Preservação |
|---|---|---|
| Minha viagem → Resumo | Planejar → Visão geral | Jornada, status, próxima ação real |
| Minha viagem → Pendências | Planejar → Visão geral → Pendências | Fontes e ações pendentes |
| Minha viagem → Decisões | Planejar → Visão geral → Decisões | Histórico e evidências |
| Explorar → Cidades-base | Explorar → Comparar bases → Pesquisar bases | Pesquisa, filtros, detalhes |
| Explorar → Comparar | Explorar → Comparar bases | Cenários, cobertura e rotas |
| Explorar → Passeios | Explorar → Descobrir / Minha lista | Descoberta e wishlist não duplicada |
| Explorar → Mapa | Explorar → Mapa | Visão geográfica e links |
| Meu roteiro → Meu planejamento | Planejar → Meus destinos | Projeção + editor canônico |
| Meu roteiro → Organizar viagem | Planejar → Organizar | Timeline, fins de semana, calendário |
| Meu roteiro → Melhorar meu roteiro | Planejar → Meus destinos → Sugestões | Recomendações, Itália, comparadores avançados |
| Orçamento → Resumo financeiro | Orçamento → Visão financeira | Teto, margem, fontes |
| Orçamento → Simulações | Orçamento → Simulações | Simuladores e consultor |
| Orçamento → Detalhamento | Orçamento → Visão financeira → Detalhamento | Rubricas e rastreabilidade |

## Decisões de UX e restrições
1. **Jornada contextual, não linear.** Mostrar `Próxima ação útil` de acordo com dados reais: lista vazia → `Descobrir destinos`; destinos desejados, 0 visitas → `Planejar uma cidade` OU `Comparar bases`; visitas sem datas → `Organizar passeios`; visitas organizadas → `Revisar custos e pendências`. Nunca inferir `comparação concluída`, `reservado` ou `orçamento aprovado` por acesso à tela.
2. **Uma visão de destinos** em Planejar, consumindo a projeção UX 6.1, sem uma duplicação visual separada de Minha lista; qualquer destino com status desejado/planejado/organizado aparece uma vez.
3. **Atrações opcionais** (UX 6.2): não redirecionar o usuário obrigatoriamente a escolher 1–5 atrações para simplesmente marcar a cidade como planejada.
4. Mostrar `Quero conhecer`, `No roteiro`, `Organizado` como estados progressivos e não confundir com reservas.
5. Resumo de custos sempre acessível nas três áreas, sem bloquear a exploração. Simulações em modo hipotético não editam o teto ou base oficiais por padrão.
6. Transferir `DATA16`, `DATA17`, `referências indicativas`, IDs técnicos e avisos de pesquisa para metadados/expansões; traduzir em linguagem normal: `Outras atrações próximas`, `Trem: tempo pesquisado`, `Horários a confirmar`, `Fontes`.
7. Preservar guias de Itália, França, calendário de pesquisa, transporte e comparadores antigos em `Mais detalhes` ou `Ferramentas avançadas` **com inventário de cada rota**. Nenhuma função removida só porque não é usada na experiência principal.
8. **Navegação segura Streamlit:** atualizar `ux_navigation.AREAS`, `SECTIONS`, `TASK_ALIASES`, `route()`, `from_legacy()`, `bootstrap()` e `apply()` considerando aliases de área/aba (não apenas seção); compatibilidade com `main_navigation`, `itinerary_section`, `guide_section`, `ux_area`, `ux_section`, widgets/URLs antigos e contexto restaurado do arquivo GCS. Resolver solicitações de nav antes de instanciar widgets. Não criar segundo router.
9. Estado visual deve ser restaurável depois de rerun, mudança de país/base/mode, login/deslogin e retorno do editor sem apagar filtros, seleções ou scroll desnecessariamente.
10. **Acessibilidade/mobile:** tabs roláveis ou menus sem aglomerar 5 botões largos; labels claros, ordem de foco, contraste e expander com indicação; nunca depender apenas da cor. Mostrar espaço de pesquisa sem placeholders vazios excessivos.

## Estratégia incremental (obrigatória)
- Fase A: matriz de rotas e aliases, testes de compatibilidade e projeções de navegação sem alterar UI.
- Fase B: reordenar interface em 3 áreas preservando mapeamento antigo como camada de compatibilidade.
- Fase C: esconder elementos redundantes atrás de controles contextuais, auditar funcionalidade por funcionalidade e remover mensagens técnicas duplicadas.
Não atualizar área persistida em arquivos antigos de forma destrutiva; converter para nova rota no carregamento.

## Gate P1 — Normalizar backups antigos ANTES de validar navegação

**Problema comprovado na leitura de código:** `continuity_archive_model.validate_continuation()` compara `area` e `section` diretamente contra `ux_navigation.AREAS/SECTIONS`, **antes** de `ux_navigation.apply()` ou `bootstrap()`. Se a nova UX remover os valores `Minha viagem` e `Meu roteiro` dos enums, um arquivo válido da versão anterior será rejeitado integralmente em `validate_archive()`, sem chance de roteamento por `TASK_ALIASES`.

### Contrato de migração
1. Criar uma função pura, com comportamento **versionado e idempotente**, p.ex. `normalize_legacy_continuation(context, from_version)`, que reconheça pares legados `(area, section)` e valores de `organize_view` e `calendar_stage`. Aplicar a normalização na importação do arquivo **antes** da validação que exige o novo `AREAS/SECTIONS`. Rejeitar áreas realmente desconhecidas; não mapear todo erro para `Planejar` silenciosamente.
2. Preservar os dados originais do TripPlan, `destination_interests`, grupos, estudos, datas e revisão; converter **somente o contexto de navegação reconhecido**, com registro legível da conversão quando pertinente. Não alterar bytes do arquivo de origem automaticamente; ao reexportar, seguir política de schema/compatibilidade declarada.
3. Tratar `ux36_pending_restore`, `continuity_ui.restore_private_on_start()`, `apply_pending_restore()`, `continuity_archive_model.validate_continuation()/validate_archive()/preview_restore()/confirm_restore()`, `ux_navigation.from_legacy()/bootstrap()/apply()/set_task()` e `ux504_guided_journey_model.navigation_request()/apply_navigation_request()` com o **mesmo mapeamento** e sem criar segundo roteador.
4. Priorizar validação dos dados de viagem **independentemente da tela ativa**: contexto apontando para destino de edição que foi removido deve gerar fallback seguro ao painel `Planejar → Meus destinos`, com aviso, sem rejeitar todo arquivo de dados válido. Não usar fallback permissivo para destino_id desconhecido no TripPlan.
5. Documentar o comportamento das 13 abas de origem **incluindo estados secundários**: pesquisa ampliada, guias especializados, Itália/França, modo/calendário, `flow_active_destination`, busca, comparação, orçamento, identidade e login/logout. Normalizar antes de instanciar widgets Streamlit; reconciliar `main_navigation`, `itinerary_section`, `ux_area` e `ux_section` sem key conflict.
6. Qualquer alteração de `continuation` por migração **não** conta como edição substantiva no indicador global do #170. A migração pode mudar a tela de retomada, mas nunca fingir que alterou visitas ou foi salva no GCS.

### Testes de cadeia completa
- **GIVEN** backup GCS/JSON antigo com `Minha viagem/Resumo`, `Minha viagem/Pendências`, `Meu roteiro/Meu planejamento`, `Meu roteiro/Organizar viagem` e `Meu roteiro/Melhorar meu roteiro` **WHEN** importo **THEN** normalização → validação → prévia → confirmação → bootstrap → renderização chegam às novas telas sem perder dados.
- **GIVEN** arquivo com modo `Calendário completo`, semana e estágio definidos **WHEN** restauro **THEN** a visualização correspondente é acessível e os widgets não lançam `StreamlitAPIException`.
- **GIVEN** contexto legível mas destino ativo ausente no plano **WHEN** restauro **THEN** os dados continuam recuperáveis e o editor usa fallback contextual explícito, sem selecionar outro destino aleatório.
- **GIVEN** área inválida/injetada **WHEN** importo **THEN** rejeição permanece, sem converter para default nem ignorar arquivo hostil.
- **GIVEN** backup atual sob três áreas **WHEN** normalizo repetidas vezes **THEN** o resultado é idêntico (idempotência), com invariantes do TripPlan preservados.

## Given / When / Then
- **GIVEN** sessão em antiga `Minha viagem/Pendências` **WHEN** usuário abre bookmark ou restaura backup **THEN** navega para `Planejar/Visão geral/Pendências` sem perder contexto.
- **GIVEN** antiga `Meu roteiro/Melhorar meu roteiro/Guias especializados` **WHEN** uso alias **THEN** guia equivalente continua acessível em contexto avançado.
- **GIVEN** 6 cidades desejadas e nenhuma visita **WHEN** entro em Planejar **THEN** vejo meus destinos e ações `Planejar cidade` e `Comparar bases`, não sequência obrigatória.
- **GIVEN** altero cidade-base de simulação **WHEN** retorno de Explorar **THEN** base oficial e TripPlan seguem idênticos.
- **GIVEN** abro resumo do orçamento durante descoberta **WHEN** consulto ou altero cenário hipotético **THEN** consigo continuar pesquisa e custo não sobrescreve teto oficial.
- **GIVEN** volto do calendário avançado **WHEN** retorno à visita anterior **THEN** mesma etapa/destino e drafts, sem KeyError de widget no Streamlit.
- **GIVEN** abro um deep link antigo de qualquer uma das 13 abas **WHEN** o roteador inicializa **THEN** a ferramenta está disponível, sem aba vazia e com redirecionamento previsível.
- **GIVEN** toco em link de fontes/pesquisas **WHEN** abro detalhes **THEN** encontro evidências e nomes compreensíveis.

## Arquivos e testes
`ux_navigation.py`, `app.py`, `ux504_guided_journey_model.py`, `ux504_guided_journey_ui.py`, `planning_context_ui.py`, `ux501/ux502/ux503`, `itinerary_flow_ui.py`, `budget_sections_ui.py`, CSS e testes.

Testes unitários de **todos os 13 mapeamentos** de abas e aliases, configuração de navegação inicial, continuação GCS JSON legado, view modes, deep links, estado dos filtros e comparação; AppTest de cada área, responsividade/teclado sem duplicação de widgets ou navegação involuntária; assert de ausência de escrita em TripPlan/GCS/GitHub por mudar de área. Rotas antigas devem ter testes de regressão e documentação de redirecionamento.

## Regras globais
TripPlan autoridade de visitas; wishlist autoridade de interesses; sem duplicação de persistência, preços ou logística inventados; reservar é externo e exige evidência. Salvamento privado GCS ≠ login Google ≠ GitHub público. Esta branch contém somente prompt, não implementação nem autorização para merge. Revisar dependências contra main após UX 6.1–6.3, executar CI e obter novo review.
