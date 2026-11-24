# UX124B — Refinamento visual e usabilidade da ficha de cidade-base

## Papel e contexto

Atue como Staff Software Engineer, Principal Product Designer e Senior UX Engineer especializado em Python, Streamlit, arquitetura de informação e acessibilidade. Repositório: https://github.com/clevertondecker/europe-trip.

Pré-requisito: PR #249 (UX124), já mergeado em main no commit `6984517b54845d7a7445cacb5b149d9979c8ae72`. O modelo de ficha única e as evidências compartilhadas são a base a preservar. Leia `docs/prompts/UX124_UNIFIED_CITY_PROFILE.md` e `docs/ux124_adversarial_review.md`.

A captura real de Mulhouse após o deploy mostrou que a nova ficha funciona, mas ainda se parece com um relatório técnico: cinco botões largos acima das abas, títulos redundantes "Investigue por assunto" e "Assunto", descrição "Cidade cadastrada no corredor Alsácia–Basel", cards muito largos para duas métricas, repetição de rede de bondes e museus, conexões em uma frase corrida, ressalvas espalhadas e dois expansores sobrepostos de fontes/pendências. A captura confirma esses problemas na Visão geral; auditar as demais cinco abas na implementação, sem presumir que foram visualmente verificadas.

## Resultado esperado

Responder em poucos segundos: "Como seria morar nesta cidade por aproximadamente dois meses, trabalhar remotamente e conhecer os meus destinos desejados?". A primeira leitura deve oferecer dados práticos, uma hierarquia editorial compacta e decisões acionáveis. Detalhes técnicos permanecem disponíveis sob demanda. A ausência de pesquisa não é uma desvantagem comprovada da cidade.

Não copiar literalmente um mockup HTML nem redesenhar a aplicação inteira. O resultado deve ser implementável em Streamlit, coerente com a identidade visual existente de Nossa Europa 2027, comprovado em navegador real.

## 1. Auditar antes de alterar

- Inspecionar `ux124_city_profile_ui.py`, `ux124_city_profile_model.py`, `rec03b_handoff_ui.py`, `rec03b_handoffs.py`, `rec03a_session.py`, `rec04_simulation_handoff.py`, `base_research_expanded_ui.py`, `city_profiles_ui.py`, `ux_shared_ui_presentation.py`, `ux100_base_card_photos.py`, `assets/styles.css` e os testes relevantes.
- Mapear as três entradas que renderizam a ficha (contextual, explorador e inventário temporário). Preservar o componente único; não criar cabeçalhos/ações paralelos incompatíveis.
- Abrir as seis seções no aplicativo com uma base rica em dados e uma com dados escassos. Registrar problemas confirmados, incluindo duplicação, excesso de whitespace, ordenação, linguagem técnica, dados omitidos, comportamento do seletor e carregamentos desnecessários.
- Fazer inventário campo a campo do renderer atual. Identificar o destino visual de cada informação antes de removê-la da primeira leitura. Não remover dados de origem.
- Usar a main atual ao implementar. Conferir o status da CI pós-merge do #249 e não atribuir regressões preexistentes ao novo PR.

## 2. Cabeçalho e hierarquia visual

- Cabeçalho compacto com retorno contextual, nome, país/região e foto existente com atribuição. Uma identidade clara, sem repetir status/corredor em frases de sistema. Não inventar descrições, indicadores ou imagens.
- Priorizar duas ações de decisão: "Simular orçamento" e "Comparar cidade". Favoritar, mapa e Descobrir continuam acessíveis como ações secundárias compactas, contextualizadas ou em um único menu nativo. Evitar cinco CTAs de largura total em duas linhas, ações escondidas sem rótulo, ou duplicar botões em cima e embaixo. A posição final pode ser escolhida após teste no navegador, desde que as ações continuem encontráveis em todas as abas.
- Preservar estado favoritado, limite de favoritas, limite de cinco cidades na comparação, capability/disabled da simulação, justificativa concisa quando indisponível, escopo da comparação e retorno do mapa, descoberta e simulação. Nenhuma oficialização automática.
- Remover "Investigue por assunto" e o rótulo visual redundante "Assunto"; manter label acessível via label_visibility. Manter os seis assuntos e seletor nativo controlado que renderiza apenas o assunto ativo. Não substituir por seis tabs que renderizem tudo avidamente sem comprovar desempenho.
- Usar tipografia, espaçamento, cards, botões e cor do design existente. Preferir componentes compartilhados e Streamlit nativo. CSS somente escopado à ficha, sem seletores globais frágeis, sem links/botões HTML falsos, sem JavaScript de navegação. Preservar dark mode se suportado e contraste legível.

## 3. Visão geral — decisão, não dashboard

Estrutura recomendada, adaptativa à largura e ao conteúdo:
1. Identidade/descrição editorial curta em português, sustentada por evidência existente. Eliminar termos de cadastro, repetições e qualificações editoriais antigas como se fossem fatos atuais. Se não houver descrição prática confiável, usar contexto mínimo neutro e dados disponíveis.
2. Dois indicadores úteis: mediana mensal de aluguel histórico (moeda, amostra, ano; ex. € 1.350 para Mulhouse conforme o modelo, sem centavos desnecessários) e destinos desejados não locais com tempo de ida (ex. 6 de 6 na captura). O segundo não mede qualidade, velocidade, frequência nem viabilidade. Sem wishlist: orientar para Minha lista; sem amostra: "Não pesquisado"; local separado; nunca mostrar 0/0 como cobertura útil. Não criar score ou estimativa de dois meses.
3. Lista compacta de conexões com os destinos desejados (até 3–5 exemplos, respeitando prioridade canônica Imperdível > Quero conhecer > Talvez; preservar identidade e ordem dentro da política existente, não escolher apenas casos favoráveis). Nome, tempo de ida destacado, qualificador histórico/indicativo/local/sem tempo e alerta legível para divergência. Acesso à aba Logística para todos. Mostrar imperdíveis sem dados, sem ocultar lacunas atrás de exemplos atraentes. Ex.: Basel 20 min com divergência, Colmar 18 min, Interlaken 2h14 na captura. Valores são ilustrativos da captura: consultar células do modelo em runtime, nunca hardcode.
4. Vantagens práticas e pontos de atenção em dois blocos compactos, empilháveis no mobile. Não repetir descrição, conexões ou ressalvas. Ex.: rede de bondes documentada; conexões regionais com tempos publicados; restrição de moradia de temporada. Evitar declarar "barato", "seguro", "boa qualidade de vida", "conexão fácil" ou "compatível" sem evidência. Distinguir riscos documentados de itens ainda não pesquisados.
5. Trabalho remoto: nome do coworking, faixa/horário publicado quando disponível e status de compatibilidade explicitamente qualificado. No caso Mulhouse, não suavizar "horário publicado não cobre todo o turno" para "compatibilidade parcial" sem indicar condição de modalidade. Internet do imóvel permanece pendente. Não calcular um expediente ou fuso novo sem premissa existente.
6. Um único expansor de contexto, fontes e pendências para a visão geral, com população municipal/ano/perímetro, fontes oficiais, limitações e auditoria histórica; deduplicar as duas entradas atuais. Não duplicar esse conteúdo em toda seção. Conservar ressalvas essenciais de interpretação ao lado do dado (ex.: não cotação 2027, não confirma volta).

Não tornar a primeira dobra outro dashboard. Evitar cards de contagem de anúncios, cobertura de pesquisa global, métricas duplicadas, listas longas e parágrafos com conteúdo repetido. Layout flexível, não impor altura fixa ou número de cards em cidades com poucos dados.

## 4. Padrão para as outras cinco seções

### Moradia — Quanto custa e onde procurar?
- Mediana, faixa observada, unidade mensal e quantidade/data da amostra num bloco compacto; destacar bairros com motivo documentado e fonte. Diferenciar referências de temporada, anúncio/catálogo e mercado residencial por m². Não misturar amostras nem estimar aluguel de 2027.
- Preservar anúncios individuais, tamanho, contas, ocupação, datas, condições de internet, proximidade de estação, taxas, caução e duração quando documentados. Organizar anúncios e outras referências históricas em uma área de detalhes, sem duplicação de imóveis nem links.
- Deixar requisitos contratuais e pendências na seção correspondente, com destaque breve do que impede reservar para duas pessoas. Sem fotos de imóveis inventadas.

### Logística — Para onde consigo ir?
- Minha lista como padrão quando houver desejos; caso contrário Todos os destinos. Preservar Com tempo pesquisado. Filtros explícitos, ordem canônica das prioridades, distinção entre local e não local, e contagem calculada do filtro ativo. A visão geral é sempre da wishlist; cobertura global apenas secundária.
- Tabela/lista compacta, responsiva, com destino, prioridade, referência de ida, tempo típico quando documentado e qualificador de evidência. Usar as mesmas células do comparador. Não substituir "sem tempo" por zero nem confundir tempo médio com mínimo.
- Detalhes por destino: fonte principal e alternativas, divergências, datas, estações, observações originais, notas, condições e limitações. Evitar despejar campos internos/inglês sem tradução; unidades claras, fontes clicáveis. Consolidar expansores sobrepostos sem esconder informações relevantes.
- Tarifas, frequência, passes urbanos e última milha quando documentados, com unidade, condição, fonte e escopo. Diferenciar tarifas da seleção e referências adicionais da base inteira. Não somar preço de ida em valor de retorno nem transferir dados de outra estação/cidade. Conexões fora do catálogo em detalhe separado, não na cobertura.

### Vida cotidiana — Como seria a rotina?
- Organizar alimentação, supermercado, transporte cotidiano (sem duplicar a tabela de logística), serviços/academia somente quando houver pesquisa e clima em blocos compactos.
- Mostrar claramente custo local vs premissa histórica comum do orçamento, moeda/unidade/pessoas. Não somar orçamento duas vezes nem apresentar cesta compartilhada como específica.
- Clima de setembro, outubro e novembro com leitura visual simples (tabela curta ou cards adaptativos), temperatura média e precipitação, estação e período climatológico. Sem previsão futura inventada ou gráfico desnecessário.
- Se faltam informações de rotina, estado vazio útil e honesto; sem preencher com generalidades.

### Trabalho remoto — Consigo trabalhar no meu horário?
- Priorizar internet residencial não confirmada e compatibilidade do coworking antes das ressalvas extensas.
- Mostrar nome, preço, modalidade, horário, condições de acesso noturno e fonte. Preço por dia/mês e impostos claramente distinguidos. Reutilizar status de UX113/REC04; sem conversão inventada de expediente.
- Não confundir falta de evidência com ausência de coworking. Evitar duplicar informações entre overview e seção: visão geral resume, seção detalha.

### Atrações — O que conhecer aqui e nas redondezas?
- Separar atrações locais, complementares e destinos regionais; evitar listas repetidas por fontes/aliases. Reutilizar catálogo, imagens e créditos existentes. Imagens compactas, consistentes e fallback neutro; respeitar licença. Não inventar atrações, fotos, distância, tempo ou tickets.
- Cards/lista responsivos, nome, descrição, duração editorial identificada, ingresso/modalidade/moeda/validade quando documentados e fonte. Não declarar gratuito se desconhecido.
- Destinos regionais com tempo de ida pesquisado e atração catalogada: apresentar de modo compacto, sem prometer bate-volta. Diferenciar esses exemplos da wishlist; reutilizar handoff para Descobrir e Minha lista sem adicionar automaticamente. Se houver pouca pesquisa, dizer explicitamente.

## 5. Arquitetura, escopo e integridade

- Refinamento de apresentação sobre a arquitetura UX124: preservar um único renderer, `city_profile`, `personalize_routes`, `route_scope`, cache público e projeção de matriz ferroviária canônica UX503/REC01 + ROUTES7, com as mesmas fontes e precedência. Pequenos helpers puros de apresentação são permitidos se eliminarem duplicação, não um modelo alternativo.
- Reutilizar os contratos de REC03A/B, CHOICE, UX64, UX41, REC04, UX113, serviços de fotos e componentes visuais existentes. Preservar as keys/callbacks e testes de retorno, ou justificar e migrar explicitamente. Ao retornar, conservar origem, cidade, lista, escopo, seleção, assunto e filtro quando ainda válidos. Se a wishlist mudou, aplicar reconciliação existente e não reutilizar contexto obsoleto.
- Não incluir dados privados no cache público; não mutar TripPlan, wishlist, orçamento, estudos privados ou persistência durante render. Favoritar e selecionar para comparar somente por ação explícita; não gravar alterações oficiais. Limpar helpers, imports e CSS realmente órfãos após auditoria de consumidores.
- Não criar novas bases/datasets, rankings, scores, comparadores, simuladores, persistência, motor de rotas ou módulos de recomendação. DATA24 e UX125 (remoção definitiva do legado) permanecem separados. Não reabrir o escopo de pesquisa nem modificar o schema.
- Preservar compatibilidade de importação a frio com o resolver lazy compartilhado; falhar fechado no componente, não no aplicativo inteiro. Não recarregar módulos vivos.
- Investigar custo de rerun, leitura repetida de datasets e renderização de imagens/expanders; manter cálculo e cache existentes salvo regressão comprovada. Não adicionar chamadas de rede por item nem expor evidência de outra sessão. Expanders do Streamlit não são garantia de lazy execution.

## 6. Critérios de aceite objetivos

- Captura comparável de Mulhouse (mesma wishlist/escopo, quando reproduzível): cabeçalho e seletor significativamente mais compactos; descrição sem linguagem de sistema; aluguel e conexões imediatamente legíveis; nenhuma frase longa concatenando destinos; pontos fortes/atenção distintos; uma entrada geral de fontes e pendências; sem cinco CTAs grandes. Registrar diferenças de conteúdo real se a wishlist da captura não puder ser reproduzida.
- Seis seções com padrão coerente; estado vazio sem dados inventados, zero indevido ou cards vazios; cada seção tem uma pergunta prática implícita, sem repetir grandes títulos e descrições.
- Mesmas evidências, valores, fonte, data, limitações, modalidades, filtros e identidade do comparador. Cobertura separada de viabilidade e qualidade; verificar locais, descartados, imperdíveis ausentes, divergências, dados sem preço, referências indicativas e sem wishlist.
- Todas as cidades atuais suportadas, sem hardcode de quantidade. Testes de projeção para todas; AppTest das seis seções em Mulhouse/Strasbourg e Annecy/Colmar, incluindo uma cidade sem foto se houver. Testar também favorito no limite, comparação com 1/2/5 selecionadas, simulação habilitada/indisponível, ida/volta de Descobrir e mapa, recarregamento/alteração da wishlist, ausência de mutação e retorno ao contexto.
- Validar visualmente no navegador real em desktop (aprox. 1440/1280 px), tablet (768 px) e mobile (390 px), incluindo a primeira dobra, scroll, seletor de assuntos, tabelas, fotos ausentes/fallback, textos longos, teclado/foco e contraste. Verificar que não haja overflow horizontal de página; tabelas largas podem ter scroll próprio. Não usar mockup gerado como prova de implementação. Anexar screenshots reais de antes/depois e das seis seções; se navegador indisponível, declarar a validação pendente e não simular evidência.
- Atualizar testes anteriores que fixavam layout/texto obsoleto (UX107–110/UX124), mantendo verificações de contratos. Rodar checks de sintaxe, contratos de dados e suíte completa. Confirmar CI verde no HEAD exato, revisão adversarial sem regressões e sem perda de informação. Não desativar testes ou relaxar validações.

## 7. Entrega

Implementar somente após aprovação deste prompt. Trabalhar neste PR, não abrir PRs sobrepostos. Ao concluir, incluir relatório com:
- findings confirmados antes/depois por seção;
- decisões de UX e motivos, com alternativas descartadas;
- inventário de informações preservadas/movidas, componentes reutilizados e código órfão removido;
- resultados reais dos testes e screenshots de navegador, limitações restantes;
- impacto em outras rotas, compatibilidade e ausência de mutações.

Manter PR em draft durante execução/review. Não fazer merge automático. Após implementação e CI verde, solicitar revisão visual do usuário antes de qualquer merge. A criação deste prompt não equivale à implementação.

Pergunta adversarial final: consigo decidir se vale investigar esta cidade sem ler uma página de metodologia, mantendo acesso às evidências necessárias? Se a resposta for não, simplificar novamente antes de considerar concluído.
