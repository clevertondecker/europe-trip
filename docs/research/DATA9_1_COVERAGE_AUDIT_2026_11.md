# DATA 9.1 — Auditoria de cobertura da DQ 3.2

**Estado pesquisado:** 18/11/2026. Extraído em GitHub Actions pela função
`build_rail_coverage_inventory()` contra o catálogo versionado do repositório.

## Resultado global

| Categoria exclusiva | Total |
|---|---:|
| Cidades-base | 30 |
| Destinos exploratórios | 46 |
| Pares base × destino | **1.380** |
| Tempo histórico do catálogo | 54 |
| Referências indicativas (DATA 9 / ROUTES 7) | 34 |
| Deslocamento local (não ferroviário) | 30 |
| **Pares sem duração documentada** | **1.262** |

Todas as categorias são mutuamente exclusivas. Os 34 indicativos não equivalem a serviços confirmados e não foram reclassificados como históricos. **Nenhuma das 1.380 combinações possui itinerário completo de ida e volta validado para 2027 neste relatório.**

## Destinos que merecem investigação

Do levantamento ordenado por quantidade de cidades-base sem tempo:

| Destino | País | Bases sem tempo |
|---|---|---:|
| Épernay | França | 30 |
| Lauterbrunnen | Suíça | 30 |
| Oeschinensee / Kandersteg | Suíça | 30 |
| Arlon | Bélgica | 29 |
| Arras | França | 29 |
| Beaune | França | 29 |
| Besançon | França | 29 |
| Esch-sur-Alzette | Luxemburgo | 29 |
| Kehl | Alemanha | 29 |
| Liège | Bélgica | 29 |
| Lörrach | Alemanha | 29 |
| Lyon | França | 29 |
| Namur | Bélgica | 29 |
| Offenburg | Alemanha | 29 |
| Reims | França | 29 |
| Saarbrücken | Alemanha | 29 |
| Saint-Louis | França | 29 |
| Saverne | França | 29 |

**Importante:** quantidade de pares sem pesquisa não é prioridade turística nem prova de impossibilidade de viagem. É um critério para planejar a próxima coleta. O ranking de pesquisa deve considerar também a wishlist e a proximidade de destinos concretamente desejados.

## Inventário completo reproduzível

Execute a partir da raiz do repositório:

```bash
python scripts/audit_data9_rail_coverage.py --output /tmp/data9-coverage
```

Arquivos gerados:
- `inventory.json`: todos os 1.380 pares, estados de evidência, fonte quando existe, e pendências independentes de 2027.
- `backlog.json`: os 1.262 pares ainda sem tempo, com campos específicos a pesquisar.
- `summary.md`: os 46 destinos ordenados por bases pendentes e as 30 cidades-base com suas respectivas coberturas.

A produção é **read-only**: nenhum JSON canônico, TripPlan, wishlist ou orçamento é modificado. Um inventário de 1.262 pares **não significa** que seja necessário buscar todos imediatamente: começar pelos destinos escolhidos para a viagem, com resultados por sentido e sem estimar conexões sem fonte.

## Áreas da aplicação auditadas

- **Explorar → Comparar:** já usa a projeção histórica + DATA 9; manter.
- **Explorar → Passeios → Descoberta ampliada DQ 3.2:** corrigida neste PR para reutilizar a mesma projeção e apresentar referências indicativas sem inflar os históricos.
- **Ferramentas antigas de cidades-base, comparador de cinco bases e orçamentos:** modelos específicos de excursões e amostras; não interpretar referências de ida do DATA 9 como rotas completas de casal.
- **Descoberta de POIs e moradia:** fonte de localização/pesquisa, não documentação ferroviária completa.

## Pendências de pesquisa além da ida

Em todos os pares, mesmo quando há tempo histórico ou indicativo, continuam independentes: **estações, serviço de volta em fim de semana, conexões, horários de 2027, preço para dois adultos, transporte urbano e acesso real às atrações**. Nenhum desses campos pode ser inferido pela presença de um mínimo ferroviário.

**Prompt executado:** `docs/prompts/DATA9_1_SHARED_RAIL_COVERAGE.md`.
