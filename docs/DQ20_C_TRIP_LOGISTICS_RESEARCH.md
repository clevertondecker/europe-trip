# Data Quality 2.0 · PR C — Chegada, aeroporto e logística sem carro

## Decisões oficiais versus propostas
\`trip_plan_model.new_plan()\` admite 65–75 dias, Itália 8–12 dias, base oficial de referência Mulhouse e proposta italiana opcional. \`data/italy_honeymoon_research_2027.json\` contempla três **propostas**; a alternativa equilibrada menciona 4 noites Roma + 5 Maiori e saída no dia 10 pelo Aeroporto de Nápoles **como hipótese, sem reserva**. O documento \`RELATORIO_REVISAO_LUA_DE_MEL_ITALIA_2027.md\` mantém a opção de última noite em Nápoles se o voo for cedo.

O modelo \`dq20_trip_logistics_model.py\` não escolhe aeroporto italiano nem pressupõe voo NAP→base. Se a proposta é informada, apenas exibe o último local do cenário. Isso impede promover uma opção editorial a decisão oficial.

## Acessos pesquisados em fontes oficiais (16/11/2026)
- Mulhouse → EuroAirport (BSL/MLH/EAP): trem até Saint-Louis + ônibus Distribus 11; trecho ônibus ~10–15 min, frequência ~15–30 min; não é tempo total desde o hotel. https://www.euroairport.com/en/transport
- Strasbourg → Entzheim (SXB): TER Strasbourg Gare–Entzheim Aéroport em exemplos publicados com ~7–13 min entre estações; terminal/hotel e voo não incluídos. https://www.sncf-connect.com/train/horaires/strasbourg/entzheim
- Strasbourg → EuroAirport: TER até Saint-Louis + ônibus 11, em alternativa estrutural; sem tempo composto de mesma partida. https://www.euroairport.com/en/transport
- Freiburg → EuroAirport: ônibus direto entre central bus station e terminal, ~60 min com partidas aproximadamente horárias anunciadas. https://www.euroairport.com/en/transport
- Napoli Centrale ↔ Aeroporto de Nápoles: ônibus Alibus, ~15 min de trecho; não inclui Salerno/Maiori→Napoli ou voo futuro. https://www.aeroportodinapoli.it/en/by-bus

## Contratos
- \`load_airport_links()\`: valida fontes e ausência de totais falsos;
- \`compare_airport_access(itinerary_variant=None, italy_exit_candidate=None)\`: produz opções condicionais, status, trechos com evidências e lacunas;
- \`airport_comparison_rows(result)\`: apresentação tabular uniforme.

## Ainda não comprovado
- Cidade/hotel italiano final e data; disponibilidade e conexão aérea da Itália até cada base;
- Aeroportos com rotas Brasil adequadas e conexões de voos;
- Bagagens, horários noturnos de ônibus e trem, esperas, check-in, riscos de conexões;
- Tempo porta a porta de cada acomodação para cada aeroporto;
- Tarifas de 2027 e necessidade real de pernoite pré-voo.

**Sem nota geral, ranking, mutação de orçamento ou TripPlan.** Campos desconhecidos são \`null\`; qualquer tempo publicado representa apenas seu trecho.
