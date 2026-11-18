# LOG — Contrato de pendências logísticas por componente

**Estado:** proposta incremental de contrato (18/11/2026). Não declara transporte ou serviço válido para 2027.

## Problema corrigido

O relatório DATA 9.1 original enumerava **1.262 pares sem duração de ida** em um universo de 30 bases × 46 destinos, mas sua lista `research_backlog()` não incluía pares históricos e indicativos que ainda não tinham horário de retorno, conexão, tarifa de casal ou última milha.

**Política de compatibilidade:** `research_backlog()` e os arquivos `inventory.json`, `backlog.json` e `summary.md` continuam com o contrato e contagens anteriores. Nenhum número existente é substituído.

## Novo contrato read-only

`component_research_backlog(inventory)` retorna uma linha por **par base × destino**, com `category`, duração de ida e fonte apenas quando documentadas, `research_required` e `confirmed_2027=False`. Resultado para o snapshot atual: **1.380 linhas**.

`component_gap_summary(backlog)` retorna `pairs`, distribuição por categoria e contagens de pendência **por componente**, não uma pontuação de qualidade.

| Categoria | Semântica | Exemplos de pendência |
|---|---|---|
| `historical` | Existe duração histórica de ida | serviço com data em 2027, estação, retorno independente, tarifa de casal, última milha, horário/duração da visita |
| `indicative` | Existe mínimo/amostra indicativa de ida | as mesmas pendências; nenhuma promoção a horário confirmado |
| `missing` | Ainda falta duração de ida | fonte da operadora, tempo da ida + todas as pendências do cenário |
| `local` | Cidade-base = destino; não há necessidade de trem intermunicipal | **ida e volta urbanas** separadas, custo local para casal e janela da atração; `None` para tempo local desconhecido |

Os dois sentidos de acesso local são propositalmente distintos. Uma rota a pé editorial não pode satisfazer `local_access_outbound` ou `local_access_return` como se fosse uma medição oficial.

No snapshot atual, os **1.350 pares não locais** carecem de serviço de retorno independente; isso não significa que inexistam trens. Os **30 pares locais** carecem de avaliação urbana e não são considerados viagens de 0 minuto.

## Exportação reproduzível

```bash
python scripts/audit_data9_rail_coverage.py --output /tmp/data9-coverage
```

Novos arquivos adicionais:

- `component_backlog.json`: todos os pares e os campos específicos ainda pendentes;
- `component_summary.json`: contagens de pendências por componente.

Nenhum arquivo de `data/`, documento de Drive, `TripPlan` ou plano versionado é modificado.

## Limites

Este levantamento é **sobre a informação registrada**, não uma avaliação temporal nem uma pesquisa de disponibilidade. Ele não deriva estação, hora, duração de retorno ou tarifa a partir da ida. Identidade canônica de atração, janela de abertura e duração de visita ainda precisam de composição com outros datasets.

O próximo PR de núcleo logístico deve consumir esse relatório somente como **backlog de pesquisa**. Para decidir viabilidade, aplicar `rail_temporal_contract`, `rail_transfer_contract`, `weekend_return_validation_model` e evidências de caminhada em uma avaliação independente por data. Não substituir o comparador ou classificar lugares automaticamente neste PR.
