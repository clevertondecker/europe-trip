# DATA 8.3 — Acesso local por estação, entrada e direção

**Papel:** Senior Mobility Researcher + Python Engineer. **Dependência:** DATA 8.2.

## Objetivo
Para atrações já conciliadas, permitir cenários editoriais de caminhada nos dois sentidos sem misturar com `attraction_last_mile_model`, que representa observações documentadas, nem com serviço ferroviário em datas concretas.

## Implementar
1. Entidade independente `attraction_id + direction + station_id + entrance_id + mode`, contendo faixa de duração, método e fonte. Chaves/direções independentes.
2. Piloto de sete atrações nas regiões centrais de Aachen, Strasbourg, Bruxelas e Lille, com 14 observações e intervalos **editoriais**, não tempos de mapa/operador.
3. Rejeitar duplicatas, estações incoerentes, durações impossíveis, `valid_for_2027` ou `joinable_to_rail_service` como verdadeiros.
4. Projeção de passeio local soma somente dois sentidos e somente para a estação exata; **não** pressupõe disponibilidade do trem, preço de passagem nem mesma duração ida/volta.
5. Todas as demais atrações ficam com acesso desconhecido. Para Baden-Baden, não inventar caminhada da estação principal até a Lichtentaler Allee sem revisar ônibus.

## Aceite
Fonte explica *a atração*, enquanto o método registra explicitamente que **não** fornece o tempo de caminhada. 7 atrações × 2 direções, zero acessos ferroviários verificados. Estado imutável, testes de assimetria, identidade e `null`. Sem editar modelos históricos, TripPlan ou app.py. Nenhum merge/deploy.
