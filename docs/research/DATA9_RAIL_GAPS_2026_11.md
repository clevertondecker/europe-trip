# DATA 9 — Enriquecimento ferroviário das lacunas

**Consulta e snapshot:** 18/11/2026. **Escopo:** referências exploratórias de ida para comparar cidades-base sem criar serviços ferroviários para 2027.

## Entregas

- 14 pares que estavam sem tempo na captura inicial com Aachen, Karlsruhe, Amsterdam e Interlaken (5 cidades-base).
- 15 combinações adicionais entre bases e destinos já existentes no catálogo. A relação está no dataset `data/rail_gap_enrichment_2026_11.json`.
- Duas candidatas não ligadas a destinos canônicos (Zürich e Geneva) permanecem explicitamente fora da projeção.
- Qualquer outro par que não possua fonte continua como **Tempo não pesquisado**; ausência de evidência não é inviabilidade.

## Referências prioritárias de ida

| Base | Destino | Minutos (fonte) | Classe de evidência |
|---|---|---:|---|
| Mulhouse | Aachen | 279 | Mínimo secundário Trainline |
| Strasbourg | Aachen | 282 | Referência secundária Rome2Rio |
| Lille | Aachen | 126 | Subtrecho de serviço SNCF Lille–Cologne, amostra |
| Karlsruhe | Aachen | 183 | Mínimo publicado DB |
| Mulhouse | Karlsruhe | 116 | Amostra SNCF 2026 |
| Strasbourg | Karlsruhe | 48 | Mínimo publicado SNCF |
| Lille | Karlsruhe | 263 | Mínimo publicado SNCF |
| Aachen | Karlsruhe | 185 | Mínimo publicado DB |
| Mulhouse | Amsterdam | 414 | Mínimo publicado SNCF |
| Aachen | Amsterdam | 178 | Mínimo publicado DB |
| Karlsruhe | Amsterdam | 292 | Mínimo publicado DB |
| Lille | Interlaken Ost | 422 | Amostra Trainline de 24/11/2026 |
| Aachen | Interlaken | 422 | Referência Rome2Rio |
| Karlsruhe | Interlaken West | 232 | Referência secundária PickTheTrain |

**Importante:** tempo de ida publicado não é média típica nem viagem porta a porta. As referências de terceiro podem não corresponder às mesmas estações ou à mesma classe de serviço das operadoras. A amostra Lille–Interlaken 422 minutos é distinta do mínimo anunciado no mesmo agregador. Nenhuma fonte implica passagem, preço, retorno, conexão garantida ou horário para setembro–novembro de 2027.

## Fontes de exemplo e governança

- [SNCF Connect — Strasbourg → Karlsruhe](https://www.sncf-connect.com/en-en/train/route/strasbourg/karlsruhe): mínimo de 48 min na página por cidade.
- [DB — Aachen → Amsterdam](https://www.bahn.de/reisen/view/verbindung/aachen/amsterdam.shtml): mínimo de 178 min.
- [SNCF Connect — Lille → Karlsruhe](https://www.sncf-connect.com/train/trajet/lille/karlsruhe): mínimo de 263 min.
- [Trainline — Lille Europe → Interlaken Ost](https://www.thetrainline.com/train-times/lille-europe-to-interlaken-ost): exemplo 14h01–21h03 de 24/11/2026 (422 min, 3 mudanças); não é o mínimo global da página.

Cada registro tem URL HTTPS, data de pesquisa, classe da fonte, tempo de ida, identidade de origem/destino, campos nulos para tarifas e transferências desconhecidas, e `valid_for_2027=false`.

### Política de precedência

1. Tempo histórico legado com fonte continua autoritativo na matriz.
2. O piloto ROUTES 7 permanece intacto; mínimos confirmados da sua pesquisa mantêm seu papel anterior.
3. Somente células sem tempo de pesquisa utilizam DATA 9; a UI rotula mínimo oficial, amostra datada de 2026 ou referência secundária.
4. Não somar trechos, não espelhar direções, não converter ausência em zero, não transformar amostra em itinerário de retorno.
5. `TripPlan`, wishlist, seleção de cidades-base e orçamento oficial continuam somente leitura.

### Próximos ciclos

O conjunto completo de possíveis pares é calculado dinamicamente a partir dos identificadores cadastrados de cidades-base e destinos. A pesquisa deve ser incremental, priorizando os destinos desejados pelo usuário, e exigindo fontes específicas para **cada direção**. Para 2027 ainda faltam retorno no fim de semana, estações, mudanças de trem, acesso até as atrações, custo de casal e validação nas datas de viagem.
