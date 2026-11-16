# Matriz ferroviária prioritária — Mulhouse e Strasbourg

**Revisão de pesquisa:** 16/11/2026. **Aplicação:** setembro–novembro/2027, sem datas reserváveis. Esta atualização não cria nenhuma tarifa ou volta de 2027.

## Inventário e causa-raiz

- A matriz `data/base_destination_routes_2027.json` continha 44 pares (quatro bases × 11 destinos), incluindo `luxembourg` e `interlaken`, porém **com minutos nulos** para ambas as bases.
- `data/five_base_comparison_evidence_2026_11.json` já continha evidências de outras rotas, mas não as dez combinações pedidas. Nele o identificador de Luxemburgo é `luxembourg_city`; no explorador e no catálogo de atrações é `luxembourg`.
- `data/exploration_bases_2027.json` já reconhecia `brussels`, `bruges_be` (Bruges, Bélgica) e `rotterdam`; não tinha rotas para Mulhouse e Strasbourg. `Bruges (France)` é outra cidade e **não** foi incorporada.
- `known_route()` procurava o identificador literal; agora resolve explicitamente o alias do Luxemburgo antes de consultar as fontes. Nunca soma trechos intermediários de outras pesquisas para gerar rota artificial.
- Evidência nova de seis pares foi incorporada à **matriz existente de cinco bases**, dois pares ao dataset canônico das quatro bases e dois pares ao explorador. Não criamos arquivo JSON paralelo de rotas.

## Dez rotas investigadas (somente ida estação–estação)

| Origem | Destino | Mínimo histórico | Referência típica | Fonte | Categoria |
|---|---|---:|---:|---|---|
| Mulhouse | Luxembourg | 2h37 | 3h31 | [SNCF Connect](https://www.sncf-connect.com/en-en/train/route/mulhouse/luxembourg) | Oficial |
| Strasbourg | Luxembourg | 1h35 | 2h34 | [SNCF Connect](https://www.sncf-connect.com/en-en/train/route/strasbourg/luxembourg) | Oficial |
| Mulhouse | Interlaken Ost | 2h14 | 2h56 | [Trainline](https://www.thetrainline.com/en/train-times/mulhouse-to-interlaken-ost) | **Secundária: reconfirmar SBB** |
| Strasbourg | Interlaken Ost | 3h12 | 3h54 | [Trainline](https://www.thetrainline.com/en/train-times/strasbourg-to-interlaken-ost) | **Secundária: reconfirmar SBB** |
| Mulhouse | Bruxelles-Midi | 4h48 | 5h11 | [SNCF Connect](https://www.sncf-connect.com/train/horaires/mulhouse/bruxelles) | Oficial |
| Strasbourg | Bruxelles-Midi | 3h42 | 4h06 | [SNCF Connect](https://www.sncf-connect.com/en-en/train/route/strasbourg/brussels) | Oficial |
| Mulhouse | Brugge (Bélgica) | 5h54 | 7h11 | [Trainline](https://www.thetrainline.com/en/train-times/mulhouse-to-bruges-brugge) | **Secundária: reconfirmar SNCB** |
| Strasbourg | Brugge (Bélgica) | 4h55 | 6h25 | [Trainline](https://www.thetrainline.com/en/train-times/strasbourg-to-bruges-brugge) | **Secundária: reconfirmar SNCB** |
| Mulhouse | Rotterdam Centraal | 6h06 | 6h28 | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/rotterdam) | Oficial |
| Strasbourg | Rotterdam Centraal | 5h10 | 5h39 | [SNCF Connect](https://www.sncf-connect.com/en-en/train/route/strasbourg/rotterdam) | Oficial |

Dados publicados em novembro de 2026 (algumas páginas Trainline exibem exemplos de datas diferentes dentro de 2026). Médias de operador são indicadores gerais, não horários que se possa reservar para a viagem. Trem direto em poucos horários não representa frequência elevada.

**Importante:** os campos `roundtrip_couple_eur`, tarifa normal, horário da volta, condições tarifárias de 2027 e última milha permanecem `null` ou marcados como pendentes. Não foi inventada uma tarifa de ida nem foi duplicada ida para calcular preço de volta. Para Luxemburgo há exemplos diretos TGV e conexões TER; para Bruxelas/Rotterdam as opções mais rápidas podem passar por **mudança de estação em Paris**, não apenas de trem. Para Interlaken Ost e Brugge os tempos dependem de conexões.

## Comparação estrutural ilustrativa

Para **uma ida a cada um dos cinco destinos**, usando *médias históricas* e não uma escolha de trens confirmada, os subtotais são:

- Mulhouse: **1.517 minutos (25h17)** só de ida.
- Strasbourg: **1.358 minutos (22h38)** só de ida.
- Diferença de 159 minutos na soma das cinco idas, favorável a Strasbourg nesse recorte.

Se, apenas como **hipótese de planejamento**, cada uma das cinco voltas consumisse a mesma média da ida, os totais seriam 3.034 minutos (50h34) e 2.716 minutos (45h16), respectivamente. **Esses totais NÃO são itinerários ida/volta verificados**, não contemplam esperas reais, deslocamento nas cidades nem tempo de visita. Não devem entrar no orçamento. A aplicação mostra esses subtotais apenas para os pares completos e com avisos expressos.

**Trade-offs:** Mulhouse é historicamente mais prática para Interlaken Ost neste conjunto; Strasbourg tem menores tempos médios para Luxemburgo, Bruxelas, Brugge e Rotterdam. A soma simples não resolve a decisão: frequências úteis, preço e logística de ida/volta e pernoite precisam ser cotados antes de concluir qual base é mais adequada.

## Regras de compatibilidade, precedência e finanças

- `known_route()` continua preferindo a matriz canônica das quatro bases **somente quando ela contém um horário documentado**; depois consulta observações da matriz de cinco bases; em seguida segmentos ferroviários ou a exploração.
- Apenas `luxembourg_city → luxembourg` e inverso para localizar fonte da matriz são aliases aceitos; `bruges_be` nunca é confundido com Bruges na França.
- O modelo mantém tempos históricos de ida e compara **médias quando disponíveis nos dois lados**, conservando também mínimos de ida para contexto. Não seleciona o menor tempo de datasets incompatíveis.
- `TripPlan`, backups JSON, decisões e orçamento **não são alterados**; o valor da moradia continua sendo somente uma hipótese manual, e as tarifas de trem desconhecidas não são €0.
- A classificação de bate-volta/pernoite é editorial, não confirmação; não há horários de volta validados.
- A matriz de doze bases finalistas deve ser expandida depois, começando pelos destinos **já escolhidos** no plano, bases comparadas de fato e trajetos com mais impacto em incerteza. Esta entrega não pesquisa todas as combinações.

## Validação pendente

1. Revisar em sessão real o painel Explorar → Comparar → destinos prioritários.
2. Validar as conexões úteis, especialmente mudança de estação em Paris, horários de retorno no sábado/domingo e necessidade de hospedagem.
3. Consultar SBB e SNCB para substituir/confimar quatro observações secundárias; conservar proveniência.
4. Cotar ida/volta para dois adultos nas datas de viagem quando as operadoras liberarem vendas.
