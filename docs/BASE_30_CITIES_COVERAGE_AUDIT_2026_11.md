# Nossa Europa 2027 — Auditoria do comparador de 30 cidades-base

**Rodada:** 15/11/2026 · **PR:** #38 (rascunho) · **Sem alteração no plano oficial**  
**Objetivo:** distinguir progresso documental, comparabilidade e adequação, sem forçar uma cidade vencedora.

## A. Diagnóstico reproduzível

- Código anterior em `base_weight_coverage_ui.py`: `normalized_score({}, profile_id)` era chamado para **cada** cidade. A cobertura apresentada era sempre **0%**, independentemente de anúncios ou rotas catalogados. A nota final corretamente permanecia sem cálculo, mas o 0% dava a entender que não havia pesquisa.
- O erro **não** está no método `normalized_score`: ele aceita exclusivamente notas normalizadas e mantém pesos faltantes (não redistribui). O problema era usar uma chamada vazia também como indicador de pesquisa documental.
- O quadro anterior exibia anúncios e rotas, mas não explicava quais atributos faltavam ou a diferença entre tarifa de ida e custo de viagem completa.
- O dataset do GitHub alimenta o comparador; as pesquisas do Drive não passam automaticamente para o aplicativo.

## B. Fontes auditadas e hierarquia

| Origem | Escopo | Uso correto | Limites |
|---|---|---|---|
| `data/base_city_research_expanded_2026_11.json` | 30 cidades, 12 finalistas, anúncios de 2026 | Existência de amostras, preços individuais históricos, pendências | Em geral links de catálogos e não anúncios individualizados; não são cotações de 60 noites |
| `data/five_base_comparison_evidence_2026_11.json` | Cinco bases, cesta fixa de 15 destinos, 23 referências de horário | Comparar **cobertura da pesquisa** ferroviária na mesma cesta; alguns anúncios com URL individual | Tempos mínimos de ida, não retorno nem porta a porta; 2027 não validado |
| `data/exploration_bases_2027.json` | 8 cidades-base e 27 registros de rotas | Reutilizar tempos/valores históricos em pares ainda sem registro na matriz principal | Referências de operador e tarifas “desde”; não custos totais |
| `data/base_destination_routes_2027.json` | 4 bases antigas, 44 pares (muitos explicitamente não pesquisados) | Somente linhas com tempo e fonte documentados | Uma linha `route_to_research` não prova tempo ou inviabilidade |
| `data/base_city_rail_evidence_expanded_2026_11.json` | 6 amostras iniciais, ampliadas para 11 | Horários efetivamente publicados para 16/11/2026 | Uma segunda-feira, não calendário de 2027 nem retorno |
| `data/city_research_round2_2026.json` | Mulhouse, Strasbourg, Metz, Nancy | Restaurante de referência, coworking e restrições de expediente | Numbeo colaborativo; internet e acesso noturno não comprovados |
| Drive `Europa_2027_Base_COMPLETA.md` v1.3 | Pesquisa acumulada e ranking editorial original | Contexto, decisões, hipóteses, histórico de valores | Ranking de 0–5 com **outros pesos e critérios**: não transportar as notas |
| Drive `02_REGISTRO_DE_PESQUISAS` | Política de fontes, unidades e revisões | Regras de qualidade e separação de hipóteses | Não alimenta automaticamente os JSONs |
| Drive `01_ESTADO_ATUAL` | Decisões oficiais | Referência normativa da viagem, especialmente D-004 pendente | **Não alterado** nesta pesquisa |

### Divergências preservadas, não reconciliadas por média

O Markdown histórico registra exemplos de Mulhouse em **€710/€750 por mês** e Strasbourg em **€950**. A triagem JSON posterior contém outras observações de anúncios (por exemplo, Mulhouse **€980–€1.360** e Strasbourg **€850–€1.100**). São amostras de fontes, épocas e elegibilidade possivelmente distintas. **Não** combinei esses preços numa média “de mercado” nem substituí os valores históricos do Drive.

A documentação anterior também descreve cinco bases prioritárias; o catálogo do produto possui **12 finalistas**, que abrangem essas cinco, e outras 18 cidades mantidas no inventário de 30.

## C. Matriz das 12 finalistas (estado documental inicial + novas rotas)

**Amostras:** contagem da triagem JSON principal, não quantidade de apartamentos disponíveis. **Tempos/15:** quantos dos mesmos 15 destinos turísticos possuem **algum** tempo estação–estação de ida documentado. **Tarifas/15:** referências de preço inicial por pessoa e **somente ida**. Nenhuma linha implica retorno viável ou custo final de duas pessoas.

| Cidade | Anúncios históricos (triagem) | Tempos / 15 | Tarifas de ida / 15 | Cotidiano da pesquisa round 2 | Nota de adequação |
|---|---:|---:|---:|---|---|
| Mulhouse | 3 | 4 | 2 | Parcial | Indisponível |
| Strasbourg | 3 | 7 | 3 | Parcial | Indisponível |
| Metz | 3 | 3 | 1 | Parcial | Indisponível |
| Nancy | 3 | **2** | 1 | Parcial | Indisponível |
| Lille | 2 | 6 | 3 | Não há cesta equivalente | Indisponível |
| Dijon | 3 | 0 | 0 | Não há cesta equivalente | Indisponível |
| Freiburg im Breisgau | 3 | 0 | 0 | Não há cesta equivalente | Indisponível |
| Offenburg | 3 | 5 | 5 | Não há cesta equivalente | Indisponível |
| Karlsruhe | 3 | 1 | 0 | Não há cesta equivalente | Indisponível |
| Trier | 3 | 1 | 0 | Não há cesta equivalente | Indisponível |
| Aachen | 3 | 1 | 0 | Não há cesta equivalente | Indisponível |
| Liège | 3 | 0 | 0 | Não há cesta equivalente | Indisponível |

**Esclarecimento:** um 0/15 significa **sem tempo incorporado à cesta comum**, não que a cidade não tenha trem, atrações ou conexão. Por exemplo, Freiburg, Karlsruhe e Offenburg estão no corredor do Alto Reno; Dijon–Beaune é uma conexão publicada, mas Beaune **não** está entre os 15 destinos comuns e, portanto, não aumenta artificialmente a cobertura comparável.

A pesquisa detalhada das cinco bases tem três anúncios para Lille, enquanto a triagem JSON mais ampla tem dois. Mantemos essas amostras em seus respectivos contextos e evitamos somá-las como se fossem cinco ofertas distintas e elegíveis.

## D. Novas verificações documentadas

**Transporte — SNCF:**
- [Nancy → Luxembourg](https://www.sncf-connect.com/en-en/train/timetables/nancy/luxembourg): horário publicado de segunda-feira 16/11/2026; melhor **91 min**, TER direto típico de aproximadamente **94 min**, média divulgada **106 min**. **Incluído** na cesta comum da cidade Nancy.
- [Dijon → Beaune](https://www.sncf-connect.com/en-en/train/timetables/dijon/beaune): melhor **18 min**, referência TER de **21 min**, média divulgada **23 min**. **Não** é um dos 15 destinos comuns; permanece evidência contextual.
- [Strasbourg → Mulhouse](https://www.sncf-connect.com/train/horaires/strasbourg/mulhouse): melhor **49 min** de TGV, TER em torno de **53 min**, média **55 min**. Fora da cesta comum; não é tarifa/retorno de passeio.
- [Lille → Bruxelas](https://www.sncf-connect.com/en-en/train/timetables/lille/brussels): referência previamente catalogada, sem substituir a passagem “desde” por uma tarifa média.

- [Karlsruhe → Strasbourg](https://www.sncf-connect.com/en-en/train/timetables/karlsruhe/strasbourg): referência de segunda 16/11/2026, melhor trem direto **41 min**, média divulgada **70 min**, com ligação regional via Offenburg mais lenta. Dentro da cesta comum, porém sem retorno/2027.
- [Aachen → Köln](https://www.sncf-connect.com/en-en/train/route/aachen/cologne): referência de 16/11/2026, melhor percurso divulgado **38 min**, média **43 min**, envolvendo trens e estações distintas; dentro da cesta comum, sem custo do casal nem retorno de passeio.

**Rede e condições de moradia:**
- [TGO Rheintalbahn](https://www.ortenaulinie.de/startseite/fahrplan/rheintalbahn.html): documenta a rede de Karlsruhe, Offenburg, Freiburg e Basel; não constitui matriz de 15 tempos.
- [CFL horários](https://www.cfl.lu/en-gb/timetable/sheets): documenta a ligação Luxembourg–Wasserbillig–Trier; não comprova o retorno de um passeio.
- [Service-Public — bail mobilité](https://www.service-public.gouv.fr/particuliers/vosdroits/F34759): modalidade de aluguel mobiliado de 1–10 meses em hipóteses qualificadas; elegibilidade do casal não verificada.
- [Wunderflats — mínimo geral](https://wunderflats.com/en/help/post/75000062964): plataforma informa mínimo usual de um mês, sujeito a condições locais/individuais.
- [HousingAnywhere Offenburg](https://housinganywhere.com/s/Offenburg--Germany/furnished-apartments): a lista inclui imóveis de **outras cidades**, inclusive Strasbourg; não contar todos como moradia em Offenburg. Sem cotação de 56–60 noites com internet e taxas verificadas.
- [DB Freiburg → Basel](https://www.bahn.de/reisen/view/verbindung/freiburg/basel.shtml): exemplo de trem rápido **36 min** e regional **62 min** em **23/11/2026**, data de amostra diferente; não integrado à cobertura de 15 destinos do dia 16.
- [SNCB Liège–Bruxelles](https://www.belgiantrain.be/fr/travel-info/origin-destination/brussels-liege): média informada de **~64 min**, mas não a mesma medida de tempo mais rápido; manter como contexto até amostra padronizada.
- [SNCB Liège-Guillemins](https://www.belgiantrain.be/en/station-information/liege/liege-guillemins): estação com tram/ônibus e Wi-Fi; **não** equivale à internet do apartamento nem ao acesso final de cada passeio.
- [SNCB Aachen internacional](https://www.belgiantrain.be/en/products/crossborder/aachen): conexão regional transfronteiriça horária com Liège, mas Liège não integra a cesta de 15, então não há pontuação adicional.

Essas verificações são **referências contextuais ou históricas** e ficam registradas no dataset canônico existente, sem gerar cotação fictícia nem nova pontuação.

## E. Método de cobertura e pontuação

### 1. Cobertura documental (progresso de pesquisa)

Cada critério possui uma lista **fixa, igual para todas as cidades**, de requisitos auditáveis. A cobertura por requisito é **0** (ausente), **fração observada** (por exemplo, 7/15 tempos da cesta comum), ou **1** (completo). Média simples dentro do critério. O percentual documental ponderado é a soma das seis coberturas vezes seus pesos do perfil Geral, Economia ou Explorador.

Exemplos: uma cidade com 3 anúncios de catálogo recebe registro de amostra histórica, mas **não** recebe automaticamente os requisitos “dois adultos”, “60 noites”, “internet” e “taxas”. Um trecho ferroviário documentado representa 1/15 da cesta de tempos, **não** toda a categoria de trens. Frequência sem retorno não autoriza bate-volta.

### 2. Cobertura apta à pontuação

Critérios requerem **indicadores de qualidade calibrados na mesma escala 0–100**, não apenas fontes. O comparador separa essa cobertura da documental. Requisitos de moradia temporária são distintos dos anúncios de aluguel convencional. A matriz de tempos de ida também não basta para inferir acessibilidade completa.

### 3. Nota de adequação

Somente quando os **seis critérios** estiverem comparáveis e completos a soma ponderada é divulgada como nota de cidade. Até lá, **nota final = indisponível**, e ausências permanecem **desconhecidas**, nunca zero ou “cidade pior”.

Os pesos foram mantidos:
- Geral: 30/25/20/10/10/5.
- Economia: 40/20/15/15/7/3.
- Explorador: 20/30/25/8/7/10.

**Evitar dupla contagem:** “Trens” mede horários, frequências, transferências e retorno da cesta fixa; “Passeios” exige chegar efetivamente à atração e classificar necessidade de pernoite; “Países” mede diversidade internacional **com retorno comprovado**, não apenas quantidade de linhas. Esses indicadores ainda não estão elegíveis para nota final.

## F. Melhoria da interface (antes → depois)

| Antes | Depois no PR |
|---|---|
| 0% mostrado para todas as cidades sem contextualização | Percentual de **progresso documental** explicado e diferenciado da pontuação |
| Tabela de anúncios/rotas desconectada dos seis critérios | Matriz compacta com Moradia, Trens, Passeios, Custos, Vida cotidiana, documentação e situação |
| Sem explicação por cidade | Requisitos preenchidos/parciais/pendentes, preços históricos, fontes e limitações |
| Dificuldade de comparar finalistas | Comparador lado a lado para 2–3 das 12 cidades |
| Um link ou preço de ida poderia parecer pesquisa completa | Regra explícita de 15 destinos, sem tarifa de volta inferida |
| Cobertura de pontuação parecia igual ao avanço de pesquisa | Métricas independentes; nota final não inventada |

O quadro principal mostra as 12 finalistas por padrão e oferece as 30 sob demanda; não impõe 30 linhas num scroll inicial.

## G. Shortlist qualitativa, não ranking

**Candidatas com melhor convergência documental para aprofundar primeiro:**
- **Strasbourg:** 7/15 destinos com tempos históricos, amostra de moradia e alguma pesquisa cotidiana; corredor alemão/alsaciano relevante. Ainda sem preços equivalentes de 60 noites, custos de passeios completos e confirmação do retorno.
- **Mulhouse:** 4/15 tempos, incluindo Basel e Colmar, com amostras históricas de aluguel e pesquisas do cotidiano. A vantagem de custo não está provada; exemplos observados não são mercado homogêneo.
- **Lille:** 6/15 tempos, com ligações para Bélgica, Países Baixos e Paris e amostras de aluguel; falta estudo de custos cotidianos, condições de alojamento e tarifas normais ida/volta.
- **Offenburg:** 5/15 tempos e forte conexão documental com Strasbourg/Alto Reno; ofertas temporárias históricas variam muito e catálogos abrangem municípios vizinhos, aumentando o risco de concluir preço errado.
- **Metz:** conexão de referência com Luxembourg e 3/15 da cesta, além de pesquisa cotidiana para casal; ainda falta cobertura comparável de passeios e tarifas regulares.

**Investigações especialmente importantes, sem exclusão:** Nancy (2/15 após nova fonte de Luxembourg), Trier (Luxembourg, 1/15), Freiburg (corredor ferroviário sem a matriz comum), **Karlsruhe (1/15)**, Dijon (Beaune fora da cesta), **Aachen (1/15)** e Liège (eixo ferroviário com fonte da SNCB mas sem dado padronizado na cesta). **Sem pesquisa na matriz não significa pior cidade.**

Nenhuma cidade-base foi aprovada; a decisão D-004 do Drive continua aberta.

## H. Pendências de maior valor

1. Cotar ao menos três apartamentos individuais completos para dois adultos por aproximadamente 60 noites, incluindo internet, caução, taxas e acesso à estação — **mesma janela para as 12 finalistas**.
2. Completar tempos de ida **e volta** em uma mesma cesta de 15 destinos, para fim de semana e dia útil representativos, incluindo conexões e última milha.
3. Obter tarifa normal ida/volta do casal e ingresso/transporte local quando aplicáveis, sem confundir “desde” com média ou benefício de tarifa especial.
4. Construir cesta urbana homogênea: supermercado, restaurantes, transporte urbano, academia, segurança, internet e horários efetivos de coworking.
5. Validar condições de aluguel curto, direito ao trabalho remoto, jornada no fuso europeu e regras locais.
6. Antes de decidir, conectar a diferença de aluguel **realmente elegível** à economia ou acréscimo de **viagens realmente escolhidas**, não a trajetos hipotéticos incomparáveis.

## I. Validação e segurança

- Testes próprios: `tests/test_base_coverage_model.py`; executam invariantes de 30/12 cidades, pesos fixos, pesquisa parcial, ausência de tarifas fictícias, status de imóvel, UX Streamlit e independência do `TripPlan`.
- Suíte completa via GitHub Actions: verificar resultado mais recente no PR #38.
- Inspeção visual de produção: não confirmada; ambiente Streamlit Cloud não disponível pelo navegador da ferramenta atual.
- Sem atualização de Drive, orçamento, autenticação, dados de planos ou propostas italianas. Nenhum merge/deploy sem aprovação.

**Critério de sucesso:** entender **o que sabemos, como sabemos, o que falta e quais comparações já são defensáveis**; não fabricar uma tabela de notas completas.
