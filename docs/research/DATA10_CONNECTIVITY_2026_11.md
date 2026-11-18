# DATA 10 — Pesquisa de conectividade e tempos entre bases

**Snapshot:** 18/11/2026 · **Natureza:** referência de trem, ida apenas, não
serviço programado para 2027. Documento operacional vinculado ao dataset DATA10.

## Universo pesquisado

- **30 cidades-base** do cadastro existente e **46 destinos** canônicos, ou
  1.380 pares dirigidos (incluindo 30 pares locais).
- **99 referências de tempo mínimo de ida** coletadas neste pacote, cobrindo
  origens nas **30 bases**; parte pode ser redundante com o histórico anterior.
- Duas classes de evidência: **operadora** (SNCF Connect, prioridade mais alta)
  e **fonte secundária** (Trainline, confiança reduzida).
- Destinos ausentes na pesquisa continuam **sem tempo**, não são classificados
  como inacessíveis; retorno, preço, frequência, última milha e horários
  setembro–novembro/2027 não são conhecidos por esse dataset.
- A cobertura efetiva é calculada **depois** da precedência de fontes; não
  contar 99 linhas como 99 novos pares sem verificar conflitos já pesquisados.

## Exemplos de referências incorporadas

| Origem | Destino | Duração mínima indicada | Fonte |
|---|---|---:|---|
| Mulhouse | Dijon | ~1h02 | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/dijon) |
| Mulhouse | Freiburg | ~50 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/fribourg-en-brisgau) |
| Strasbourg | Kehl | ~10 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/strasbourg/kehl) |
| Strasbourg | Baden-Baden | ~35 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/strasbourg/baden-baden) |
| Metz | Strasbourg | ~48 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/metz/strasbourg) |
| Sélestat | Strasbourg | ~19 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/selestat/strasbourg) |
| Arlon | Luxembourg City | ~20 min | [Trainline](https://www.thetrainline.com/en/stations/arlon) |
| Lörrach | Basel | ~7 min | [Trainline](https://www.thetrainline.com/en/stations/lorrach) |
| Esch-sur-Alzette | Luxembourg City | ~24 min | [Trainline](https://www.thetrainline.com/en/stations/esch-sur-alzette) |

**Interpretação:** menor duração indicada na rota publicada, não média,
promessa de intervalo diário, trem direto, nem saída válida na viagem de 2027.

## Inventário integral por base

Execute `python scripts/audit_data10_connectivity.py --output /tmp/data10-coverage`.
Os arquivos `coverage.json` e `coverage.md` discriminam histórico, indicativo,
DATA10 aplicado e desconhecido por **cada uma das 30 bases**. O CSV
`unresearched_pairs.csv` contém os pares ainda sem duração após toda a
evidência disponível, para a próxima rodada.

A política em `rail_reference_projection_model.decorate_comparison` permanece:
histórico preexistente → ROUTES7 → DATA9 → DATA10 → desconhecido.
Mínimos DATA10 não substituem evidência mais prioritária.

## Limitações e expansão futura

As referências foram selecionadas por tempo dirigido publicado, sem inferir
tempos inversos, soma de trechos, existência de ônibus onde não há fontes,
tempo de espera em conexão nem disponibilidade de 2027.

O número bruto de fontes não deve ser usado como nota automática de qual
cidade-base é melhor. A comparação precisa manter **a mesma cesta de
destinos e prioridades** para cada base e diferenciar pesquisa incompleta
de viagens inviáveis.

**Prompt executado:** [DATA10_ALL_BASES_CONNECTIVITY.md](../prompts/DATA10_ALL_BASES_CONNECTIVITY.md).
