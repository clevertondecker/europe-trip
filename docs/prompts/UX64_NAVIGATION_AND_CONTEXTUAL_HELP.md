# PROMPT DE IMPLEMENTAÇÃO — UX 6.4

**Situação:** apenas especificação para revisão; **não implementado**.
**Prioridade:** P1
**Dependência:** Planejado após UX 6.1–6.3, com atenção a compatibilidade de deep links e widget keys.

## Papel do agente
Atue como Staff Software Engineer, Senior Python/Streamlit Engineer, UX/Product Engineer e Data Integrity Reviewer.

## Objetivo
Reduzir duplicidades e termos técnicos mantendo quatro áreas reconhecíveis e um caminho progressivo 'Descobrir → Lista → Planejar → Organizar → Orçamento'.

## O que implementar
1. Preservar 4 áreas principais: Minha viagem, Explorar, Meu roteiro, Orçamento. Reorganizar subabas em:
   - Minha viagem: 'Resumo' com próxima ação real, pendências e decisões em seções contextuais;
   - Explorar: 'Descobrir', 'Minha lista', 'Comparar bases', 'Mapa' (pesquisa de cidades-base disponível nesta área, sem novo roteador paralelo);
   - Meu roteiro: 'Meu planejamento', 'Calendário' — 'Melhorar meu roteiro' migra para sugestões contextuais e ferramentas avançadas;
   - Orçamento: 'Visão financeira', 'Simulações' e detalhamento expansível.
2. Construir uma matriz das 13 abas atuais e ferramentas legadas (ux_navigation.py, app.py), com destino futuro de cada uma. Não eliminar cálculos, informações históricas, pesquisas, guias especializados ou funcionalidades de edição; mover para contexto ou 'Ferramentas avançadas'.
3. Remover jargão da navegação: DATA16, IDs de pesquisas, 'referências indicativas', 'revisão do inventário' devem ser explicados em linguagem de viagem, mantendo metadados e fontes para auditoria nos detalhes.
4. A ação prioritária em cada estado deve ser contextual e HONESTA: sem wishlist → Descobrir; com wishlist/sem passeios → Escolher atrações; com passeios sem data → Organizar; com roteiro organizado → Revisar custos e pendências. Nunca dizer 'comparação concluída' por só visitar página.
5. Incluir explicações claras das diferenças 'Quero conhecer' vs 'No meu roteiro' vs 'Organizado' vs 'Reservado'; estado Reservado exige evidência externa, nunca inferido.
6. Garantir responsividade, acessibilidade e não perda de contexto entre abas. Atualização das seções sem resetar filtros, staged widgets ou duplicar campos controlados pelo Streamlit.
7. Atualizar TASK_ALIASES, deep links e roteamento legado; preservar bookmarks existentes e passar pelo bootstrap/aplicação pré-widgets.
8. Se alguma aba ainda não tem substituto funcional, manter link contextual ao legado e registrar a lacuna, em vez de removê-la.

## Pontos atuais
- ux_navigation.py (AREAS, SECTIONS, TASK_ALIASES, route(), from_legacy())
- app.py (roteador, secundários, ferramentas legadas)
- ux504_guided_journey_model.py / ux504_guided_journey_ui.py
- planning_context_ui.py
- ux501/ux502/ux503, itinerary_flow_ui.py, budget_sections_ui.py
- Assets CSS e documentação existente de UX

## Critérios de aceite e testes
- Matriz de migração 100% das abas/links pré-existentes e seus novos destinos.
- Navegação de todos os estados da jornada sem abas vazias; breadcrumbs corretos e retorno ao contexto.
- Busca, filtros e lista preservados ao alternar Brasil/Itália/temporada, cidade-base, simulação, calendário, orçamento e voltar.
- Modo avançado preserva pesquisas e comparadores históricos.
- Tests AppTest com navegação por teclado/sem login/owner e testes de chaves de widgets pré-render.
- Nenhuma alteração de TripPlan por navegação ou somente por abrir telas.

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
