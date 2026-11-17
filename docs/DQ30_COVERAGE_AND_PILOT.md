# DQ3.0 — Auditoria e piloto de evidências (17/11/2026)

## Escopo e metodologia

Snapshot da `main` em 17/11/2026 antes desta branch. Leitura de `data/base_city_research_expanded_2026_11.json`, `data/five_base_comparison_evidence_2026_11.json`, `data/base_destination_routes_2027.json`, `data/attractions_2027.json`, `data/dq21_weekend_evidence_2026_11.json` e contratos dos adaptadores de rotas. Observações em datasets auxiliares não foram somadas como pares canônicos novos. Nenhuma reserva ou edição de TripPlan.

## Cobertura encontrada

| Métrica | Antes | Depois desta entrega | Definição |
|---|---:|---:|---|
| Cidades pesquisadas | 30 | 30 | `cities` no estudo histórico |
| Shortlist | 12 | 12 | `shortlist=true` |
| Cesta comparativa | 15 | 15 | destinos fixos do estudo de cinco bases |
| Destinos no catálogo canônico | 14 | 14 | destinos de `attractions_2027.json` |
| Atrações canônicas | 65 | 65 | `attractions` |
| Atrações com coordenadas verificadas | 0 | 0 | coordenadas na atração; o piloto só verifica endereços |
| Rotas canônicas | 56 | 56 | `base_destination_routes_2027.json` |
| Rotas canônicas com tempo | 14 | 14 | `train_minutes_one_way` preenchido |
| Rotas canônicas com última milha | 0 | 0 | `first_last_mile_minutes` preenchido |
| Retornos de fim de semana canônicos verificados | 0 | 0 | `weekend_return_verified=true` |
| Evidências adicionais do piloto | 0 | 2 serviços datados + 2 resumos de corredor | Fonte complementar, NÃO soma cobertura canônica |
| Atrações canônicas com acesso oficial descrito no piloto | 0 | 2 | referência por ID, sem coordenadas |
| Referências urbanas não canônicas | 0 | 1 | Musée Unterlinden; 15 min a pé **informados pelo museu**, não calculados |

### Cesta de 15 destinos — cobertura ferroviária histórica parcial

Os valores da coluna tempo são o número de destinos distintos com tempo positivo em `five_base_comparison_evidence_2026_11.json` **ou** `base_destination_routes_2027.json`. Não incluem a terceira origem `exploration_bases_2027.json`, `dq20` nem trajetos locais; portanto não representam toda a pesquisa existente. Retornos e última milha são medidos exclusivamente no catálogo de 56 pares.

| Cidade-base | Com tempo /15 | Retornos verificados na cesta | Última milha na cesta | Ofertas históricas cadastradas |
|---|---:|---:|---:|---:|
| Mulhouse | 6 | 0 | 0 | 3 |
| Strasbourg | 9 | 0 | 0 | 3 |
| Freiburg im Breisgau | 0 | 0 | 0 | 3 |
| Offenburg | 5 | 0 | 0 | 3 |
| Lille | 6 | 0 | 0 | 2 |
| Metz | 1 | 0 | 0 | 3 |
| Nancy | 1 | 0 | 0 | 3 |
| Karlsruhe | 0 | 0 | 0 | 3 |
| Trier | 1 | 0 | 0 | 3 |
| Liège | 0 | 0 | 0 | 3 |

**Atenção:** zero nesta matriz significa ausência do campo na seleção de datasets usada para este recorte, não inexistência de trens. A densidade de pesquisa não é uma nota de qualidade da cidade. Nenhuma oferta histórica prova disponibilidade mobiliada para duas pessoas no outono de 2027.

## Verificações externas documentadas no piloto

1. **Offenburg → Strasbourg — DB**: quadro de horários publicado em 11/11/2026 para **quarta-feira 25/11/2026**: SWE direto 06h35–07h04 (29 min), preço *desde* €13,20 por pessoa/trecho; TGV direto 07h15–07h40 (25 min), sem preço verificado. Esses serviços são horários publicados para uma data futura no momento da pesquisa, **não viagens já operadas**. Fonte: https://www.bahn.de/reisen/view/verbindung/offenburg/strassburg.shtml
2. **Strasbourg → Colmar — SNCF Connect**: página da rota apresenta mínimo 26 min e média 31 min; tarifa *desde* €6 para pessoa/trecho, condicionada a datas e disponibilidade. Não garante ida e retorno específicos em 2027. Fonte: https://www.sncf-connect.com/en-en/train/route/strasbourg/colmar
3. **Brussels → Bruges — SNCB**: conexão direta, duração média publicada de 1h04. A página apresenta padrões de sábado/domingo para o trecho, mas **não** verifica retorno da base de moradia. Fonte: https://www.belgiantrain.be/en/travel-info/origin-destination/brussels-bruges
4. **Cathédrale Notre-Dame — turismo Strasbourg**: Place de la Cathédrale, 67000 Strasbourg; bonde A/D, parada Langstross Grand'Rue. Tempo de acesso e coordenadas da entrada continuam ausentes. Fonte: https://www.visitstrasbourg.fr/en/fiche-sit/F223007269_the-cathedral-of-notre-dame-strasbourg/
5. **Grand-Place — visit.brussels**: Grand-Place, 1000 Brussels, endereço oficial; rota caminhável da estação ainda não pesquisada. Fonte: https://www.visit.brussels/en/visitors/venue-details.3743
6. **Musée Unterlinden — site do museu**: Place Unterlinden, Colmar; acesso desde a estação a pé em **15 minutos segundo o museu**, ou ônibus 1/3/4/5/7/8 até Théâtre. Não é uma atração canônica cadastrada, por isso está na seção exploratória. Fonte: https://www.musee-unterlinden.com/en/visit-and-activities/informations/access/

## Integração implementada

- `data/dq30_mobility_pilot_2026_11.json`: novas observações datadas e endereços/acessos com `null` para campos não pesquisados.
- `dq30_mobility_evidence_model.py`: validação e consulta somente leitura.
- `rail_evidence_unified_model.py`: inclui observações ferroviárias do piloto **sem** substituir a precedência das fontes históricas, somar preços ou declarar viagens comparáveis.
- Testes de integridade, ID canônico, preservação de desconhecidos e regressão do adaptador.

## Lacunas e próximos PRs propostos

**PR 2 — Geolocalização e caminhos caminháveis:** verificar pontos de entrada com OSM ou serviço licenciado, registrar geometria/atribuição e apenas então obter tempos caminháveis. Não inventar 65 coordenadas nem calcular Haversine como caminhada.

**PR 3 — Produto:** visualização consultiva em comparação de bases, passeios e grupos de fim de semana, usando o adaptador reconciliado, sem alterar decisões oficiais.

**Trabalho de pesquisa ainda em aberto:** amostragem comparável para as cinco bases da onda 1, ida de sábado e volta de domingo no mesmo fim de semana (de cada trecho), mobilidade porta a porta, tarifa normal para dois adultos, estadia de 55–65 noites e trabalho remoto. Todas as datas de viagem de 2027 permanecem sem verificação.

Sem score final, sem alteração de `TripPlan`, sem merge/deploy sem aprovação.
