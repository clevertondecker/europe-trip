# ROUTES 7A — rastreabilidade do piloto de 15 pares

**Snapshot imutável:** `data/europa2027_pesquisa_15_pares_original.csv` reproduz a pesquisa de 17/11/2026, sem substituir durações originais. A matriz JSON mantém `fastest_min`, `average_min` e `original_snapshot` correspondentes ao CSV; `recheck` guarda uma observação separada de 18/11/2026. `load_route_references()` exige que ambos concordem quanto ao snapshot e valida estados cruzados.

**Resultado da reconsulta:** 13 dos 14 mínimos intermunicipais foram corroborados em páginas-resumo por cidade dos operadores/agregadores, sem fixação da data do serviço. O mínimo Strasbourg → Mulhouse (49 min) não foi corroborado nesta rodada como uma **nova** evidência, embora exista no histórico legado. Os valores de **Lille → Belfort 294**, **Lille → Mulhouse 252** e **Mulhouse → Bruxelas 288 minutos** continuam preservados; foram novamente encontrados em páginas da SNCF. Para a média Strasbourg → Belfort, o CSV contém **116 min** e a reconsulta SNCF exibiu **106 min**; o programa registra a divergência e não usa automaticamente a média antiga nem substitui o snapshot. A média Lille → Haguenau **246 min** não foi corroborada. Referências agregadas da Trainline foram tratadas como secundárias.

**Identidade e comparabilidade:** o mínimo publicado pela página de uma rota entre *cidades* é somente uma referência indicativa, não um serviço concreto. Belfort-Ville ≠ Belfort-Montbéliard TGV; Lille-Flandres ≠ Lille-Europe; Gent-Sint-Pieters não representa qualquer ponto da cidade de Gand. Quando não há confirmação independente de origem e destino ferroviários, ambos IDs permanecem `null` e `comparability=indicative_only_not_station_comparable`. Lille-Europe ↔ Bruxelles-Midi e Strasbourg ↔ Bruxelles-Midi têm a identificação explicitamente apresentada nas páginas-resumo, mas **não** comprovam calendário/duração para 2027.

## Estados por campo

- `fastest_provenance=corroborated_city_level`: valor reproduzido como mínimo de uma página-resumo; mostrado apenas como `mínimo indicativo por cidade`, nunca como itinerário comparável por estação.
- `fastest_provenance=snapshot_only_unreproduced`: preservar mas **não mostrar como referência confiável** em células novas.
- `average_provenance=corroborated_city_level`: mostrar como média publicada, separadamente do mínimo.
- `average_provenance=disagrees_with_current_page | snapshot_only_unreproduced | not_provided`: conservar a informação original, sem apresentá-la como média atual comprovada.
- `reference_differs_from_legacy`: tempos numéricos diferentes de universos de serviços/estações não constituem conflito; somente observações sobre o mesmo serviço concreto e condições compatíveis poderiam ser classificadas como conflito verdadeiro.
- `local`: sem trem intermunicipal; acesso urbano pendente.

**Validação:** 15 pares direcionais únicos, domínio HTTPS consistente com a natureza da fonte, coerência entre estado/tempo/confiança/estações, nenhuma tarifa/retorno/frequência inventada, teste negativo de incompatibilidade, snapshot recalculável por CSV, `get_rail_evidence()` intocado.

**Dependência:** PR #127 consome somente este overlay; após o merge de #126, sua base deve ser alterada para `main`, e a suíte integrada precisa passar. `TripPlan`, wishlist e base oficial intocados.

**Limite:** as páginas mudam conforme data e operador e não são cotação para setembro–novembro de 2027. Os registros continuam adequados apenas a planejamento exploratório.
