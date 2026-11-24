# UX125 — Retirada definitiva dos painéis legados

Depende exclusivamente da migração comprovada e remoção de Evidências e lacunas em DATA24A (#253). Não depende de DATA24B (#255); UX125 deve precedê-lo. Coordenar somente os blocos de navegação compartilhados e preservar o trabalho UX126B/UX127. Auditar app.py, ux_navigation, base_explorer_ui, base_research_expanded_ui, popovers/expanders, Referências históricas, Cinco bases aprofundadas, Todas as candidatas e explorador de atrações. DATA24A retira Evidências e lacunas; não reintroduzir. Mapear campo a campo evidências, filtros, links, estudos privados, simulações e recuperação de cenários; migrar conteúdo exclusivo às fichas/contextos/relatório, preservar ferramentas sem equivalente. Remover contêiner temporário e navegação legada somente após equivalência comprovada; manter Decisões oficiais/pendências/REC05 em Planejar. Normalizar estados/deep-links, remover renderizadores e CSS órfãos após auditoria de consumidores. Sem novo dashboard, sem alterar TripPlan ou orçamento. Testes de navegação real, estados antigos, preservação de dados, ausência de inventários globais concorrentes e regressão, CI verde. QA desktop/mobile quando disponível.

## Inventário obrigatório (QA desktop de 24/11/2026)
Além da lista atual (Referências históricas, Cinco bases aprofundadas, Todas as candidatas, explorador de atrações, contêiner temporário), auditar e resolver cada item abaixo. Para cada um: remover, migrar para o lugar canônico ou manter com justificativa registrada no PR. Confirmar rótulos e caminhos no HEAD após UX126B/UX127.

| Onde | Expansor ou entrada | Destino esperado |
|---|---|---|
| Explorar → Descobrir | “Visualização anterior · avançado” | Remover após equivalência |
| Explorar → Minha lista | “Visualização anterior · avançado” | Remover após equivalência |
| Explorar → Minha lista | “Comparação personalizada anterior · avançado” | Remover (Comparar bases cobre) |
| Explorar → Minha lista | “Indicadores do catálogo de desejos · avançado” | Relatório DATA24 ou remover |
| Explorar → Minha lista e Descobrir | “Pesquisar por cidade-base · opcional” | Remover após verificar equivalência com Comparar bases e ficha UX124 |
| Explorar → Comparar bases | “Pesquisas e estudos preservados · temporário” (restante após DATA24A) | Migrar estudos privados; remover o contêiner |
| Explorar → Mapa | “Explorar atrações turísticas por cidade-base →” | Unificar com Descobrir ou remover |
| Planejar → Meus destinos e Organizar | “Acessar outras etapas · opcional” (segunda jornada) | Remover; as três áreas cobrem |
| Planejar → Visão geral | “Pesquisas e mapa · opcional” | Remover duplicação de Explorar → Mapa; manter acesso a Decisões, pendências e REC05 em Planejar |
| Orçamento → Simulações | “Ajustes avançados da simulação”, “Outras ferramentas financeiras · avançado”, “Comparar alternativa” (reposicionados por UX127) | Decidir: remover ferramentas sem uso ou manter dentro de Simulações |
| Barra lateral | “Fontes e ferramentas” (inclui seletor antigo de cidade-base) | Manter único acesso; remover seletor duplicado |
| Rodapé de todas as telas | “Fontes do Drive verificadas…” e “Fontes e documentação do projeto” | Única ocorrência global (barra lateral ou página de fontes); preservar fontes contextuais e atribuição |

Inspecionar também `bottom_source()`, navegação anterior, deep-links, popovers e outros equivalentes de rótulos alterados. Registrar para cada item caminho real, arquivo/função, dados, ações, estado de sessão, consumidores, equivalente, informação exclusiva, decisão, destino e teste. Não basta ocultar; remover renderizadores e entradas órfãs após equivalência. Preservar ferramentas exclusivas úteis com acesso claro e justificativa.

## Fronteiras
- **UX127 (#260)** reposiciona os controles de Orçamento e não remove ferramentas. **UX125** decide a remoção depois do merge autorizado do UX127. Não alterar os mesmos blocos em paralelo. Até esse merge, pode auditar/preparar mudanças independentes; não antecipar a remoção desses controles. Preservar cálculo oficial, premissas, simuladores legítimos e paridade UX127.
- **UX126B (#254)** é dono dos filtros, paginação e textos do Descobrir. UX125 remove somente os expansores legados dessa tela.
- **DATA24A (#253)** remove “Evidências e lacunas”. UX125 não o reintroduz. DATA24B não é pré-requisito.

## Aceite adicional
- Teste que falhe se qualquer expander cujo rótulo contenha “anterior”, “temporário” ou “· avançado” for renderizado nas áreas Explorar, Planejar ou Orçamento, com allowlist explícita e justificada para os mantidos. Cobrir subabas/caminhos relevantes, inclusive após navegação em sessão nova e antiga; normalizar caixa e variantes de rótulo.
- Mapa campo a campo de cada item removido e o lugar onde a informação continua consultável. Testar fontes, recuperação de estudos, simulações, navegação e retorno contextual, ausência de mutação privada e paridade oficial UX127. QA desktop/mobile quando disponível; registrar limitações.

## Entrega
Implementar sequencialmente após pré-requisitos. Antes de implementar, atualizar base com alterações integradas ou estabelecer stack revisável; evitar conflitos em app.py e no gerador. Manter draft até código, suíte completa e checks do HEAD confirmados; não mergear sem autorização. Documentar limitações e evidência de testes. DATA25–28 serão definidos a partir dos resultados, não neste PR.

**Status:** especificação publicada; implementação pendente.