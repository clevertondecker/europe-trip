# Nossa Europa 2027 — DQ 3.0 / Pacote 3 (17/11/2026)

## Resultado e critério de evidência

Este PR evolui o dataset complementar do PR #86, sem alterar `TripPlan`, catálogo de atrações, orçamento, CSS, modelos ferroviários, dados pessoais ou a UX. A pesquisa foi conduzida nos seis destinos P0.

**Não declarar o Pacote 3 integralmente concluído:** os motores pedestres não foram executados; não existem pontos públicos de entrada/saída comprovados suficientes para roteamento responsável. Distâncias dos seis trechos estação→atração continuam desconhecidas. Um circuito oficial de 7 km e um tempo oficial de 20 minutos são fatos **de escopos diferentes** e não podem ser combinados.

### Matriz antes e depois

| Indicador | Antes (main/PR #86) | Depois (branch P3) |
|---|---:|---:|
| Atrações P0 inventariadas | 30/30 | 30/30 |
| Atrações P0 com coordenadas representativas e fonte | 13/30 | **26/30** |
| Atrações com entrada pedestre verificada | 0 | 0 |
| Estações com posição geral documentada | 6 | 6 |
| Estações com saída pública confirmada | 0 | 0 |
| Conflitos de **posição representativa** de estação sem reconciliação | 1 | **0** (Brugge reconciliada, não saída) |
| Seis pares estação→atração pesquisados | 6 | 6, **todos com distância null** |
| Pares estação→atração com duração oficial | 1 | 1 (Brugge→Markt: 20 min) |
| Pares com duração e distância calculadas por motor pedestre | 0 | 0 |
| Circuitos completos com distância total oficial | 0 | **1** (Rotterdam: 7 km) |
| Sequências de atrações investigadas/documentadas | 6 | 6 |
| Retornos de trem 2027 verificados | 0 | 0 |

### As 17 lacunas pesquisadas

| ID | Resultado | Precisão / fonte |
|---|---|---|
| `strasbourg_grande` | Coordenada adquirida | Ilha Grande Île, centroide de área: [Wikidata Q1895943](https://www.wikidata.org/wiki/Q1895943) |
| `strasbourg_europe` | Sem ponto único inequívoco | Distrito cobre várias instituições; [referência de bairro](https://www.citadineseurometropolestrasbourg.com/en/places/european-quarter/) |
| `colmar_tanners` | Sem centroide confiável | [Q3413256](https://www.wikidata.org/wiki/Q3413256) é ponto de construções na rue des Tanneurs, **não** centroide comprovado do bairro |
| `colmar_stmartin` | Coordenada adquirida | Igreja, ponto representativo: [Wikidata Q1581390](https://www.wikidata.org/wiki/Q1581390) |
| `colmar_heads` | Coordenada adquirida | Maison des Têtes, ponto de edifício: [Wikidata Q3279905](https://www.wikidata.org/wiki/Q3279905) |
| `basel_mittlere` | Coordenada adquirida | Ponto representativo da ponte: [Middle Bridge](https://en.wikipedia.org/wiki/Middle_Bridge%2C_Basel) |
| `basel_oldtown` | Coordenada adquirida | Centroide **parcial** de Altstadt Grossbasel: [Wikidata Q445565](https://www.wikidata.org/wiki/Q445565); não representa todas as partes do centro histórico |
| `brussels_royal_galleries` | Coordenada adquirida | Ponto das galerias: [Wikidata Q1491935](https://www.wikidata.org/wiki/Q1491935) |
| `brussels_mont_arts` | Coordenada adquirida | Centroide da praça: [Wikidata Q1865794](https://www.wikidata.org/wiki/Q1865794) |
| `brussels_eu_quarter` | Sem ponto único verificado | [Visit Brussels — passeio pelo bairro](https://www.visit.brussels/en/visitors/plan-your-trip/neighbourhood-walk--the-european-quarter) documenta a área, mas não uma entrada comum |
| `bruges_belfry` | Coordenada adquirida | Torre: [Belfry of Bruges](https://en.wikipedia.org/wiki/Belfry_of_Bruges) |
| `bruges_rosary_quay` | Coordenada adquirida | Ponto panorâmico [OSM node 4170360237](https://mapcarta.com/N4170360237) |
| `bruges_minnewater` | Coordenada adquirida | Centroide do parque [OSM way 3516686](https://mapcarta.com/W3516686) |
| `bruges_canals` | Sem ponto único verificado | É uma atividade linear pelos canais; [turismo oficial](https://www.visitbruges.be/en/things-to-do/sights) |
| `rotterdam_erasmus_bridge` | Coordenada adquirida | Ponto representativo da ponte: [Erasmusbrug](https://en.wikipedia.org/wiki/Erasmusbrug), não cabeceira |
| `rotterdam_old_harbour` | Coordenada adquirida | Centroide do porto: [Wikidata Q2398977](https://www.wikidata.org/wiki/Q2398977) |
| `rotterdam_centraal` | Coordenada adquirida | A atração corresponde à arquitetura da estação; reutilizada a posição geral da estação do [Wikidata Q801388](https://www.wikidata.org/wiki/Q801388), **não** entrada pública |

Cada ponto tem lat/lon, URL, precisão e data de consulta no JSON. **Nenhuma dessas novas coordenadas foi afirmada como entrada.**

### Brugge Station: conflito reconciliado com escopo limitado

As fontes [Wikidata Q800580](https://www.wikidata.org/wiki/Q800580), [OSM/Mapcarta](https://mapcarta.com/29355084) e [registro OSM independente](https://be.geoview.info/station_brugge%2C20217215117w) situam o complexo ferroviário próximo de latitude **51,1974 N** e longitude **3,2174 E**, consistente com o ponto representativo anterior (51,1976219 / 3,2179192). A coordenada alternativa registrada anteriormente, 51°11′2N 3°13′30E, desloca-se significativamente para sul e não foi confirmada como posição da estação. `coordinate_conflict_unresolved` passou a `false` **somente para a posição geral**, com histórico, justificativa e links preservados em `coordinate_reconciliation`. `pedestrian_routing_ready` continua `false`, `pedestrian_access_points` permanece vazio. Nada foi convertido em entrada fictícia.

### Acesso estação → atração: seis pares P0

| Par | Distância em metros | Tempo pedestre | Evidência |
|---|---:|---:|---|
| Strasbourg Gare → Catedral | desconhecida | desconhecido | [Turismo Strasbourg](https://www.visitstrasbourg.fr/organiser/venir-et-se-deplacer-a-strasbourg/venir-a-strasbourg/en-train/) informa apenas que a estação fica a poucos minutos do **centro**, não uma rota até a catedral |
| Colmar Gare → Petite Venise | desconhecida | desconhecido | [Turismo Colmar](https://www.tourisme-colmar.com/en/to-sleep/hotels/holidays-residences/F235014532_residence-pierre-et-vacances-la-petite-venise-colmar-en) cita hospedagem próxima, mas não descreve exatamente este par |
| Basel SBB → Basler Münster | desconhecida | desconhecido | [Basel Tourism](https://www.basel.com/en/attractions/sbb-railway-station-41a9908ee1) confirma estação, não trecho calculado |
| Bruxelles-Central → Grand-Place | desconhecida | desconhecido | [Visit Brussels](https://www.visit.brussels/en/professionals/news-articles-insights/venues-station-event/brussel-centraal) possui tempos até hospedagens, não este par específico |
| Brugge Station → Markt | desconhecida | **20 min, publicados** | [Visit Bruges](https://www.visitbruges.be/en/plan-your-visit/mobility); fonte não publica distância |
| Rotterdam Centraal → Markthal | desconhecida | desconhecido | [Rotterdam Tourism](https://www.rotterdam.info/en/visit/guide/walking-in-rotterdam) publica **circuito completo**, não trecho individual |

**Não somar** tempos de hotel→atração e estação→hotel para inventar trajetos. Não usar Haversine como caminhada ou o centro geográfico da estação como saída pública.

### Sequências por cidade, efetivamente investigadas

- **Strasbourg:** Catedral → Petite France → Ponts Couverts (as atrações aparecem em roteiros turísticos, sem distâncias de trechos publicadas).
- **Colmar:** Maison Pfister → Quartier des Tanneurs → Petite Venise (candidata, sem duração entre pares).
- **Basel:** Münster → centro histórico → Mittlere Brücke (candidata, sem rota pedestre publicada entre os IDs).
- **Bruxelas:** Grand-Place → Galeries Royales Saint-Hubert → Mont des Arts (candidata, sem tempo de cada trecho).
- **Bruges:** Markt → Belfort → Rozenhoedkaai (o [turismo municipal](https://www.visitbruges.be/en/things-to-do/sights) descreve esses locais; sem metragem oficial de cada trecho).
- **Rotterdam:** Markthal → Cube Houses → Oude Haven ([roteiro municipal](https://www.rotterdam.info/en/visit/good-to-know/city-walking-tour) cita destaques; nenhum segmento individual tem distância publicada).

O **circuito circular oficial de Rotterdam tem 7 km** e começa/termina na Rotterdam Centraal, segundo o [turismo oficial](https://www.rotterdam.info/en/visit/good-to-know/city-walking-tour). Esse número é armazenado em `published_walking_itineraries` como `distance_m=7000`, `route_scope=entire_loop_not_individual_segments`, `duration_min=null`. **Não é a distância Centraal→Markthal nem Markthal→Cube Houses.**

### Viabilidade técnica de roteamento, termos e bloqueios

- [openrouteservice](https://api.openrouteservice.org/): serviço hospedado requer chave/API e respeitar [restrições do servidor](https://giscience.github.io/openrouteservice/hosted-api-restrictions). Não havia credencial do serviço disponibilizada para a execução.
- [GraphHopper](https://www.graphhopper.com/faq/create-an-api-key/): requer chave de usuário; planos e atribuição dependem de [termos](https://www.graphhopper.com/terms/).
- [Valhalla FOSSGIS](https://valhalla.github.io/valhalla/): servidor público demonstrativo, política de uso justo e limites; não usar para coleta indiscriminada ou produção automaticamente.

Mais importante: **nenhuma das seis estações possui uma saída pública com coordenada comprovada no dataset**, nem as atrações prioritárias possuem entrada validada. O contrato do PR #86 exige pontos de acesso reais e fonte para ambos os lados antes de declarar `pedestrian_routed`. Portanto **não foram executadas chamadas a motores** e **nenhuma distância/tempo de segmento foi calculada**.

### Próximos passos para alcançar o objetivo integral

1. Verificar acessos públicos por IDs de nós/entradas do OSM e dados oficiais de cada uma das seis estações, incluindo as saídas realmente utilizadas, sem tratar posição de estação como saída.
2. Validar entradas nas atrações prioritárias e só então executar motor autorizado com perfil `pedestrian`, armazenando request, engine/version, resposta e referência à geometria.
3. Completar a geografia das quatro atrações que são áreas ou atividades lineares com representação em geometria (polígono/linha), não com um ponto fictício.
4. Expandir segmentos entre atrações e última atração→estação a partir das sequências existentes, verificando ida e volta quando necessário.
5. Exibir no aplicativo somente depois de testar a renderização e a consistência com os passeios reais.

**Estado do PR:** pesquisa geográfica útil e contrato de dados mais rico; entrega pedestre integral **ainda pendente**. Sem merge ou deploy.
