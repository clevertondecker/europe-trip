# Data Quality 2.1 A — retornos e fins de semana (16/11/2026)

Base: PR #67 e módulos `dq20_weekend_routes_model.py` / `rail_evidence_unified_model.py`. Não reescrever originais.

## Achados adicionais
- SNCB publica primeiro/último serviço nos dois sentidos entre Bruxelas e Bruges aos sábados e domingos, com média de 64 minutos: https://www.belgiantrain.be/en/travel-info/origin-destination/brussels-bruges . Isso é um **padrão**, não prova de ligação até Mulhouse/Strasbourg/Freiburg.
- Há uma amostra da SNCF/SBB republicada para Strasbourg→Luxemburgo no sábado **21/11/2026, 22:00–23:49** (não uma saída útil para bate-volta): https://pickthetrain.com/trains/strasbourg-to-luxembourg/
- SNCF documenta Luxembourg→Strasbourg em dia útil terça-feira **17/11/2026, 16:44–19:00** com conexão: https://www.sncf-connect.com/en-en/train/timetables/luxembourg/strasbourg . Essa evidência NÃO substitui retorno de domingo.
- DQ 2.0 já registrou Freiburg→Bruxelas sábado 14/11/2026; preservado como dado de ida, sem retorno da mesma data.

## Contratos
- `load_weekend_details()`: valida trechos datados e padrões de serviço separadamente.
- `paired_day_trip(origin,destination,date,minimum_hours=4,last_mile_minutes_each_way=None)`: só testa um par de horários **na mesma data e em dia de fim de semana**, subtraindo última milha apenas se conhecida. Exemplo sintético nos testes não é pesquisa de viagem real.
- `weekend_research_matrix()`: preserva 15 pares e ausência de retorno comprovado.
- `combined_belgian_weekend()`: documenta somente o trecho intermunicipal Bruselas–Bruges.
- `weekend_hypotheses(8|9)`: fins de semana editoriais, com descanso e sem datas reais.

## Cobertura
Tempo de ida histórico: 15/15 (herdado DQ2.0). Saída em sábado com hora exata identificada para 2 pares; **0/15** roteiros completos com ida+volta+última milha verificados. Sem hotel confirmado ou tarifa 2027; ainda depende de busca por data no operador e confirmação de hotel.

## Condição para próxima pesquisa
Não escolher vencedor por tempo mínimo; pesquisar o mesmo fim de semana para 15 pares, a ida e a volta e sua conexão porta a porta. Disponibilidade de 2027 pode continuar indisponível por antecedência.
