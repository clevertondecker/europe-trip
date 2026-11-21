# PROMPT — REC01–REC05: recomendações personalizadas de cidades-base

**Projeto:** Nossa Europa 2027  
**Repositório:** https://github.com/clevertondecker/europe-trip  
**Estado:** proposta para revisão; não é implementação nem autorização de merge.

Atue como Staff Software Engineer, Product/UX Engineer, Senior Python/Streamlit Engineer e especialista em sistemas de recomendação multicritério e qualidade de evidências. Antes de escrever código, inspecione o HEAD atualizado de main, os contratos e testes existentes. Confirme ou refute as premissas deste documento, registre divergências e preserve funcionalidades atuais. Execute em incrementos independentes, revisáveis, com CI verde. Não implemente todos os incrementos simultaneamente nem faça merge sem autorização.

## 1. Problema e objetivo

Hoje o usuário descobre atrações, registra destinos e prioridades, e escolhe manualmente 2–5 cidades para comparar. Queremos inverter essa dependência: sugerir automaticamente candidatas a partir dos destinos escolhidos, explicando adequação, cobertura, incertezas e compromissos entre logística, moradia e qualidade de vida. A pesquisa de cidades deve continuar dinâmica (34 candidatas no DATA23, nunca uma quantidade fixa no algoritmo). A escolha exploratória não equivale a confirmação de residência, reserva ou alteração do TripPlan.

Contexto: lua de mel na Itália seguida de temporada europeia com trabalho remoto, passeios sobretudo nos fins de semana, viagem após 04/09/2027. Datas, duração, valores e preferências atuais do plano devem ser lidos dos contratos existentes; não codificar premissas pessoais como regras universais. Priorizar acesso ferroviário, moradia mobiliada para dois adultos, conectividade para trabalho remoto e orçamento. Tratar Itália/lua de mel e temporada europeia como escopos distintos: não usar automaticamente destinos da lua de mel para sugerir a base da temporada.

## 2. Auditoria obrigatória antes da implementação

- ux_navigation.py, app.py, ux504_guided_journey_model.py e ux504_guided_journey_ui.py: rotas, callbacks, jornada e atalhos existentes.
- ux501_destination_discovery_model.py, trip01_supplemental_discovery.py, ux502_destination_interests_model.py e ux502_destination_interests_ui.py: IDs, prioridades, lista persistida, escopos, GCS e migrações.
- ux503_destination_base_comparison_model.py/UI, rail_reference_projection_model.py, routes7_comparison_projection.py, evidence_query_model.py, rail_evidence_unified_model.py e ux506_decision_readiness_projection.py: matriz histórica, overlays, precedência, divergências, associação de ida e retorno.
- base_research_expanded_model.py, base_coverage_model.py, base_scenario_model.py, city_profiles_model.py: pesquisa dinâmica, cesta fixa de referência, candidatas, base oficial, moradia, dados opcionais.
- Verificar módulos de orçamento, cenários, mapa, favoritos, roteiro e persistência, seus testes e documentação. Reutilizar caminhos canônicos de navegação e ações existentes.
- Documentar conjunto real de destinos elegíveis, universo de bases, eventuais aliases/IDs, cobertura por categoria, limites de datas e quais cidades podem ser usadas em cenários versus oficializadas.

## 3. Jornada e UX

Manter áreas principais: Minha viagem, Explorar, Meu roteiro e Orçamento. Não criar uma quinta área ou editor paralelo.

Fluxo flexível: Descobrir lugares → Minha lista → Encontrar cidade-base → Comparar alternativas → Simular estadia → Montar/organizar roteiro → Revisar orçamento e pendências. Permitir saltar, retornar e reavaliar sem perda de escolhas.

- Em Minha lista, exibir CTA principal "Encontrar cidades-base para nossos destinos"; manter comparação manual acessível. Se lista vazia ou toda descartada, orientar descoberta.
- Na área Explorar → Comparar, disponibilizar atividades "Cidades sugeridas" e "Comparação personalizada", sem duplicar navegação. A entrada pelo CTA deve chegar diretamente na atividade sugerida; links legados continuam funcionando.
- Na jornada inicial, oferecer sugestão como próximo passo quando existirem interesses relevantes; acesso à montagem do roteiro não deve ser bloqueado. Abrir uma tela não significa concluir uma decisão.
- Começar com perfil equilibrado e apresentar resultados sem exigir formulário longo. Permitir perfis Logística, Economia, Vida cotidiana/trabalho remoto e Exploração internacional; configurações avançadas recolhidas, com explicação e reset.
- Mostrar lista efetivamente avaliada (todos os destinos elegíveis, não apenas filtro visual de cinco destinos do UX503), prioridades, escopo temporada/Itália e opção de ajustar interesses na fonte canônica. Se não houver classificação de escopo existente, oferecer filtro explícito e transitório, com indicação clara, sem inferir escopo pela nacionalidade do destino nem duplicar lista persistida.
- Mostrar poucas sugestões iniciais (por exemplo 3–5, adaptável à quantidade e evidência), razões concretas, métricas, lacunas, fotos com fallback/crédito quando disponíveis. Acesso a todas as candidatas, inclusive pouco pesquisadas. Não rotular uma vencedora quando as evidências não sustentarem isso.
- Ações: abrir ficha da cidade, favoritar, selecionar 2–5 bases para comparador existente, voltar à lista, simular estadia, continuar roteiro. Transferir IDs e escopo selecionado, sem sobrescrever indiscriminadamente seleções manuais anteriores; oferecer ação explícita para substituir seleção.
- Distinguir base de referência oficial, cenário exploratório e cidade candidata. Não oferecer confirmação inválida para candidatas não suportadas pelo TripPlan. Indicar limitações de forma acionável.
- Layout responsivo, labels acessíveis, hierarquia clara, progressive disclosure, estados vazios/erro/baixa cobertura, sem depender exclusivamente de cor ou hover. Não repetir tabelas e informações em várias telas.

## 4. Motor de recomendação: sem falsa precisão

### 4.1 Projeção canônica
Generalizar internamente o cálculo usado pelo UX503 para qualquer quantidade válida de bases, mantendo limite visual 2–5 no comparador público e compatibilidade de contratos. Reusar precedência e overlays do rail_reference_projection_model; nenhuma nova fonte mutável, nem substituir snapshots históricos. Indexar por par direcional (base_id, destination_id), deduplicar aliases e preservar fonte, data, categoria, confiança, estação, divergência e limitações. Não deduzir rotas inversas nem percursos via terceiros.

Separar: histórico documentado; referência indicativa da operadora; referência secundária; local com acesso pendente; sem tempo; divergência. Local não é zero minutos. Falta de informação não é inviabilidade e não é zero. Não imputar tempo, preço, frequência ou retorno. Não promover mínimo de ida a tempo típico porta a porta ou viabilidade de bate-volta. Dados 2026 não confirmam 2027. Manter cesta fixa comparável histórica de 15 destinos isolada da matriz personalizada.

### 4.2 Preferências e métricas
Usar prioridades UX502: must_visit=5, interested=3, maybe=1, discarded excluído. Pesos são iniciais, explícitos, testáveis e não verdades universais. Para cada cidade separar:
- cobertura ponderada de tempos = soma dos pesos dos destinos com duração utilizável / soma dos pesos dos destinos elegíveis para avaliação de deslocamento; explicitar tratamento separado de destinos locais e denominador; cobertura dos imperdíveis separadamente; contagem de históricos e indicativos, sem duplicar pares.
- mínimo médio ponderado de ida para pares com duração conhecida (soma peso*minutos / soma pesos observados), sempre exibir denominador e avisar que não é tempo médio típico.
- destinos com referência dentro de limiares configuráveis (60/120/180 minutos), distinguir contagem de deslocamentos ferroviários de destinos locais e pendências de retorno.
- moradia (amostra histórica vs cotação real comparável para mesmo período, ocupação, taxas), custos de transporte comprovados, trabalho remoto, qualidade de vida e diversidade de países relevantes para os interesses selecionados. Não contar país como acessível se apenas houver indicação de ida; tratar como país com referência de ida. Evitar dupla contagem de localização internacional e logística.
- preferências sugeridas por perfil (logística/moradia/vida cotidiana/diversidade): equilibrado 45/25/20/10; explorador 65/15/10/10; econômico 30/50/15/5; remoto 30/25/40/5. Validar pesos não negativos, soma positiva e normalização determinística. Expor apenas critérios efetivamente suportados. Não renormalizar pesos silenciosamente por cidade e assim beneficiar falta de dados.

### 4.3 Comparabilidade, elegibilidade e incerteza
Antes de ordenar, definir e documentar política de comparação previamente (limiares de cobertura, imperdíveis, qualidade de evidência, conjunto comum mínimo). Propor inicialmente cobertura ponderada >=80% e todos os imperdíveis com referência utilizável ou local explicitamente identificado como requisitos para destaque logístico preliminar, sujeitos à validação de sensibilidade. Não significam probabilidade de acerto nem viabilidade. Se insuficientes, listar alternativas para pesquisa, não vencedora.
- Comparação de tempo deve usar o mesmo conjunto de destinos e pesos para todas as cidades comparadas, ou deixar diferença de denominador explícita e não ordenar médias como se fossem comparáveis. Não permitir um conjunto comum de apenas um destino induzir superioridade global; se conjuntos diferem, indicar insuficiência ou comparações condicionais claramente rotuladas.
- Separar adequação, cobertura e qualidade da evidência; não misturar em percentual de confiança arbitrário. Não manipular duração com penalidade arbitrária por confiança.
- Critérios sem métricas comparáveis (inclusive moradia para 2027 e vida cotidiana) permanecem indisponíveis, sem score geral artificial. Perfis servem para destacar evidências/pendências; se critério prioritário desconhecido, avisar que não se pode recomendar por ele. Não introduzir 0–100 de qualidade no MVP sem contrato e justificativa. Alternativas por objetivo e fronteira de Pareto somente sobre critérios, escopos e denominadores de fato comparáveis; se não forem, omitir. Empates estáveis, desempate transparente sem confundir ordenação visual com qualidade.
- Explicar as razões por cidade com valores e fonte; exibir o que mudaria a conclusão, sem inventar probabilidades ou impacto causal. Cidades sem evidência ficam pesquisáveis. Sem ranking universal nem autoeleição.
- Sensibilidade: validar resultados com mudanças de pesos, limiares, prioridades e cobertura; não esconder instabilidade. Política deve ser versionada em código/documentação, sem alterar schemas persistidos no MVP.

## 5. Arquitetura, segurança e performance

Funções puras e dependências injetáveis para testes; separar montagem de evidências, avaliação, projeção de apresentação e Streamlit UI. Propor base_recommendation_model.py, base_recommendation_preferences.py, base_recommendation_projection.py, base_recommendation_ui.py, adaptando nomes à arquitetura existente. Evitar refatoração especulativa: extração mínima compartilhada com UX503. Sem LLM/RAG, chamadas de rede no cálculo ou dependência de API de rota em reruns.
- Complexidade esperada O(B×D) para construção das células com índices; evitar scans repetidos e recarregamentos por célula. Não impor limite visual ao processamento. Medir tempo/memória contra universo real e cenário de 200 interesses (limite atual da lista); se Pareto, medir custo adicional separado.
- Cache somente dados versionados/públicos; não compartilhar preferências privadas via cache global. Invalidar resultados derivados quando lista, escopo, preferências ou dados de referência mudarem. Sem persistir cópias divergentes. UI com callbacks pré-widget e one-shot navigation requests, keys estáveis/distintas e proteção contra estado restaurado inválido.
- Não modificar TripPlan, base oficial, datas, passeios, orçamentos, GCS, favoritos ou interesses por renderização/recomendação; apenas ações explícitas já suportadas podem alterar os respectivos contratos. Simular sem promover cenário nem descartar edição. Não expor dados pessoais, credenciais ou conteúdo de armazenamento privado.
- Documentar limites de comparabilidade e consistência entre resumo, cartão, matriz, fonte, orçamento e pendências.

## 6. Entregas incrementais propostas

### REC01 — Matriz de evidências reutilizável (fundação)
Extrair projeção de leitura para escala dinâmica; preservar contratos/políticas de UX503 e todos os snapshots. Testar paridade célula a célula com comparador, incluindo DATA23, overlays anteriores, retornos, localidades, conflitos e aliases. Relatar cobertura real da seleção de teste em todas as bases. Sem interface nova.

### REC02 — Motor determinístico de recomendação
Consumir REC01; implementar prioridades, preferências, cobertura, elegibilidade, métricas comparáveis, explicações e estados de insuficiência; testar sensibilidade e propriedades. Entregar exemplos reproduzíveis com dados reais e fixtures artificiais rotuladas. Não produzir score fictício. Sem mudança visual.

### REC03 — UX e jornada (MVP utilizável)
Consumir REC02. Implementar CTA, atividade de sugestões na aba Comparar, cartões, perfis, controle de escopo, transferência de seleção para comparação/ficha, retorno a Minha lista, atalhos na jornada. Preservar rotas e estado existente. Validar desktop/mobile e acessibilidade. Sem alterar base oficial.

### REC04 — Simulações e orçamento
Reusar cenários existentes, orçamento e mapa quando houver suporte; mostrar impacto financeiro comparável, origem de valores, moeda/unidade, datas, desconhecidos e limitações. Não criar conversões, estimativas ou cotações fictícias. Se base não for suportada por simulador, exibir motivo e ação de pesquisa, não bypass. Testar ida/volta entre cenário, sugestão, comparação e plano.

### REC05 — Pesquisa orientada à decisão e auditoria
Gerar pendências derivadas e não persistidas: rotas imperdíveis faltantes, retornos, moradia e dados que impedem comparação. Priorizar por preferência e lacuna observável (não afirmar impacto quantitativo sem análise); reusar página Pendências. Documentar performance, dados críticos, limites e roadmap de enriquecimento; auditar jornada e regressões. Sem disparar pesquisa externa automaticamente.

REC01→REC02→REC03 são núcleo MVP; REC04/05 complementam e podem ser fatiados. Cada PR deve partir da base adequada ou declarar claramente dependência de PR empilhado, fila de merge, testes e rollback. Não misturar novos lotes de dados com alterações de domínio sem necessidade. Antes de implementar, relatar plano técnico, contratos e riscos identificados.

## 7. Testes obrigatórios e critérios de aceite

- Todos os IDs ativos do universo candidato entram na análise de forma adaptativa, inclusive adição futura de cidade sem alterar constantes visuais. Testar uma, várias, 200 preferências, vazia, todos descartados, destinos locais, escopos Itália/temporada, lista mista, aliases, mudança de prioridade, filtros visuais e dados ausentes.
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
6. O MVP REC01–03 é suficientemente pequeno e testável? Há melhor separação de dependências ou riscos de regressão?
7. Que evidências e testes faltam para aprovar a implementação? Identificar P0/P1/P2, propostas concretas e itens conscientemente fora de escopo.

**Resultado pretendido:** transformar pesquisa em apoio à decisão explicável, sem falsa precisão nem mutação silenciosa do planejamento. Este PR é somente o prompt para análise; a implementação futura depende de revisão.
