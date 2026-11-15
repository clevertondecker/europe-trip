# Consultor de destinos e estilos — implementação 15/11/2026

## Resumo
Implementado no aplicativo [Nossa Europa 2027](https://nossa-europa-2027.streamlit.app/) (Roteiro → Consultor inteligente), sem LLM, com descoberta de destinos mesmo quando não existe passeio selecionado, comparações financeiras com destinos concretos e aprovação explícita antes de alterar o plano.

## Entregas (7 steps)
1. **Sem propostas vazias** — `travel_optimizer.propose_schedule` retorna lista vazia quando o roteiro não contém passeios, elimina alternativas repetidas e não mostra alternativas sem mudança real. O consultor apresenta o próximo passo correto.
2. **Descoberta** — `destination_recommender.py` seleciona destinos não escolhidos usando os 11 destinos e 50 atrações do catálogo histórico. Reavalia quando cidade-base, perfil, limites de transporte e pernoite mudam. Exclui destinos descartados e atrações marcadas "Descartar"; recomendações mostram fonte e horários ausentes.
3. **Custo-benefício** — pontuação relativa por interesse, custo conhecido, conforto e disponibilidade. Ausência de tarifa não conta como custo zero; deslocamento conhecido é de estação a estação, e retorno e preços 2027 continuam dependentes de verificação.
4. **Cenários** — `travel_profile_scenarios.py` cria roteiros **Econômico / Equilibrado / Aproveitar ao máximo** a partir de atrações e destinos reais, com quantidades máximas ilustrativas 2 / 4 / 6 destinos (incluindo os já escolhidos). `advisor_finance.py` + `unified_budget.py` recalculam projeções a partir dos custos históricos conhecidos, EUR/CHF convertidos com câmbio indicado, taxa de moradia histórica e verba preexistente para excursões. **Não** aplica aumento percentual arbitrário pelo estilo.
5. **Aceite seguro** — `recommended_itineraries.py` exige aprovação explícita para adicionar uma recomendação ou aceitar um roteiro completo; mantém escolhas anteriores, respeita destinos descartados e não altera dias já aprovados. Sugestões sem horário/documentação completa permanecem pendentes no calendário.
6. **Interface** — `discovery_ui.py` mostra destinos, fotos com crédito Wikimedia, atrações, valores parciais do casal, links oficiais, avisos de retorno, botão "Quero visitar", descarte explícito, opção de pesquisar pernoites e comparação dos três estilos. Os botões só chamam a persistência depois que o proprietário aprova ou habilita salvamento (não há escrita na prévia).
7. **Regressão/CI** — `tests/test_destination_discovery.py` valida plano vazio, exclusões, troca de cidade-base, diferenças dos três perfis, aprovação/recusa/obsolescência, orçamento/margem e pernoite; tests legados adaptados para não esperar alternativas vazias.

## Como testar
1. Entre em **Roteiro → Consultor inteligente**.
2. Com nenhuma atração escolhida, observe **Descobrir lugares para conhecer**. Você deve ver sugestões como Colmar, Strasbourg e cidades próximas adequadas à base.
3. Clique em **Quero visitar** numa sugestão. Ela passa ao planejamento único sem reserva.
4. Abra **Comparar estilos de viagem** (na mesma página). Compare destinos concretos, dias usados, orçamento total projetado e os valores faltantes.
5. Selecione **Aceitar este roteiro sugerido** para efetivar os novos destinos e as datas que tenham uma janela verificada pelo calendário. Depois clique em **Salvar planejamento** — ou use salvamento automático se já optou por ele.
6. Troque cidade-base ou teto financeiro e confirme a recomputação.

## Limitações essenciais
- Dados de transportes e ingressos são históricos (maioria observada em 2026) e **não são cotações confirmadas para 2027**. Muitas viagens não têm horário de retorno nem tarifa normal. Sem dados, o sistema orienta a pesquisa e não confirma viabilidade.
- Projeções são calculadas usando as rubricas da planilha: uma despesa desconhecida não é representada como preço zero; o número projetado é **parcial/condicional**.
- O ranking é heurístico, não uma avaliação treinada em dados de usuários.
- O roteiro não é uma reserva, e não garante abertura/ingresso/serviço de trem.
- Fotos são recursos externos Wikimedia com crédito; a renderização depende da disponibilidade dos links.
- O repositório GitHub atual é público; **não colocar dados pessoais** nos planos. Login Google, controle SHA e confirmação explícita continuam ativos.
- O Google Drive continua somente leitura e a decisão D-004 sobre a cidade-base permanece em aberto.
- Não foi feita inspeção visual do aplicativo hospedado em navegador real; GitHub Actions + Streamlit AppTest testam código e widgets.

## Arquivos
`destination_recommender.py`, `travel_profile_scenarios.py`, `recommended_itineraries.py`, `discovery_ui.py`, `travel_optimizer.py`, `travel_advisor_ui.py`, `planning_store.py`, `tests/test_destination_discovery.py`, testes antigos e `.github/workflows/validate.yml`.
