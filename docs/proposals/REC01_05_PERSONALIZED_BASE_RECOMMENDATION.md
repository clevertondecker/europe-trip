# PROMPT — REC01–REC05: recomendações personalizadas de cidades-base

**Projeto:** Nossa Europa 2027  
**Repositório:** https://github.com/clevertondecker/europe-trip  
**Estado:** proposta revisada após avaliação adversarial em 21/11/2026; não é implementação nem autorização de merge. A revisão restringe o MVP à logística e exige reprodução da triagem no REC01.

Atue como Staff Software Engineer, Product/UX Engineer, Senior Python/Streamlit Engineer e especialista em sistemas de recomendação multicritério e qualidade de evidências. Antes de escrever código, inspecione o HEAD atualizado de main, os contratos e testes existentes. Confirme ou refute as premissas deste documento, registre divergências e preserve funcionalidades atuais. Execute em incrementos independentes, revisáveis, com CI verde. Não implemente todos os incrementos simultaneamente nem faça merge sem autorização.

## 1. Problema e objetivo (MVP logístico)

Hoje o usuário descobre atrações, registra destinos e prioridades, e escolhe manualmente 2–5 cidades para comparar. Queremos inverter essa dependência: sugerir automaticamente candidatas a partir dos destinos escolhidos, explicando referências logísticas, cobertura e incertezas; moradia e qualidade de vida são contexto complementar até serem comparáveis. A pesquisa de cidades deve continuar dinâmica (34 candidatas no DATA23, nunca uma quantidade fixa no algoritmo). A escolha exploratória não equivale a confirmação de residência, reserva ou alteração do TripPlan.

Contexto: lua de mel na Itália seguida de temporada europeia com trabalho remoto, passeios sobretudo nos fins de semana, viagem após 04/09/2027. Datas, duração, valores e preferências atuais do plano devem ser lidos dos contratos existentes; não codificar premissas pessoais como regras universais. Priorizar acesso ferroviário, moradia mobiliada para dois adultos, conectividade para trabalho remoto e orçamento. Tratar Itália/lua de mel e temporada europeia como escopos distintos: não usar automaticamente destinos da lua de mel para sugerir a base da temporada.

## 2. Auditoria obrigatória antes da implementação

- ux_navigation.py, app.py, ux504_guided_journey_model.py e ux504_guided_journey_ui.py: rotas, callbacks, jornada e atalhos existentes.
- ux501_destination_discovery_model.py, trip01_supplemental_discovery.py, ux502_destination_interests_model.py e ux502_destination_interests_ui.py: IDs, prioridades, lista persistida, escopos, GCS e migrações.
- ux503_destination_base_comparison_model.py/UI, rail_reference_projection_model.py, routes7_comparison_projection.py, evidence_query_model.py, rail_evidence_unified_model.py e ux506_decision_readiness_projection.py: matriz histórica, overlays, precedência, divergências, associação de ida e retorno.
- base_research_expanded_model.py, base_coverage_model.py, base_scenario_model.py, city_profiles_model.py: pesquisa dinâmica, cesta fixa de referência, candidatas, base oficial, moradia, dados opcionais.
- Verificar módulos de orçamento, cenários, mapa, favoritos, roteiro e persistência, seus testes e documentação. Reutilizar caminhos canônicos de navegação e ações existentes.
- Documentar conjunto real de destinos elegíveis, universo de bases, eventuais aliases/IDs, cobertura por categoria, limites de datas e quais cidades podem ser usadas em cenários versus oficializadas.

## 3. Jornada e UX (revisão adversarial)

A UX64 está implementada: ux64_navigation_model.py define PUBLIC_AREAS=(Explorar, Planejar, Orçamento) e PUBLIC_TASKS; app.py importa public_area/select_public_area e render_public_task_tabs. ux_navigation.py mantém quatro áreas INTERNAS por compatibilidade. Não substituir o roteador, criar área/aba principal ou persistir outro estado de navegação.

Fluxo público: Explorar → Descobrir → Minha lista → Comparar bases (atividade interna Cidades sugeridas / Comparação personalizada) → Planejar → Meus destinos / Organizar → Orçamento. A visão geral de Planejar oferece atalhos contextuais. Cidades-base/fichas continuam acessíveis no fluxo já existente; pendências e decisões legadas não são removidas. Não bloquear montagem de roteiro nem marcar comparação como concluída por visita à tela.

- CTA "Encontrar cidades-base" em Minha lista e, quando houver interesses ativos, na visão geral. Entrar diretamente na atividade de sugestões em Comparar bases via select_public_task/set_task e intenção pré-widget existente. Um único seletor interno de atividade, sem rotas duplicadas. Preservar deep links e compatibilidade dos callbacks legados.
- Exibir primeiro escopo de análise e resumo dos interesses; não exigir formulário de pesos. Mostrar cobertura, imperdíveis, exemplos de trajetos, evidências e pendências. Até 3–5 destaques quando úteis, acesso a todas as candidatas e comparação manual (2–5), sem apresentar ordenação como ranking global.
- Fotos apenas com fontes/créditos/fallback existentes. Ações explícitas para abrir ficha, favoritar, selecionar para comparação, voltar à lista, simular se suportado e continuar roteiro. Transferir IDs e escopo selecionado sem destruir filtros manuais; pedir ação explícita antes de substituir seleção anterior.
- Diferenciar base oficial, cenário e candidata exploratória. Não oferecer confirmação inválida. Progressive disclosure, layout responsivo, labels acessíveis, estados vazios/erro, sem depender de cor/hover.

### 3.1 Contrato de escopo (MVP)
Wishlist v1 valida exatamente destination_id e priority por item, sem etapa; mudar schema afetaria importação, GCS, restauração e testes. Não modificar wishlist, TripPlan ou backups no MVP. Criar contrato puro, transitório recommendation_scope={stage, destination_ids}, stage inicialmente europe_season; destination_ids é conjunto ordenado/deduplicado de IDs ativos canônicos. Não inferir etapa por país, alocação histórica ou nome da cidade. Permitir que um destino italiano seja explicitamente incluído na temporada; o mesmo destino pode pertencer a qualquer cenário sem duplicar a wishlist.
- Sem interesses ativos: no_destinations; com interesses e escopo ainda não escolhido/confirmado: scope_required. Mostrar todos os ativos pré-selecionáveis, com prioridades, CTA "Usar toda a lista para a temporada" e opção de remover desta análise. A confirmação é explícita mesmo se lista parecer homogênea. Escopo vazio mostra ação de seleção, não resultado.
- Guardar escopo confirmado apenas em estado de sessão isolado, reconciliar contra lista atual por IDs e revision; destino removido/descartado sai, prioridade alterada recalcula, destino novo fica pendente de revisão do escopo (não misturar automaticamente etapas). Se sessão perdida/recarregamento sem estado, solicitar novamente. Nada de promessa de restauração entre dispositivos. Não armazenar apenas booleano de conclusão.
- Passar escopo confirmado à comparação e simulações; comparação manual pode escolher sua própria seleção, rotulando claramente quando escopo difere. Não forçar mudança da wishlist nem filtros legados.

## 4. Motor de recomendação: MVP logístico, sem falsa precisão

### 4.1 Universo e projeção
Usar explicitamente load_research(include_candidates=True) para o universo de bases recomendáveis, validando unicidade de IDs canônicos. Todos entram na avaliação, inclusive sem rotas. Manter default histórico em outros consumidores e registrar diferenças de escopo. Centralizar o carregamento público de candidatas no ponto de entrada da projeção, não refatorar todos os loaders. Para destinos selecionáveis, usar build_exploration_discovery() e UX502. A auditoria abaixo encontrou 48 IDs nesse catálogo reconstruído e 34 bases; 9 de 10 destinos de trajetos DATA23 estão fora do catálogo atual. REC01 deve auditar esse descompasso e permitir inclusão das entradas DATA23 com identidade, país, atração/fonte de turismo e validações já exigidas, em overlay somente leitura se os dados sustentarem; se não sustentarem, reportar exatamente os IDs faltantes como backlog. Não promover automaticamente todos os endpoints ferroviários à wishlist nem modificar snapshots, catálogo oficial ou TripPlan. Testar restauração e deduplicação. Candidata com pouca cobertura nunca é excluída.

Extrair minimamente do UX503 uma projeção read-only para qualquer número de bases; limite 2–5 continua apenas no contrato manual. Reusar get_rail_evidence e decorate_comparison (incluindo precedência histórica, ROUTES7 corroborado, DATA9–13, DATA22 e DATA23). Além disso auditar dq32_macro_opportunities_model: ele já monta projection_rows e chama decorate_comparison; evitar terceira montagem de mesma matriz. Preservar todas as observações, categoria, origem/destino direcionais, fonte, datas, estações, divergências e limitações; não inferir reversos/retornos/frequência/tarifas. Cesta histórica de 15 é separada desta seleção.

### 4.2 Métricas e política de comparação
MVP analisa logística de ida para destinos escolhidos. Moradia, trabalho remoto, vida cotidiana, preço e outros países aparecem como contexto com fonte e lacunas, não como score/recomendação econômica ou de trabalho remoto. Retirar presets multicritério e sliders do MVP; REC04 só os reintroduz quando houver medidas comparáveis, unidade, denominadores e política de dados ausentes justificadas. Não contar países como acessíveis/viáveis a partir de mínimo de ida.

Pesos de prioridade 5/3/1 (imperdível/interessado/talvez) iniciais, descartado excluído. Sensibilidade 10/3/1 e 3/2/1 em testes; não expor controle de pesos na UI agora. Métricas por cidade:
- Cobertura ponderada ferroviária = soma pesos dos pares com duração utilizável / soma pesos dos destinos não locais do escopo; sempre publicar numerador/denominador, contagem de locais e desconhecidos. Se denominador zero, cobertura não aplicável, resultado local separado (sem zero minutos).
- Cobertura dos imperdíveis: tempos conhecidos, locais com acesso pendente e desconhecidos separados. Exibir contagem de históricos e indicativos/qualidade sem duplicar pares. Local reconhecido satisfaz identificação do destino, não comprovação de acesso.
- Contagem de destinos com mínimos conhecidos até 60/120/180 min, rotulada como referência de ida e não bate-volta viável. Exemplos reais são destaque na UI; média ponderada dos mínimos publicados/conhecidos é secundária, com conjunto de destinos, pesos, denominador e fontes; nunca "tempo médio de viagem".
- Comparações de duração somente para mesma lista de destinos não locais e mesmos pesos entre candidatas; comparações em subconjunto comum explicitamente condicionais, publicar IDs e cobertura; não comparar médias de conjuntos incompatíveis nem dar superioridade global a partir de um único destino comum. Se destinos locais diferem, apresentar separadamente, sem imputar 0; comparação de logística total pode ser indeterminada.
- Histórico e mínimo indicativo/ fonte secundária mantêm categorias distintas; comparação com mistura de categorias é preliminar, não equivalência de serviço/estação/data; divergências sinalizadas. Nenhuma validação de ida/volta, última milha, serviço ou disponibilidade 2027.
- Distinguir cobertura de adequação e qualidade; nenhum score composto 0–100, probabilidade de acerto ou peso renormalizado por cidade.

### 4.3 Estados explícitos e critérios
Estados do modelo, não somente da UI: no_destinations, scope_required, comparable, partial_evidence, insufficient_evidence. Definir resultado global e status por candidata (evidência insuficiente se sem tempo nem local, parcial se há evidência mas falta algum requisito, comparável no subconjunto explicitado quando permitido). Estado global comparable exige pelo menos duas candidatas e critérios/conjunto comum explicitamente definidos; não significa logística comprovada. Uma base com dados completos sem outra equivalente continua alternativa individual. Local-only deve ser descrito separadamente. Retornar reasons, gaps, scope, contagens, conjunto comparado e versão de política.
- Não fixar 80% como requisito global antes de validar experimento executável de REC01. Usar avaliação por níveis; todos os imperdíveis devem ter tempo conhecido ou ser local explicitamente identificado para destaque preliminar, mas retorno/última milha seguem pendentes. Cobertura de 60/70/80/90/100% é um indicador descritivo para calibrar destaque, não veto à exibição nem ranking. Começar por comparações de escopo completo entre bases com conjunto ferroviário igual, depois comparações condicionais somente sobre conjuntos comuns relevantes (>=2 destinos, explicitar os excluídos e não omitir imperdíveis para conclusão global). Lista de um destino admite comparação daquele trajeto, sem extrapolar.
- Se não houver comparação adequada, mostrar de forma útil as referências existentes e pendências prioritárias; jamais inventar vencedora, penalizar ausência como impossibilidade, ou ocultar candidatas. Ordenação visual estável por critérios declarados, não pelo menor tempo médio parcial. Empates explícitos. Comparações e critérios qualitativos não são rankings globais.

### 4.4 Feasibility assessment — revisão de 21/11/2026
Triagem reproduzida sobre JSON reais de main: 30 bases históricas + 4 DATA23, 48 destinos do registro reconstruído (attractions_2027, exploration_bases_2027, cidades históricas e TRIP01), 581 pares direcionais únicos com duração positiva e URL https após precedência reproduzida em JavaScript; 571 pares dentro do universo base × destino selecionável (34 × 48 = 1.632 combinações brutas, antes de excluir locais). Usados os JSONs five_base_comparison_evidence, base_city_rail_evidence_expanded, base_destination_routes, dq30_mobility_pilot, exploration_bases, routes7_priority_reference (apenas fastest_provenance corroborated_city_level), rail_gap_enrichment e DATA10/11/12/13/22/23, em ordem de precedência. Não é execução do Python/validadores nem verificação editorial externa; REC01 deve reproduzir usando os loaders e a projeção real, pinando SHA e publicando script/teste reproduzível; diferenças de alias/schema/validação devem ser reconciliadas. Os números abaixo medem presença documental, não horários ou viabilidade.

Cenários (I=5 imperdível, Q=3 quero conhecer, T=1 talvez):
- FR: Paris I, Strasbourg I, Colmar Q, Nancy Q, Metz T.
- Multi: Paris I, Cologne Q, Brussels Q, Basel I, Lucerne T.
- Fronteira: Luxembourg City I, Trier Q, Saarbrucken T, Metz I.
- Imperdíveis: Paris, Strasbourg, Brussels, Basel, Interlaken, Amsterdam, todos I.
- Pequena: Paris I, Colmar Q, Basel T.
- Grande: Paris I, Strasbourg I, Colmar Q, Brussels Q, Bruges T, Amsterdam I, Cologne Q, Aachen T, Luxembourg City Q, Basel I, Lucerne T, Interlaken Q.
- Suplementar: Obernai I, Lucerne Q (os dois IDs TRIP01).

Todas as listas usam IDs presentes no registro reconstruído. Cada cenário considera 34 bases. Cobertura limiar calculada sobre destinos não locais e exigindo todos os imperdíveis com tempo ou identificação local; 100% pode ter locais, por isso a coluna "todos com tempo, sem local" é mais restritiva. Sem tempo = 34 menos bases com pelo menos um tempo.

| Cenário | Bases com tempo | Sem tempo | >=60% | >=70% | >=80% | >=90% | 100% | Todos com tempo, sem local | Pares históricos / indicativos / locais | Utilidade provável |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| FR | 31 | 3 | 28 | 26 | 24 | 19 | 18 | 14 | 13 / 118 / 4 | comparação preliminar completa de ida para subconjunto de bases |
| Multi | 31 | 3 | 21 | 21 | 12 | 11 | 4 | 4 | 11 / 88 / 0 | comparação preliminar em quatro bases completas |
| Fronteira | 27 | 7 | 19 | 17 | 4 | 4 | 4 | 2 | 8 / 45 / 4 | duas bases completas sem local; demais condicionais |
| Imperdíveis | 31 | 3 | 5 | 5 | 5 | 5 | 5 | 4 | 20 / 115 / 1 | conjunto pequeno com referências completas; demais pendências |
| Pequena | 31 | 3 | 28 | 26 | 26 | 21 | 21 | 20 | 6 / 73 / 1 | boa triagem preliminar, não logística completa |
| Grande | 31 | 3 | 18 | 14 | 10 | 4 | 3 | 2 | 33 / 188 / 4 | duas bases completas sem local; comparações condicionais úteis |
| Suplementar | 7 | 27 | 7 | 5 | 5 | 5 | 5 | 5 | 0 / 12 / 0 | cinco bases com mínimos indicativos dos dois destinos; 27 sem duração |

Bases abaixo de 80% ou sem imperdíveis documentados: 10,22,30,29,8,24,29 respectivamente. Não confundir esse total com cidades inviáveis ou proibidas de comparar. Sensibilidade (número elegível a 80%; 5/3/1, 10/3/1, 3/2/1): FR 24/26/24; Multi 12/21/12; Fronteira 4/17/4; Imperdíveis 5/5/5; Pequena 26/26/26; Grande 10/14/10; Suplementar 5/5/5. Peso maior nos imperdíveis já exigidos pode inflar cobertura, sem adicionar evidência; justificar pesos e evitar limiar rígido.

Exemplos de médias ponderadas de mínimos sobre o MESMO conjunto completo sem locais, apenas para demonstrar cálculo: Multi Strasbourg 133 min (3 históricos, 2 indicativos), Mulhouse 137 (2/3), Metz 154 (1/4); Grande Mulhouse 163 (7/5), Lille 194 (6/6); Suplementar Colmar 77, Strasbourg 79, Mulhouse 83 (todos só indicativos). Não são vencedoras nem tempo típico; origem/destino, estação, data, retornos e qualidade de fontes limitam a comparação.

Moradia: 12 das 30 históricas têm amostras históricas, nenhuma tem cotação elegível 2027 no snapshot, novas candidatas não têm cotações verificadas. Vida cotidiana/trabalho remoto e custos totais não têm métricas comparáveis para universo integral; perfis Econômico/Remoto não sustentam ranking no MVP. A documentação base_coverage_model já exige critérios comparáveis e não produz score. Priorizar pesquisas de retorno/última milha, imperdíveis ausentes de candidatas bem documentadas e destinos suplementares; não confundir intenção com evidência.

**Lacuna adicional P1:** DATA23 tem 10 pares, apenas Paris consta no registro atual: Saumur, Nantes, Tours, Chartres, Aix-les-Bains, Geneva, Chamonix, Saint-Malo, Dinan não entram na wishlist reconstruída. Angers, Annecy e Rennes têm referências fora do conjunto selecionável; Le Mans tem Paris. Não confundir candidatas pouco documentadas com integração completa; auditar os IDs no runtime antes de publicar resultados. Corrigir/reconciliar catálogo com fontes e validação de identidade em REC01 ou separar PR de dados explicitamente bloqueante para esse alcance. Não alterar snapshots. Priorizar os destinos que o usuário efetivamente seleciona.

**Conclusão:** MVP logístico é viável com resultados preliminares; motor multicritério completo não é justificado agora. REC01 deve reproduzir a triagem, verificar denominadores comuns, executar análise de sensibilidade de limiares/pesos com os loaders reais, validar casos de catálogo misto e registrar SHA. Não iniciar REC02 sem evidência reproduzível. Comparações condicionais em subconjuntos diferentes não formam uma ordenação transitiva; não encadear vitórias par a par para produzir ranking global. Distinguir falha de carregamento/validação de ausência documental; erro não deve gerar resultado aparentemente válido. Se os resultados divergirem, corrigir especificação antes de implementação.

### 4.5 Review de integração REC01/REC01B — situação real

- O CI do HEAD inicial de #185 (`bba4b2a3c4a4`, run 44932437003) executou 1.044 testes e reproduziu a triagem anterior com os loaders Python: 34 bases, 48 destinos, 54 históricos, 517 indicativos, 30 locais e 1.031 sem tempo. Os sete cenários coincidiram com as contagens da seção 4.4. Isso confirma o baseline anterior ao overlay, não os HEADs novos.
- #185: preservado limite manual 2–5; matriz interna permite uma ou todas as bases. Variação histórica foi explicitada como diferentes datas/tipos de observação ou condições não reconciliadas, sem inferir contradição. DQ32 preserva proveniência DATA22/23. Diagnóstico imprime cobertura por base, imperdíveis, lacunas e contagens de comparação completa/parcial/insuficiente; três cenários DATA23 são executados quando IDs estão no catálogo, caso contrário explicitamente reportados como ausentes.
- #186: catálogo exploratório adiciona Angers, Le Mans, Annecy, Rennes, Saumur, Saint-Malo e Dinan, com fotos contextuais de atrações e créditos. Universo combinado esperado: 55 destinos (confirmar via CI). Seis endpoints ferroviários continuam sem entrada turística: Nantes, Tours, Chartres, Aix-les-Bains, Geneva, Chamonix. Não inventar identidade/atrativo.
- Decisão de domínio: opção B temporária. DATA23 ainda não reúne contrato canônico completo de passeio/etapa/identidade para promoção ao TripPlan. A interface explicita a limitação na descoberta, wishlist, comparação, quadro de destinos e organização; destino desejado nunca vira planejado sem ação e contrato válido. Evoluir suporte de planejamento em PR complementar após auditoria dos contratos de passeio, restauração e custo.
- #187 é integração temporária dos incrementos, sem merge autorizado. Workflow exclusivo gera diagnóstico dos dez cenários e benchmark real/sintético; validações de runtime atuais, medições, AppTest e verificação visual ainda dependem dos resultados. Não afirmar foto carregada apenas por URL/crédito ou fallback testado.
- Gate REC02 permanece FECHADO até confirmar CI dos HEADs finais, diagnóstico combinado reproduzido, paridade, benchmark e regressões. Não alterar REC02–05 antecipadamente.

## 5. Arquitetura, segurança e performance

Funções puras e dependências injetáveis para testes; separar montagem de evidências, avaliação, projeção de apresentação e Streamlit UI. Propor base_recommendation_model.py, base_recommendation_preferences.py, base_recommendation_projection.py, base_recommendation_ui.py, adaptando nomes à arquitetura existente. Evitar refatoração especulativa: extração mínima compartilhada com UX503. Sem LLM/RAG, chamadas de rede no cálculo ou dependência de API de rota em reruns.
- Complexidade esperada O(B×D) para construção das células com índices; evitar scans repetidos e recarregamentos por célula. Não impor limite visual ao processamento. Medir tempo/memória contra universo real e cenário sintético de até 200 interesses distintos (limite atual da lista, não atingível com apenas 48 IDs reais); Pareto fora do MVP.
- Cache somente dados versionados/públicos; não compartilhar preferências privadas via cache global. Invalidar resultados derivados quando lista, escopo, preferências ou dados de referência mudarem. Sem persistir cópias divergentes. UI com callbacks pré-widget e one-shot navigation requests, keys estáveis/distintas e proteção contra estado restaurado inválido.
- Não modificar TripPlan, base oficial, datas, passeios, orçamentos, GCS, favoritos ou interesses por renderização/recomendação; apenas ações explícitas já suportadas podem alterar os respectivos contratos. Simular sem promover cenário nem descartar edição. Não expor dados pessoais, credenciais ou conteúdo de armazenamento privado.
- Documentar limites de comparabilidade e consistência entre resumo, cartão, matriz, fonte, orçamento e pendências.

## 6. Entregas incrementais propostas

### REC01 — Matriz de evidências e feasibility reproduzível (fundação)
Extrair projeção compartilhada com UX503/DQ32; preservar contratos/snapshots. Testar paridade célula a célula, reconciliar catálogo DATA23, reproduzir os sete cenários com loaders Python reais e SHA pinado, calibrar limiares e confirmar o escopo explícito. Sem interface nova. Gate obrigatório para REC02.

### REC02 — Motor determinístico de recomendação
Consumir REC01; implementar estados e métricas logísticas, prioridades, cobertura, comparações condicionais e razões. Sem score multicritério, perfis ou sliders. Testar sensibilidade e propriedades; produzir exemplos reproduzíveis. Sem mudança visual.

### REC03 — UX e jornada (MVP utilizável)
Consumir REC02. Implementar CTA, atividade de sugestões em Explorar → Comparar bases, cartões, controle de escopo, transferência de seleção para comparação/ficha, retorno a Minha lista, atalhos na jornada. Preservar rotas e estado existente. Validar desktop/mobile e acessibilidade. Sem alterar base oficial.

### REC04 — Simulações e orçamento
Reusar cenários existentes, orçamento e mapa quando houver suporte; só considerar perfis econômicos/remotos e pesos multicritério após métricas comparáveis comprovadas; mostrar impacto financeiro comparável, origem de valores, moeda/unidade, datas, desconhecidos e limitações. Não criar conversões, estimativas ou cotações fictícias. Se base não for suportada por simulador, exibir motivo e ação de pesquisa, não bypass. Testar ida/volta entre cenário, sugestão, comparação e plano.

### REC05 — Pesquisa orientada à decisão e auditoria
Gerar pendências derivadas e não persistidas: rotas imperdíveis faltantes, retornos, moradia e dados que impedem comparação. Priorizar por preferência e lacuna observável (não afirmar impacto quantitativo sem análise); reusar página Pendências. Documentar performance, dados críticos, limites e roadmap de enriquecimento; auditar jornada e regressões. Sem disparar pesquisa externa automaticamente.

REC01→REC02→REC03 são núcleo MVP; REC04/05 complementam e podem ser fatiados. Cada PR deve partir da base adequada ou declarar claramente dependência de PR empilhado, fila de merge, testes e rollback. Não misturar novos lotes de dados com alterações de domínio sem necessidade. Antes de implementar, relatar plano técnico, contratos e riscos identificados.

## 7. Testes obrigatórios e critérios de aceite

- Todos os IDs ativos do universo candidato entram na análise de forma adaptativa, inclusive adição futura de cidade sem alterar constantes visuais. Testar uma, várias, até 200 preferências em fixture sintética, vazia, todos descartados, destinos locais, escopos Itália/temporada, lista mista, aliases, mudança de prioridade, filtros visuais e dados ausentes.
- Paridade entre recomendação e comparação manual: Le Mans→Paris (56 min indicativos DATA23 no snapshot revisado), Angers→Saumur, Annecy→Geneva, Rennes→Saint-Malo quando elegíveis; testar fontes antigas prevalentes, secundárias, conflitos, ausência de retorno, rota inexistente no catálogo e não inferência inversa. Não fixar 56 min como verdade universal; usar fixture/contrato do dataset identificado e verificar HEAD.
- Teste contra viés de cobertura: candidata com 2/10 rotas rápidas não vence outra com 9/10 por mera média; ausência não vira 0 nem falha de serviço. Avaliar cobertura ponderada e dos imperdíveis, denominadores comuns, critérios financeiros indisponíveis, pesos inválidos, empates, determinismo com reordenação de entradas e ausência de duplicação.
- Monotonicidade apenas sob condições equivalentes (mesmos pares, cobertura e evidência): melhoria de tempo não piora adequação logística; aumentar prioridade deve melhorar importância relativa do destino, não necessariamente posição de toda cidade.
- Testar compatibilidade de importação/restauração, favoritos, seleção manual anterior, navegação, orçamento, dados opcionais, tratamento de falha de foto, mobile e controles acessíveis. Usar Streamlit AppTest quando viável; teste de integração com callbacks reais e reruns.
- Verificar integridade por deep copy antes/depois do TripPlan, interesses, datasets e cenário oficial; nenhuma escrita ou efeito colateral inesperado. Testar ações explícitas separadamente.
- Rodar validadores de pesquisa, suíte completa, checks de estilo/compilação existentes e GitHub Actions no HEAD final. Realizar validação visual manual desktop/mobile se ambiente disponível; não confundir AppTest com inspeção visual. Informar exatamente o que não foi executado. Não relaxar validação, desativar testes ou alterar snapshots para fazer CI passar.

## 8. Entrega de cada etapa

Descrição do PR com objetivo, escopo, módulos, decisões arquiteturais, comportamento anterior/novo, exemplos de evidência, metodologia, riscos e limitações, testes executados/resultados, cobertura, SHA, CI e itens pendentes. Incluir matriz de impactos por tela, checklist de aceite e passos de teste manual. Para REC03+, demonstrar jornada completa com captura visual se possível.

## 9. Perguntas para review desta proposta

1. O recorte de temporada versus lua de mel pode ser resolvido com contratos atuais? Qual o comportamento padrão se não houver escopo?
2. A política de comparação por conjunto comum e limiares evita viés sem excluir excessivamente as cidades? Que benchmarks e análise de sensibilidade justificam os valores?
3. Como preservar todas as proveniências e evitar dupla contagem ou inconsistência entre UX503 e a recomendação?
4. Quais perfis podem produzir recomendações reais com os dados atuais e quais devem exibir apenas pendências? Como apresentar isso sem frustrar o usuário?
5. Como se encaixam favoritos, cenários, orçamento e candidatas não suportadas no plano oficial? Existe risco de duplicação de estado?
6. O MVP logístico REC01–03 é suficientemente pequeno e testável? Há melhor separação de dependências ou riscos de regressão?
7. Que evidências e testes faltam para aprovar a implementação? Identificar P0/P1/P2, propostas concretas e itens conscientemente fora de escopo.

**Resultado pretendido:** transformar pesquisa em apoio à decisão explicável, sem falsa precisão nem mutação silenciosa do planejamento. Este PR é somente o prompt para análise; a implementação futura depende de revisão.
