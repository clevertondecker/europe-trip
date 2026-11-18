# Prompt executado — DATA 10 | Conectividade e duração entre todas as bases e destinos

**Repositório:** `clevertondecker/europe-trip`
**Base de partida:** `main` no commit `8d0681ec`
**Data da pesquisa:** 18/11/2026

## Papel

Atuar como Staff Software Engineer e pesquisador de transporte ferroviário europeu.
Priorizar cobertura verificável de conexões e duração de ida para seleção da
cidade-base da temporada europeia de 2027, sem simular disponibilidade futura.

## Objetivo e escopo

1. Inventariar o universo atual de **30 cidades-base × 46 destinos canônicos**
   (1.380 pares **dirigidos**). Canonicalizar Luxemburgo, Bruges e Colônia.
2. Reutilizar a pesquisa existente e identificar somente lacunas não cobertas
   por `evidence_query_model`, `routes7_reference_model`, DATA9 e seus overlays.
3. Pesquisar páginas públicas SNCF Connect, DB, SBB, CFL, SNCB ou plataformas
   secundárias como Trainline. Registrar **duração mínima publicada**, origem,
   destino, direção, fonte URL HTTPS, data da consulta, tipo e confiança.
4. Quando documentado, anotar também duração típica/conexão/modal sem obrigar
   toda rota a ter esses detalhes. Não gerar tempos por distância Haversine.
5. Preservar *ausente* como `None` ou `no_time`, nunca converter em zero,
   viagem impossível ou trajeto confirmado para 2027.
6. Não presumir que ida e volta são simétricas. Não compor automaticamente
   via bases intermediárias; conexões apenas quando uma fonte descreve o par.
7. Fontes secundárias devem ter confiança menor que a operadora; um mínimo
   divulgado não representa horário garantido.
8. Reutilizar `rail_reference_projection_model.decorate_comparison` como
   **única política de seleção**: histórico > ROUTES7 > DATA9 > DATA10 > desconhecido.
   Preservar as quatro categorias de exibição e `routes7_comparison_projection`
   como fachada de compatibilidade.
9. DQ3.2 e UX503 devem receber a mesma evidência, URL e rótulos em `reference_only`.
   Não alterar `TripPlan`, wishlist, orçamento, dados de 2027 nem implantação.
10. Relatar cobertura **após precedência** separadamente da quantidade bruta
    de referências cadastradas. Exibir lacunas por cidade-base e destino.
11. Preservar registros originais DATA9 e de fontes anteriores; adicionar
    dataset novo versionado. Não reescrever horários ou preços históricos.

## Entregas implementadas

- `data/data10_connectivity_2026_11.json`: fontes por par dirigidas.
- `data10_connectivity_model.py`: parser, validação de URL, tipo,
  mínimo, data, IDs canônicos e status 2027 explícito como não confirmado.
- `rail_reference_projection_model.py`: fallback DATA10, preservando
  precedências e categorias, sem segunda lógica de comparação.
- `dq32_macro_opportunities_model.py` e
  `rail_gap_coverage_audit_model.py`: retenção de proveniência por dataset.
- `scripts/audit_data10_connectivity.py`: exportar inventário de
  **todos os pares**, resumo por 30 bases e lista de pares sem tempo.
- `tests/test_data10_connectivity_coverage.py`: origem/destino, fonte,
  preferências, paridade das telas, ausência de horário de retorno e
  crescimento de cobertura.
- `tools/validate_research_data.py`: incluir validação do overlay
  na etapa de CI de contratos.
- `docs/research/DATA10_CONNECTIVITY_2026_11.md`: relatório reprodutível.

## Validação

```bash
python -m compileall -q .
python tools/validate_research_data.py
python -m unittest discover -s tests -v
python scripts/audit_data10_connectivity.py --output /tmp/data10-coverage
python scripts/audit_data9_rail_coverage.py --output /tmp/data9-coverage
```

Verificar `coverage.json`, `coverage.md` e `unresearched_pairs.csv` e
garantir que a soma de categorias continua 1.380; nenhum retorno/tarifa
foi gerado nem uma viagem foi declarada disponível para setembro–novembro de 2027.
Antes de merge, exigir CI verde e revisão do diff. Não realizar redesign,
ranking automático nem evolução para o motor multicritério neste pacote.

## Continuidade

O inventário é extensível, não uma promessa de 1.380 durações completas.
Priorizar lacunas por destinos da wishlist, facilidade de deslocamento e bases
shortlist após verificar as fontes; separar futura pesquisa de horário/retorno
da simples **conectividade publicada**.
