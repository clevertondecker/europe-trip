# PROMPT DE IMPLEMENTAÇÃO — Catálogo de atrações e roteiro adaptativo por cidade-base
Versão: 1.0 | 14/11/2026 | Projeto: Nossa Europa 2027

## Papel e missão
Atue como engenheiro de software Python/Streamlit sênior, pesquisador de viagens com rigor de fontes e designer de UX para o projeto GitHub `clevertondecker/europe-trip`. Implemente uma experiência intitulada **Explorar atrações** dentro da página **Roteiro**, conectada ao **Mapa & destinos**, **Comparar cidades**, **Calendário** e **Orçamento integrado**.

O objetivo é permitir ao casal responder: "Se morarmos em Mulhouse, Strasbourg, Metz ou Nancy, quais cidades e atrações poderemos conhecer, quanto tempo leva de verdade, quanto custa para duas pessoas, o que cabe num bate-volta e como isso afeta os R$60–70 mil da viagem?". Não entregar apenas uma lista de países ou tempos de trem.

## Contexto obrigatório
- Casamento 04/09/2027; saída do Brasil somente depois.
- Dois adultos, Itália primeiro (~10 dias; Roma + Costa Amalfitana, bases Salerno ou Maiori), depois ~55–65 dias numa ÚNICA base francesa a escolher entre Mulhouse, Strasbourg, Metz e Nancy.
- Sem carro; priorizar trem, transporte público, ferry, caminhada.
- 20–30 dias iniciais de férias; após isso, trabalho remoto para o Brasil, com horas livres sujeitas ao fuso França/Brasil. Saídas longas devem priorizar férias/finais de semana.
- Teto financeiro do casal de R$60k ou R$70k para viagem inteira, com reserva emergencial já incluída.
- A decisão D-004 de cidade-base segue ABERTA. Selecionar uma cidade na tela não aprova nem grava uma decisão no Drive.
- Fonte oficial e sincronização atual do Drive: não reescrever planilha, decisões, Secrets ou credenciais; pesquisas históricas seguem versionadas em GitHub e **não** representam disponibilidade 2027.
- Aproveitar arquivos existentes: `app.py`, `assets/styles.css`, `catalog.py`, `itinerary_planner.py`, `route_preview.py`, `calendar_model.py`, `unified_budget.py`, `data/itinerary_options_2027.json`, as decisões e tarefas já sincronizadas.
- Manter visual A+B: app de viagens com fotografias e mapas, mas informação financeira clara, comparável e sem excesso de texto.

## Escopo de pesquisa — primeiro release
Pesquise no mínimo, com fonte oficial sempre que possível:
1. **Dentro de cada possível base**
   - Mulhouse: Place de la Réunion / centro, Cité du Train, Musée National de l’Automobile e outras atrações oficiais relevantes.
   - Strasbourg: Catedral, Petite France, Grande Île, Ponts Couverts, Barrage Vauban, distrito europeu e demais atrações verificadas.
   - Metz: Catedral Saint-Étienne, Centre Pompidou-Metz, Musée de la Cour d’Or, Porte des Allemands e parques conforme fontes.
   - Nancy: Place Stanislas, Parc de la Pépinière, Villa Majorelle, Musée de l’École de Nancy e patrimônio Art Nouveau.
2. **Cidades vizinhas e países próximos**: Colmar (Petite Venise, centro histórico), Freiburg (Münster, Altstadt, Schlossberg), Basel (centro e museus conforme fontes), Luxemburgo (Bock Casemates, Corniche, Grund), e alternativas próximas relevantes descobertas durante a pesquisa.
3. **Alpes suíços com etiqueta "pode exigir pernoite"**: Interlaken, Lauterbrunnen, Kandersteg/Oeschinensee. Estadia, teleférico e trens até a região são custos distintos.
4. **Reuso futuro da fase italiana**: a mesma arquitetura deve comportar Roma, Salerno/Maiori, Amalfi, Positano, Capri, Minori e atrações internas, sem misturar as rotas italianas com as bases francesas.
5. Buscar pelo menos 5 atrações verificadas por cidade-base e 3 por destino de bate-volta prioritário, quando houver fontes; se faltar evidência, registrar lacuna em vez de criar itens fictícios. Evitar duplicar uma atração só para preencher quantidade.

Fontes iniciais a verificar:
- Strasbourg: https://www.visitstrasbourg.fr/en/discover/must-see-attractions/
- Mulhouse: https://www.tourisme-mulhouse.com/en/what-to-do-in-mulhouse/getting-around-mulhouse-by-public-transport/
- Metz: https://www.tourisme-metz.com/en/discover-metz-metropole/top-15-tourist-spots-in-metz-metropole
- Nancy: https://www.destination-nancy.com/en/tourisme/
- Colmar: https://www.tourisme-colmar.com/en/
- Freiburg: https://visit.freiburg.de/en/
- Luxemburgo: https://www.visitluxembourg.com/destinations/luxembourg-city
- Trens Grand Est: https://www.ter.sncf.com/grand-est/se-deplacer/lignes
- Desconto Fluo: https://www.ter.sncf.com/grand-est/tarifs-cartes/cartes-reduction/carte-fluo
- Suíça: https://www.sbb.ch/en e https://www.oeschinensee.ch/en/tarife-fahrplan/
A pesquisa deve ampliar e abrir páginas específicas de cada atração (preços, funcionamento e reservas), não depender só de páginas-guia.

## Modelo de dados: entidades separadas
Criar dados versionados como `data/attractions_2027.json`, `data/base_destination_routes_2027.json`, `data/outing_packages_2027.json` ou formato equivalente com validação.

**Attraction**: `id`, `place_id`, `name`, `category` (história, arquitetura, natureza, museu, gastronomia, foto/paisagem), `summary`, `lat`, `lon`, `suggested_visit_minutes`, `ticket_price` (valor, moeda, por pessoa ou casal, ida/volta quando aplicável, inclusões), `free_access` (true/false/unknown), `opening_hours`, `seasonality`, `reservation_required`, `photo_url` e `photo_credit/license`, `source_urls`, `checked_at`, `confidence`, `status`, `notes`. Nunca marcar grátis só porque não encontrou preço.

**RouteFromBase**: `base_id`, `destination_id`, `origin_point` (estação/centro, ou endereço da hospedagem se informado), `destination_point`, `transport_mode`, `distance_km` com `distance_kind` (ferroviária, rodoviária, caminhada ou linha reta), `travel_minutes_one_way` e `duration_kind` (trecho de trem, porta a porta ou estimativa), `transfer_count`, `walking_minutes`, `last_mile_minutes`, `return_last_departure`, `weekend_service_confirmed`, `fare_outbound`, `fare_return`, `fare_type`, `discount_requirements`, `source_url`, `checked_at`, `valid_for_date`, `missing_fields`.

**OutingPackage**: `id`, `base_id`, `destination_id`, `attraction_ids`, `title`, `morning/afternoon/evening`, `estimated_hours`, `cost_breakdown`, `feasibility`, `requires_overnight`, `season_restrictions`, `preferred_days`, `source_ids`. Permitir selecionar 2–5 atrações próximas na mesma visita sem contar duas vezes o transporte interurbano.

Todos os registros devem identificar natureza do valor (`historical_observation`, `operator_published`, `dated_quote`, `assumption`, `unknown`), unidade, moeda, data e fornecedor.

## Distâncias, horários e custos — invariantes
1. Gerar uma matriz **quatro bases × destinos**: Colmar, Strasbourg, Mulhouse, Metz, Nancy, Basel, Freiburg, Luxemburgo e Alpes, conforme relevância, sem inventar trechos indisponíveis. O MESMO destino deve ter tempos e custos próprios para cada base.
2. Nunca apresentar distância geográfica em linha reta como km ferroviários/rodoviários. Se só existir distância Haversine, rotular "linha reta (não é percurso)" e não usar para prometer duração.
3. Diferenciar **tempo dentro do trem** de **porta a porta**: deslocamento até estação + espera + baldeação + trecho(s) + percurso final. Sem informação, exibir "não verificado" e subtotal parcial.
4. Para cada passeio, avaliar capacidade de fazer ida/volta num sábado/domingo, horários de última volta, quantidade de baldeações, cansaço e necessidade de pernoite. Nunca deduzir disponibilidade para 2027 apenas de tabela 2026.
5. Custos para **duas pessoas**, rubricas separadas: ida, volta, bilhete urbano/última milha, entradas/visitas, alimentação adicional opcional, teleférico/ferry, hospedagem extra, taxas. O valor parcial deve ser rotulado "custo conhecido, incompleto".
6. EUR e CHF preservados separadamente; converter para BRL apenas com câmbio informado pelo usuário e data da taxa. Não somar moedas sem conversão explícita.
7. Fluo: o valor reduzido **exige cartão ou condições específicas**. Comparar cenário normal e cenário com desconto, incluindo custo do cartão e eventual acompanhante de fim de semana, apenas quando a regra oficial permitir.
8. Evitar dupla contagem no orçamento: "passeios" já têm verba na planilha. O usuário pode **substituir** a verba de excursões pela cesta detalhada de passeios ou somar apenas o excedente, com indicação visual. Nunca adicionar o custo integral como gasto adicional automaticamente.
9. Para ingressos gratuitos: confirmar se a parte pública é gratuita mas mirante/torre/visita guiada é paga; tratar separado.
10. Não usar preços/hora 2026 como garantia de 2027; separar "observado", "projeção" e "cotado para data".

## UX/visual obrigatório
Implementar seção **Roteiro → Explorar atrações**, com menu segmentado e estes elementos:
- Seletor de base: Mulhouse / Strasbourg / Metz / Nancy. Buscar base escolhida no estado de simulação, mas NÃO editar decisão D-004.
- Filtros: país, cidade, categoria, custo (gratuito/faixa/sem preço), tempo total, duração possível (fim de tarde, meio dia, dia inteiro, pernoite), prioridades e apenas rotas com fontes.
- Primeira faixa: quantidade de cidades acessíveis pesquisadas, atrações disponíveis, número de bate-voltas documentados, excursões que precisam de pernoite, custo conhecido do roteiro selecionado.
- **Cards fotográficos** com nome da cidade, país, 2–4 atrações destaque, distância e natureza do km, minutos de viagem (estação-estação/porta a porta), tempo recomendado, tarifa de transporte ida/volta para casal, soma de ingressos, total conhecido, aviso de custos faltantes e botão "Ver atrações".
- Clique "Ver atrações" abre ficha da cidade com fotos, mapa por pinos, atrações e informações de visita, possíveis agrupamentos em 1 dia, fontes oficiais e indicação de dias de abertura.
- Marcadores de mapa diferenciados para a base escolhida, outras cidades e atrações. Usar apenas coordenadas verificadas, sem linhas retas desenhadas como rota real; trajetos geográficos apenas se houver rota validada por serviço/licença apropriada.
- Filtros e seleção devem funcionar em telas móveis, com estados preservados durante a navegação; status ativo visualmente destacado.
- Ações "Quero visitar", "Opcional" e "Descartar" para atrações/pacotes; escolha persistida em sessão e exportável em JSON/Markdown se possível, sem afirmar sincronização com Drive. Controlar duplicados ao somar pacotes.
- Botão "Adicionar ao calendário" para um dia elegível (férias ou fim de semana quando possível), impedindo conflitos de datas/horários; preservar escolha da base e avisos de sazonalidade.
- Ligação "Simular custo no orçamento" com `unified_budget.py`, sem dupla contagem.
- "Comparar cidades" deve usar a diversidade de passeios e viabilidade como informação complementar de contexto — não modificar scores editoriais arbitrariamente.
- Evitar repetir um botão por fonte em cada linha: exibir links no detalhe/expander.

## Exemplos de validação manual obrigatória
- Mulhouse → Colmar: SNCF publica 18 min de trem e €5,40/pessoa/trecho **com Carte Fluo** (não total porta a porta). Para dois adultos, dois trechos, soma CONDICIONAL €21,60 só de trem, sem cartão.
- Strasbourg → Colmar: 32 min e €7,90/pessoa/trecho com Fluo; casal ida/volta €31,60, condicional.
- Mulhouse → Basel: 22 min e €4,70/pessoa/trecho com Fluo; verificar eventuais condições transfronteiriças antes de assumir validade.
- Metz ↔ Nancy: 38 min e €7/pessoa/trecho com Fluo; casal ida/volta €28, condicional.
- Luxemburgo: transporte público nacional é geralmente gratuito em classe padrão, porém a viagem desde a França e atrações específicas NÃO são necessariamente gratuitas.
- Oeschinensee: teleférico e acesso ferroviário desde a base francesa são despesas distintas; operações sazonais de 2027 devem ser verificadas com a data exata. Não chamar viagem aos Alpes de bate-volta simples sem evidência.
Esses exemplos são **checks de integridade**; a pesquisa final deve confirmar cada fonte e data.

## Arquitetura e testes
- Código de domínio preferencialmente em `attractions_model.py`, `base_routes.py`, `outing_costs.py` ou equivalentes, sem tornar `app.py` ainda maior. Componentes visuais e estilos reutilizáveis em módulos/arquivos separados.
- Validar schemas, IDs/aliases, URLs, geolocalização, preços não negativos, status de evidência, unidade, tempo, moedas, ida e volta e exclusão de duplicações.
- Testar mudança de base: mesmas atrações, mas deslocamentos/custos reavaliados. Testar campos desconhecidos, ingresso grátis parcial, viagem exigindo pernoite, despesas CHF/EUR, desconto Fluo, orçamento sem dupla contagem, agendas em datas incompatíveis.
- Executar `python -m unittest discover -s tests -v`, compilação do projeto e smoke test das seis páginas com `streamlit.testing.v1.AppTest`.
- Publicar commits no repo GitHub, sem exigir push do Mac, aguardar GitHub Actions e documentar resultado. Verificação visual em browser do Streamlit Cloud deve ser relatada separadamente; CI não equivale a teste visual.
- Não inserir credenciais, dados pessoais, segredos nem fotos não autorizadas/licenças não verificadas no repositório.

## Critérios de aceite do primeiro release
1. Ao mudar de **Mulhouse** para **Strasbourg**, as durações/tarifas de Colmar mudam com fonte identificada.
2. Ao mudar para **Metz** ou **Nancy**, o roteiro lista atrações locais e destinos próximos sem inventar facilidade de acesso a Alpes/Alsácia.
3. Cada cidade-base tem pelo menos cinco atrações verificadas quando possível; três para destinos de excursão prioritários, com status explícito de lacunas.
4. Pelo menos quatro exemplos de rotas oficiais comparáveis e testados, matrizes incompletas sinalizadas sem preencher zero como dado.
5. Usuário consegue abrir um destino e ver o que fará, tempo de visita, custo de entrada, deslocamento ida/volta e fontes.
6. Seleções de atrações entram no calendário sem conflitos nem dupla contagem financeira.
7. Todos os dados mantêm data, moeda, proveniência e confiança; nenhuma escolha muda D-004 sem aprovação explícita.
8. Sem inventar rotas, preços, abertura 2027, disponibilidade ou fotos.
9. Visual consistente e legível nas seis páginas, com testes aprovados.

## Sequência de implementação sugerida
Fase A: pesquisa curada e auditoria de fontes por cidade/atração.
Fase B: esquemas e matriz de rotas origem–destino + testes.
Fase C: novo seletor "Explorar atrações", cards, detalhes e mapa.
Fase D: listas Quero visitar/Opcional/Descartar, pacotes e calendário.
Fase E: integração ao orçamento, avaliação de viabilidade e testes de regressão.
Fase F: documentação, CI, revisão do deploy e relatório de lacunas.

A entrega deve separar claramente **implementado**, **testado**, **pesquisado mas incompleto** e **dependente de cotação de 2027**.
