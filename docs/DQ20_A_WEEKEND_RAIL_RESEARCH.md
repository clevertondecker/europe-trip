# Data Quality 2.0 · PR A — Roteiros e evidências de fim de semana

## Inventário e decisão de modelagem
Reutilizamos `rail_evidence_unified_model.py` (UX 4.3) e os três catálogos canônicos. Acrescentamos **apenas evidências complementares** em `data/dq20_route_evidence_delta_2026_11.json`, mantendo registros originais inalterados.

- 3 bases × 5 destinos = **15 combinações fixas**: Luxemburgo, Interlaken, Bruxelas, Bruges e Rotterdam.
- Evidências novas: **14 observações adicionais** de horários/durações publicados em 2026; somadas às fontes já normalizadas da UX 4.3, há referência histórica de tempo de ida em **15/15** pares. Isso NÃO é confirmação de ida e volta aos fins de semana nem garantia de horários em 2027.
- `dq20_weekend_routes_model.py`: `route_matrix()` expõe as 15 linhas e preserva proveniência, ausência de tempo e a diferença entre mínimo e representativo.
- Critérios explícitos: bate-volta só com ida + volta de fim de semana e pelo menos quatro horas úteis verificadas; longas de pelo menos quatro horas só são rotuladas como **indicativamente exigentes**; desconhecidas permanecem desconhecidas.
- Nenhum dos 15 pares recebe classificação de "bate-volta comprovado" sem um itinerário de retorno verificado. Deutsche Bahn documenta um exemplo de **saída no sábado 14/11/2026** de Freiburg para Bruxelas (07h06–12h36, duas conexões), mas falta a volta ao ponto de origem.
- A SNCB documenta Bruxelas–Bruges como trecho direto, aproximadamente 64 minutos em média, com operação aos fins de semana. Isso **não** valida a chegada a Bruxelas nem o retorno à cidade-base.
- `illustrative_weekends(8|9)` mantém finais de semana de descanso e engloba os mesmos cinco destinos. Nenhum calendário/data ou total de transportes é inventado.

## Fontes adicionais consultadas (16/11/2026)
1. SNCF Connect — Mulhouse/Luxembourg: https://www.sncf-connect.com/en-en/train/timetables/mulhouse/luxembourg
2. SNCF Connect — Strasbourg/Luxembourg: https://www.sncf-connect.com/en-en/train/timetables/strasbourg/luxembourg
3. SNCF Connect — Strasbourg/Brussels: https://www.sncf-connect.com/en-en/train/route/strasbourg/brussels
4. SNCF Connect — Strasbourg/Rotterdam: https://www.sncf-connect.com/en-en/train/timetables/strasbourg/rotterdam
5. SNCF Connect — Mulhouse/Rotterdam: https://www.sncf-connect.com/train/trajet/mulhouse/rotterdam
6. SNCB — Bruxelles/Bruges: https://www.belgiantrain.be/en/travel-info/origin-destination/brussels-bruges
7. Trainline — Freiburg/Interlaken (secundário): https://www.thetrainline.com/en/train-times/freiburg-breisgau-hbf-to-interlaken-ost
8. Rome2Rio — Freiburg/Luxembourg (secundário): https://www.rome2rio.com/Train/Freiburg-im-Breisgau/Luxembourg-Station
9. Omio — Freiburg/Rotterdam (secundário): https://www.omio.com/trains/freiburg-im-breisgau/rotterdam

10. Deutsche Bahn — Freiburg/Bruxelles: https://www.bahn.de/reisen/view/verbindung/freiburg/bruessel.shtml (amostra sábado 14/11/2026)
11. Trainline — Mulhouse/Bruges **(Brugge, Bélgica)**: https://www.thetrainline.com/en/train-times/mulhouse-to-bruges-brugge
12. Trainline — Strasbourg/Bruges **(Brugge, Bélgica)**: https://www.thetrainline.com/en/train-times/strasbourg-to-bruges-brugge
13. Trainline — Freiburg/Bruges **(Brugge, Bélgica)**: https://www.thetrainline.com/en/train-times/freiburg-breisgau-hbf-to-bruges-brugge
14. Trainline — Mulhouse/Interlaken Ost: https://www.thetrainline.com/en/train-times/mulhouse-to-interlaken-ost
15. Trainline — Strasbourg/Interlaken Ost: https://www.thetrainline.com/en/train-times/strasbourg-to-interlaken-ost

**Atenção à homonímia:** Bruges (Brugge) na Bélgica e Bruges na França são destinos diferentes. Somente `bruges_be` pertence à cesta piloto. Páginas de distribuidores apresentam mínimos e médias genéricos, não um itinerário único reservado para data concreta; uma média e um tempo mínimo não são necessariamente do mesmo serviço.

## Lacunas e limites
- O serviço do trecho Bruxelas–Bruges opera em fins de semana, mas não demonstra conexões até cada base.
- Horários de terça-feira não permitem confirmar funcionamento no domingo.
- Tempos de estação a estação, tempo porta a porta, tempo de visita e bilhetes são conceitos diferentes.
- Roteiros de Interlaken, Bruxelas/Bruges e Rotterdam merecem simulação de pernoite; ainda faltam ida e volta em data equivalente, últimos trens, deslocamento urbano e orçamento para o casal.
- A camada pode alimentar o PR D após revisão, sem alterar `TripPlan`, favoritos e orçamento oficial.
- Nenhuma pesquisa sobre hospedagem individual foi feita.

## Testes
`python -m unittest tests.test_dq20_weekend_routes -v` e suíte completa no CI; inspeção visual só se houver navegador de produção.
