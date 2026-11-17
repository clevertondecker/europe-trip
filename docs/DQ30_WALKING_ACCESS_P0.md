# DQ 3.0 / Pacote 2 — Auditoria geoespacial P0 (17/11/2026)

## Escopo / limitações
Esta entrega foi construída a partir do catálogo canônico e fontes públicas rastreáveis para os seis destinos P0. O arquivo complementar não altera `data/attractions_2027.json`, `TripPlan`, os agrupamentos, a UX ou o piloto histórico DQ 3.0 P1. Não foi disponibilizado um serviço de roteamento pedestre autorizado para todos os seis destinos, portanto **nenhuma distância caminhável numérica foi inferida**. O objetivo de pesquisar/verificar individualmente todas as 30 atrações não está completamente atendido: treze têm ponto representativo confirmado; as demais aguardam geocodificação e conferência de acesso.

### Antes / depois

| Métrica | Antes | Depois | Observação |
|---|---:|---:|---|
| Atrações canônicas totais | 65 | 65 | catálogo original intacto |
| Atrações nos destinos P0 | 30 | 30 inventariadas | 6 Strasbourg, 5 Colmar, 4 Basel, 5 Bruxelles, 5 Bruges, 5 Rotterdam |
| Atrações P0 com coordenada individual | 0 | 13 | **nenhuma** representa entrada pública verificada |
| Atrações P0 com entrada identificada geograficamente | 0 | 0 | pontos representativos e centroides não são entradas |
| Atrações P0 com endereço/documentação associada | 2 (piloto P1) | 3 (datasets complementares) | Catedral e Grand-Place já existiam; Basel Münster é novo |
| Estações P0 com coordenada de estação | 0 | 6 | fonte e precisão documentadas; não são plataformas nem saídas |
| Rotas estação → atração investigadas no pacote | 0 | 6 | uma por destino, cinco ainda sem tempo |
| Trechos com tempo de caminhada informado diretamente | 0 | 1 | Brugge Station → Markt, 20 min pelo turismo municipal |
| Trechos com distância em metros documentada | 0 | 0 | sem roteador autorizado |
| Sequências candidatas de atrações | 0 | 6 | uma por destino; não equivalem a percurso calculado |
| Rotas com retorno ferroviário confirmado em 2027 | 0 | 0 | fora de escopo |

### Evidências geográficas confirmadas

| ID canônico | Latitude | Longitude | Precisão | Fonte |
|---|---:|---:|---|---|
| `strasbourg_cathedral` | 48.5818889 | 7.7511111 | ponto da atração (não porta) | [Wikidata Q745460](https://www.wikidata.org/wiki/Q745460) |
| `colmar_venise` | 48.0700000 | 7.3600000 | centroide de bairro | [Wikidata Q3377391](https://www.wikidata.org/wiki/Q3377391) |
| `basel_munster` | 47.5564000 | 7.5925000 | ponto da construção | [Vitrosearch](https://www.vitrosearch.ch/en/buildings/2713158) |
| `brussels_grand_place` | 50.8467078 | 4.3525382 | centroide da praça | [Wikidata Q21771859](https://www.wikidata.org/wiki/Q21771859) |
| `bruges_markt` | 51.2085000 | 3.2243889 | centroide da praça | [Wikidata Q1108938](https://www.wikidata.org/wiki/Q1108938) |
| `rotterdam_markthal` | 51.9201111 | 4.4869500 | ponto do edifício | [Wikidata Q3327230](https://www.wikidata.org/wiki/Q3327230) |


### Georreferências complementares verificadas

Além dos seis pontos iniciais, sete registros do Wikidata foram reconciliados diretamente com os IDs existentes: `strasbourg_petite` ([Q965606](https://www.wikidata.org/wiki/Q965606), centroide de bairro), `strasbourg_ponts` ([Q3397780](https://www.wikidata.org/wiki/Q3397780)), `strasbourg_vauban` ([Q2885001](https://www.wikidata.org/wiki/Q2885001)), `colmar_pfister` ([Q2350639](https://www.wikidata.org/wiki/Q2350639)), `basel_townhall` ([Q688984](https://www.wikidata.org/wiki/Q688984)), `brussels_atomium` ([Q180901](https://www.wikidata.org/wiki/Q180901)) e `rotterdam_cube_houses` ([Q42153772](https://www.wikidata.org/wiki/Q42153772)). A precisão permanece **ponto representativo ou centroide**, não entrada pública verificada.

### Estações documentadas

| ID | Nome | Fonte | Limitação |
|---|---|---|---|
| `strasbourg_gare` | Strasbourg Gare Centrale | [Wikidata Q801473](https://www.wikidata.org/wiki/Q801473) | posição de estação, não acesso pedestre |
| `colmar_gare` | Colmar Gare | [Wikidata Q958671](https://www.wikidata.org/wiki/Q958671) | posição de estação |
| `basel_sbb` | Basel SBB | [Basel SBB](https://en.wikipedia.org/wiki/Basel_SBB_railway_station) | posição geral arredondada, não plataforma |
| `brussels_central` | Bruxelles-Central | [Wikidata Q800588](https://www.wikidata.org/wiki/Q800588) | estação, não saída específica |
| `brugge_station` | Brugge Station | [Wikidata Q800580](https://www.wikidata.org/wiki/Q800580) | Wikidata possui coordenada alternativa conflitante; confirmar geografia para navegação |
| `rotterdam_centraal_station` | Rotterdam Centraal | [Wikidata Q801388](https://www.wikidata.org/wiki/Q801388) | posição de estação, não saída específica |

### Caminhadas e evidências de deslocamento

A fonte primária [Visit Bruges — Travelling to and in Bruges](https://www.visitbruges.be/en/plan-your-visit/mobility) indica **20 minutos a pé** de Brugge Station até Markt. O tempo não foi produzido por Haversine, nem convertido em metros ou em tempo de volta; pode variar com ritmo, acessibilidade e saída utilizada.

Outras cinco consultas estação→atração (`strasbourg_gare`→`strasbourg_cathedral`, `colmar_gare`→`colmar_venise`, `basel_sbb`→`basel_munster`, `brussels_central`→`brussels_grand_place`, `rotterdam_centraal_station`→`rotterdam_markthal`) permanecem **`duration_min=null`, `distance_m=null`**: não há percurso pedestre específico reproduzível usado neste pacote.

O [turismo de Rotterdam](https://www.rotterdam.info/en/visit/good-to-know/city-walking-tour) publica um roteiro a pé que inclui Markthal e Cube Houses, mas não informa tempo/distância entre os dois no material consultado. As demais sequências representam prioridades de coleta, não afirmações de tempo, proximidade ou ordem ótima.

### Três exemplos de leitura

```python
from dq30_walking_access_model import attraction_access

strasbourg = attraction_access("strasbourg_cathedral")
# arrival_station.id = strasbourg_gare
# station_route.duration_min = None, distance_m = None
# historical_access conserva o endereço do piloto #85

brussels = attraction_access("brussels_grand_place")
# arrival_station.id = brussels_central
# station_route.duration_min = None, distance_m = None

bruges = attraction_access("bruges_markt")
# arrival_station.id = brugge_station
# station_route.duration_min = 20 (turismo oficial)
# station_route.distance_m = None (não aferida)
```

### O que foi efetivamente produzido

- `data/dq30_walking_access_2026_11.json`: inventário completo de 30 atrações P0, seis estações, seis pares de acesso pesquisados, seis sequências candidatas e dados verificados com URL/data
- `dq30_walking_access_model.py`: adaptador de leitura, validação de IDs e proveniência, compatibilidade com histórico do PR #85
- `tests/test_dq30_walking_access.py`: testes de valores ausentes, coordenadas, fontes, duração, modais, integridade e consultas
- Não há migração e o catálogo canônico não foi alterado

### Bloqueios e trabalho não concluído

1. As 17 atrações restantes P0 precisam de geocodificação por identificadores OSM/Wikidata e confirmação individual da natureza do ponto; os 30 acessos principais e suas entradas exigem pesquisa mais ampla.
2. Um serviço autorizado (Valhalla/GraphHopper/ORS com perfil pedestrian, ou instruções oficiais específicas) é necessário para metros e tempos dos outros pares. Não foi acessado no pacote.
3. Percursos atração→atração e última atração→estação ainda são apenas sequências candidatas, com distância e duração desconhecidas.
4. Coordenadas de Brugge Station têm conflito de registros no Wikidata: validar a coordenada exata/entrada antes de fornecer rota navegável.
5. Verificação visual da interface e inclusão de mapas não fazem parte deste pacote.

**Conclusão:** o Pacote 2 entrega dados reais e um inventário validável, mas o objetivo completo de mobilidade pedestre P0 segue **parcialmente atendido**. Não apresentar como completo nem atribuir desempenho fictício à caminhada.
