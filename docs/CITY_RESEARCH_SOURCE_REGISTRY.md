# Catálogo permanente de fontes — pesquisas de cidades-base

**Projeto:** Nossa Europa 2027 · **Revisão inicial:** 2026-11-16 · **Status:** catálogo de descoberta e reutilização, não dataset de preços/rotas já verificados.

## Finalidade e escopo

Usar este documento **antes de toda pesquisa sobre cidades novas ou cadastradas**, priorizando as 12 finalistas atuais entre as 30 cidades de França, Alemanha e Bélgica. As fontes abaixo servem para localizar **evidências verificáveis**, não para copiar automaticamente notas, índices turísticos ou preços para 2027.

O cenário é um casal, sem carro, trabalhando remotamente, passando aproximadamente 56–60 noites na Europa após 04/09/2027. Cada pesquisa precisa preservar `city_id` canônico, país, perímetro municipal, período de observação e unidade.

## Hierarquia editorial

- **A · Institucional/primária:** autoridade estatística, serviço meteorológico, operador de transporte, entidade municipal. Priorizar para fatos quantificáveis; ainda verificar granularidade, ano e limitações.
- **B · Observação de mercado/dados abertos secundários:** anúncio individual, índices de preços, dataset derivado de reanálise. Usar com cautela; amostra não representa toda a cidade.
- **C · Contexto editorial/colaborativo:** perfis turísticos, relatos, índices percebidos. Nunca converter automaticamente em score oficial ou regra para reserva.

**Direitos de uso:** fonte confiável não significa licença de cópia livre. Confirmar e registrar licença, atribuição, limites de API, robôs/ToS e possibilidade de redistribuir dados/ícones/fotos antes da ingestão. Não executar scraping de sites que o proíbem. Nenhuma fonte externa deve entrar na previsão oficial sem revisão do domínio financeiro.

## Fontes reutilizáveis, com URLs e papéis

| Fonte (URL) | Área/país | Confiança | Uso pretendido | Coleta e ressalva |
|---|---|---|---|---|
| [INSEE — Base du comparateur de territoires](https://www.insee.fr/fr/statistiques/2521169) | França | A | População, moradia, emprego, receitas e perfil municipal; CSV/Parquet de 2026 | Dados institucionais, conferir o indicador e a licença na versão publicada |
| [Destatis — GV-ISys](https://www.destatis.de/EN/Themes/Countries-Regions/Regional-Statistics/OnlineListMunicipalities/_inhalt.html) | Alemanha | A | Identificadores municipais AGS/ARS, população, área e classificação territorial | Dados administrativos, não custo de vida |
| [Statbel — Open Data](https://statbel.fgov.be/en/open-data) | Bélgica | A | Indicadores municipais de população, habitação e setores estatísticos | Ver tabela, data/município e licença do arquivo específico |
| [Eurostat — City Statistics / Urban Audit](https://ec.europa.eu/eurostat/cache/metadata/EN/urb_esms.htm) | Europa | A | Indicadores comparáveis de demografia, transporte, cultura e ambiente | Cobertura limitada a certas cidades e métricas; não imputar ausência como zero |
| [Eurostat — metodologia de cidades/FUA](https://ec.europa.eu/eurostat/web/cities/methodology) | Europa | A | Compatibilização de perímetros e comparabilidade municipal/aglomeração | Nunca misturar cidade administrativa e região funcional sem aviso |
| [SNCF Connect — Timetables](https://www.sncf-connect.com/en-en/train-ticket/timetables) | França/internacional | A / operador | Tempos, baldeações, datas e referência de tarifas ferroviárias | Registrar origem-destino exatos, ida/volta, data; histórico não vale para 2027 |
| [Deutsche Bahn — Travel information](https://int.bahn.de/en/booking-information/travel-information) | Alemanha/internacional | A / operador | Rotas por tipo de trem, mudanças de estação, conexões | Horários e preço variam por data; evitar usar só opção mais rápida |
| [SNCB/NMBS — Rail travel](https://www.belgiantrain.be/en/travel-info/current/current-departure-times) | Bélgica | A / operador | Conexões, frequências e horários locais | Dados de partida em tempo real não demonstram retorno futuro |
| [Météo-France — fiches climatologiques](https://www.data.gouv.fr/datasets/fiches-climatologiques) | França | A | Normais mensais históricas por estação, temperatura e precipitação | Distinguir normal de estação e previsão para 2027 |
| [DWD — médias climáticas 1991–2020](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/multi_annual/mean_91-20/) | Alemanha | A | Clima histórico por estação (temperatura, chuva, sol) | Conferir estação, distância e representatividade |
| [Open-Meteo — Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | Europa | B · reanálise | Cobertura padronizada para clima histórico onde falta estação | Reanálise é modelo, não observação pontual; respeitar termos e atribuição CC BY |
| [Weatheo / data.gouv.fr — normais 1991–2020 por comuna](https://www.data.gouv.fr/datasets/normales-climatiques-mensuelles-1991-2020-par-commune-france) | França | B · dataset derivado | Temperatura/chuva por município em CSV/Parquet | **Não é produto oficial de Météo-France**; é reanálise ERA5-Land publicada por terceiro com CC BY e atribuições |
| [SSMSI — Base communale](https://statistiques.interieur.gouv.fr/ssmsi/sources-et-methodes-statistiques/sources-de-donnees/base-communale) | França | A | Fatos policiais registrados por categoria e período | Registro policial não mede risco pessoal diretamente; amostragem/limiares importam |
| [Deutschlandatlas — Straftaten](https://deutschlandatlas.bund.de/karten/unsere-sicherheit/straftaten) | Alemanha | A | Indicadores regionais de delitos registrados | Geografia pode ser distrito, não município; não montar nota subjetiva de segurança |
| [OpenStreetMap — copyright](https://www.openstreetmap.org/copyright) | Europa | B · comunidade | Estações, supermercados, parques, serviços e caminhada | ODbL exige atribuição e pode impor compartilha-igual em bases derivadas; usar API conforme política |
| [Wikimedia Commons — reuse](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/pt) | Europa | B · mídia | Fotos de cidades com autoria/licença por arquivo | Confirmar cada licença, autor, crédito e direito de reprodução; não usar foto de cidade errada |
| [Tripbase — metodologia](https://www.tripbase.com/about/) | Europa | C | Taxonomia editorial para fichas e inspiração visual | **Não** importar notas de 0–10 como métricas verificadas; validar fatos decisivos na fonte primária |
| [Tripbase — comparação fornecida](https://www.tripbase.com/compare/mulhouse-france-vs-strasbourg-france-vs-freiburg-germany/) | Mulhouse/Strasbourg/Freiburg | C | Referência de experiência comparativa | Confirmar abertura e fonte dos números antes de registrar; licença/republicação não presumida |
| [Numbeo — termos](https://www.numbeo.com/common/terms_of_use.jsp) | Europa, cobertura variável | C · colaborativo | Referência complementar de despesas urbanas | **Scraping/crawling automatizado proibido sem autorização escrita**; não importar em lote |
| [Expatistan — metodologia](https://www.expatistan.com/how-does-it-work) | Europa, cobertura variável | C · colaborativo | Sinal auxiliar de preços e confiabilidade da amostra | Confiança e representatividade variam; verificar termos antes de qualquer reutilização |
| [Flatio](https://www.flatio.com/) | Europa, oferta variável | B · mercado | Procurar estadias mobiliadas intermediárias, quando houver resultados locais | Preço/ocupação/56–60 noites/taxas/internet só valem com anúncio individual e datas verificadas |
| [HousingAnywhere](https://housinganywhere.com/) | Europa, oferta variável | B · mercado | Amostras de anúncios individuais mobiliados | Índice de aluguel e anúncio são produtos diferentes; não inferir disponibilidade 2027 |

## Fontes locais obrigatórias a descobrir para cada município

Registrar também a **prefeitura**, o **operador de transporte urbano**, o **operador de fibra/internet**, a **área de turismo local** e, se houver, **coworkings com preço e regras explícitos**. Não inventar nomes nem URLs locais: verificar cidade por cidade.

## Registro de uma fonte por dado observado

Para cada evidência incluída na pesquisa, preencher ao menos:
```yaml
city_id: strasbourg
country: Franca
indicator: population_total
value: null                # preencher só após leitura da fonte
unit: people
geographic_scope: commune  # município / área funcional / aglomeração
reference_period: null     # ano/mês/dia a que o valor se refere
collected_at: null         # data UTC da coleta
source_name: INSEE
source_url: https://www.insee.fr/fr/statistiques/2521169
source_type: official_statistic
method: official_download
license_or_terms: check_dataset
limitations: null
valid_for_2027: false      # histórico não confirma oferta ou preço futuro
```

O exemplo contém `null` de propósito. Não confundir metadados de fonte com evidência numérica válida.

## Como reutilizar para a 31ª cidade

1. Encontrar país e **ID canônico** existente ou gerar ID novo sem colidir; mapear código municipal INSEE/AGS/NIS quando aplicável.
2. Consultar primeiro **A**, depois **B** e por fim **C**; registrar fontes locais verificadas.
3. Adicionar evidências com URL exata, indicador, valor/unidade, geografia, ano, coleta, licença e limitações.
4. Enriquecer ficha interpretável sem publicar nota final se faltam métricas comparáveis.
5. Manter histórico: **append/versão**, sem apagar observações antigas nem sobrescrever preços passados por novos.
6. Recalcular a matriz documental no código já existente. Fatos históricos jamais são cotações confirmadas para 2027.
7. Executar testes de integridade, IDs únicos, schemas, links/atribuição e impacto no `TripPlan`.
8. Revisar este catálogo quando descobrir fonte melhor, queda de serviço, mudança de licença ou publicação nova.

**Governança:** `AGENTS_COORDINATION.md`; alterações em módulos compartilhados pelo integrador. Nenhum commit de dados particulares, chaves, sessões, reservas, planos privados ou arquivos restritos. Este catálogo deve permanecer versionado no GitHub para reutilização; não criar planilhas paralelas por cidade.


## Novas fontes municipais verificadas — rodada de 16/11/2026

Fontes de contexto público verificadas e utilizadas **apenas em descrições qualitativas**, com URL vinculada a cada observação no dataset `data/city_profiles_enriched.json`. Não representam preços nem estadias confirmadas.

| Cidade | Referência municipal / operador | Área |
|---|---|---|
| Mulhouse | [Turismo municipal — transporte público](https://www.tourisme-mulhouse.com/en/what-to-do-in-mulhouse/getting-around-mulhouse-by-public-transport/) | mobilidade e museus |
| Strasbourg | [Turismo oficial — bairros e áreas](https://www.visitstrasbourg.fr/en/discover/strasbourg-and-its-surrounding-area/) | contexto urbano |
| Metz | [SNCF Connect — Metz/Luxembourg](https://www.sncf-connect.com/en-en/train/timetables/metz/luxembourg) | ligação ferroviária histórica |
| Nancy | [Destination Nancy — turismo](https://www.destination-nancy.com/en/tourisme/) | patrimônio e parques |
| Lille | [Ville de Lille — transports](https://www.lille.fr/Vivre-a-Lille/Me-deplacer/En-transports-en-commun) | transporte municipal |
| Dijon | [Turismo Dijon Bourgogne](https://www.dijonbourgogne.com/en/tourism/) | contexto urbano |
| Freiburg | [Portal municipal de turismo](https://visit.freiburg.de/en) | turismo, ambiente universitário |
| Offenburg | [Ortenau Tourismus — Altstadt](https://www.ortenau-tourismus.de/attraktionen/offenburg-historische-innenstadt-faf825ebc9) | comércio, centro histórico |
| Karlsruhe | [ZKM — acesso por transporte público](https://zkm.de/en/directions) | transporte urbano |
| Trier | [Germany Travel — Trier](https://www.germany.travel/en/cities-culture/trier.html) | patrimônio romano |
| Aachen | [Aachen Tourist Service — Catedral](https://www.aachen-tourismus.de/en/aachen-entdecken/details/poi/aachener-dom/) | patrimônio e acesso a pé |
| Liège | [SNCB — Liège-Guillemins](https://www.belgiantrain.be/en/station-information/liege/liege-guillemins) | estação multimodal |

**Atenção:** as fontes turísticas promovem seus destinos; fatos narrativos provenientes delas não constituem uma avaliação independente de habitabilidade, segurança ou custo. Nova cidade deve ser pesquisada nas mesmas categorias, com indicadores de fontes primárias e seus períodos.


## Fontes locais acrescentadas pelos pacotes 1–3 (16/11/2026)

**Bairros — evidências institucionais** (os bairros são pontos de partida para procurar imóveis, nunca garantias de segurança, preço ou adequação):

| Município | Fonte | Escopo |
|---|---|---|
| Mulhouse | [Turismo municipal — bairros](https://www.tourisme-mulhouse.com/app/uploads/mulhouse-tourisme/2025/07/DP_2025-FR_BD.pdf) | Centre Historique, Rebberg e Nouveau Quartier |
| Strasbourg | [Turismo — quartiers](https://www.visitstrasbourg.fr/decouvrir-strasbourg/strasbourg-et-alentours/les-quartiers-de-strasbourg/) | Gare-Tribunal, Krutenau e Neudorf |
| Metz | [Prefeitura — conseils de quartier](https://metz.fr/engager-entraider/citoyennete/conseils-quartiers.php) | Gare/Nouvelle Ville, Sablon/Amphithéâtre e Centro |
| Nancy | [Prefeitura — quartiers](https://www.nancy.fr/nancy-la-ville/quartiers-et-territoires) | Centre-ville/Charles III, Poincaré/Foch, Vieille Ville |
| Lille | [Prefeitura — transportes](https://www.lille.fr/Vivre-a-Lille/Me-deplacer/En-transports-en-commun) | Bairros cobertos por serviços urbanos descritos |
| Dijon | [Prefeitura — Montchapet](https://patrimoine.dijon.fr/le-patrimoine-dijonnais-en-ligne/123-quartiers/quartier-montchapet/) | Montchapet |
| Freiburg | [Prefeitura — Stadtbezirksatlas 2025](https://www.freiburg.de/pb,%2CLde/2480165.html) | Stühlinger, Wiehre, Vauban |
| Karlsruhe | [Prefeitura — Stadtteile](https://www.karlsruhe.de/stadt-rathaus/stadtteile-ortsverwaltungen/karlsruher-stadtteile) | Innenstadt-Ost, Innenstadt-West, Nordweststadt |
| Trier | [Prefeitura — Ortsbezirke](https://www.trier.de/leben-in-trier/stadtportrait/ortsbezirke/index.html) | Mitte-Gartenfeld |
| Liège | [Police — secteurs](https://www.policeliege.be/page/stat/secteurs) | Liège-Centre/Outremeuse, Guillemins/Avroy |

**Operadores — ligações e regras tarifárias históricas**:

- [TER Mulhouse–Strasbourg](https://www.ter.sncf.com/grand-est/trajet-mulhouse-strasbourg): cerca de 53 min, até 33 idas/voltas diárias e condição Carte Fluo; não usar como horários de fim de semana de 2027.
- [TER Metz–Strasbourg](https://www.ter.sncf.com/grand-est/trajet-metz-strasbourg): 1h36, seis idas/voltas diárias publicadas e tarifa Carte Fluo; restrições de data.
- [TER linhas Grand Est](https://www.ter.sncf.com/grand-est/se-deplacer/lignes): Nancy–Metz, até 52 idas/voltas, tempo mínimo publicado de 38 min.
- [Carte Fluo](https://www.ter.sncf.com/grand-est/tarifs-cartes/cartes-reduction/carte-fluo): €30/ano com regras de 50% e benefício de acompanhante aos fins de semana/feriados em trajetos elegíveis. Não duplicar desconto automaticamente.

**Clima**: [normais francesas 1991–2020 via ERA5-Land reanalisada](https://www.data.gouv.fr/datasets/normales-climatiques-mensuelles-1991-2020-par-commune-france) são CC BY 4.0 com atribuição Copernicus obrigatória, resolução de ~9 km e não são medições de estações. Dataset identificado, **valores municipais ainda não importados** nesta rodada; não publicar médias sem ler o recurso bruto.

**Custo e coworking:** manter os registros existentes em `data/city_research_round2_2026.json`; índices de Numbeo são referências colaborativas históricas, sem scraping. Horários e condições de uso dos espaços requerem revalidação diretamente com fornecedores antes da viagem.


### Normais climáticas de estações — seis finalistas francesas (1991–2020)

Valores de temperatura média (°C) e chuva mensal (mm) extraídos das tabelas de normais 1991–2020 exibidas pelo **Meteociel com dados Météo-France**, para as estações abaixo, em 16/11/2026. **Não equivalem a normais municipais pontuais**, pois estação e centro urbano podem ter altitudes/localizações diferentes.

| Cidade-base | Estação de referência | URL |
|---|---|---|
| Mulhouse | Mulhouse | https://www.meteociel.fr/obs/clim/normales_records.php?code=68224006 |
| Strasbourg | Strasbourg-Entzheim | https://www.meteociel.fr/obs/clim/normales_records.php?code=67124001 |
| Metz | Metz-Frescaty | https://www.meteociel.fr/obs/clim/normales_records.php?code=57039001 |
| Nancy | Nancy-Essey | https://www.meteociel.fr/obs/clim/normales_records.php?code=54526001 |
| Lille | Lille-Lesquin | https://www.meteociel.fr/obs/clim/normales_records.php?code=59343001 |
| Dijon | Dijon-Longvic | https://www.meteociel.fr/obs/clim/normales_records.php?code=21473001 |

**Método de reutilização:** conferir mês/estação/período de 30 anos, atribuir Météo-France na descrição da fonte, guardar link do agregador e verificar direitos antes de reprodução em massa; não transferir dados da estação para o endereço exato de hospedagem, nem comparar condições meteorológicas de 2027.
