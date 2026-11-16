# Data Quality 2.1 C — aeroportos, ligação com a Itália e retorno ao Brasil

## Operadoras aéreas oficiais (2026, sem promessa de 2027)
- SWISS: ZRH → GRU, LX92, saída publicada ~22h40 e duração ~11h45. https://www.swiss.com/lhg/br/pt/o-d/cy-cy/zurique-sao-paulo
- Lufthansa: FRA → GRU, LH506, saída publicada ~22h05 e duração ~11h45. https://www.lufthansa.com/lhg/br/en/o-d/cy-cy/frankfurt-sao-paulo

**Rota publicada em 2026 != passagem de 2027, e chegar em GRU não significa estar no destino final no Brasil.** Não gerar preços/assentos/reservas.

## Exemplos de acesso estação-a-estação (2026)
- Freiburg Hbf → Frankfurt Flughafen Fernbahnhof: exemplo DB **28/11/2026 07h27–09h38 (2h11), uma conexão**: https://www.bahn.de/reisen/view/verbindung/freiburg/flughafen-frankfurt.shtml
- Strasbourg → Frankfurt Flughafen Fernbahnhof: exemplo SNCF 09h08–11h08 (2h00), data específica da amostra não confirmada: https://www.sncf-connect.com/train/horaires/strasbourg/aeroport-de-francfort-sur-le-main
- Strasbourg → Zürich HB: SNCF amostra terça **17/11/2026** 05h19–08h00 (2h41, 1 conexão). **Zürich HB não é Zürich Flughafen**. https://www.sncf-connect.com/en-en/train/timetables/strasbourg/z%C3%9Crich
- Dados EuroAirport, SXB e ônibus para Freiburg da DQ 2.0 permanecem intactos.

## Saída de Itália
O Aeroporto de Nápoles publicou em 2026 o Alibus Napoli Centrale ↔ aeroporto (~15 min). Na página oficial, a oferta citada a partir de 01/11/2026 apresenta intervalos **06h–09h e 15h–18h** com saídas a cada 30 min; é necessário confirmar se essa informação é completa e atual para a data da viagem, pois pode não cobrir voos em outros horários: https://www.aeroportodinapoli.it/en/by-bus . Maiori/Salerno → Napoli Centrale continua SEM tempo de porta a porta verificado e NAP vs FCO ainda é hipótese.

## Contratos
`evaluate_travel_options(italy_variant=None, italy_exit_airport=None, final_brazil_airport=None)` expõe 3 bases e aeroportos pesquisados, preservando `null` para tempo total, 2027 custo e reserva. Nenhuma alteração de `TripPlan`.

## Pendências de compra
Voos com origem italiana real, data, malas, custos, chegada final no Brasil, horários porta a porta por endereço do apartamento, margem de aeroporto, pernoite pré-voo. Comparar FRA/ZRH/BSL/SXB sem tratar frequência de voos de 2026 como certeza 2027.
