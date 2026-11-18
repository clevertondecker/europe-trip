# Prompt executado — DATA 9.1 | DQ 3.2, consistência entre telas e inventário

## Contexto

Repositório `clevertondecker/europe-trip`. DATA 9 (#135) já está na `main` e fornece 29 referências ferroviárias históricas de ida; a tela **Explorar → Comparar** consome `routes7_comparison_projection.decorate_comparison`, mas a tela **Explorar → Passeios → Descoberta ampliada DQ 3.2** ainda usa apenas `get_rail_evidence`, classificando falsamente como "Transporte não pesquisado" destinos já cobertos pelo DATA 9.

## Execução solicitada / critérios de aceite

1. Reutilizar a MESMA projeção `decorate_comparison` na DQ 3.2. Preservar tempos históricos como prioritários e expor referências indicativas em categoria separada, sem prometer horários, tarifas, retorno, acesso local ou 2027.
2. Integrar `attractions_ui.py` com grupo "Referências indicativas de ida", fonte/consulta/confiança, mantendo seletor e status histórico originais; não mudar o `TripPlan` ou a wishlist.
3. Auditar telas: `ux503_destination_base_comparison_ui.py`, `attractions_ui.py`, `base_explorer_ui.py`, `five_base_comparison_ui.py`, `base_research_expanded_ui.py`, `discovery_ui.py`, `ux501_destination_discovery_ui.py`. Distinguir UI com métrica própria (ex.: cenário financeiro de quatro bilhetes) da matriz histórica de ida; NÃO forçar DATA 9 em cálculos não comparáveis.
4. Gerar inventário para todas as 30 cidades-base e todos os destinos canônicos existentes no universo DQ 3.2 (46 no snapshot original). Total de pares esperado se o catálogo estiver inalterado: 30×46=1380. Contar separadamente histórico, indicativo, local e sem tempo. Para cada destino, listar em quantas bases ainda falta tempo e preservar backlog por par.
5. A pesquisa futura será priorizada pelo backlog. Não acrescentar trajetos presumidos, não duplicar fontes nem transformar "desconhecido" em zero. Pendências independentes por par: estações, fonte, data, ida, retorno, tarifa para casal, última milha e data de viagem em 2027.
6. Testes unitários e AppTest cobrindo Mulhouse, Strasbourg, mudanças de seleção, ausência de dados, estado read-only, classificação exclusiva e consistência com a projeção usada em Comparar.
7. Executar CI: `python -m compileall -q .`, `python tools/validate_research_data.py`, `python -m unittest discover -s tests -v`. Também executar `python scripts/audit_data9_rail_coverage.py --output /tmp/data9-coverage`, verificando inventário e documentação.
8. Só realizar merge após CI verde e revisão, preservando histórico. Não fazer deploy manual nem alterar orçamento oficial.

## Arquivos implementados

- `dq32_macro_opportunities_model.py`: enriquecimento conservador por projeção compartilhada, categorias e contagens distintas.
- `attractions_ui.py`: apresentação do novo grupo e proveniência de ida.
- `rail_gap_coverage_audit_model.py`: inventário completo por par, cidade-base e destino, a partir do catálogo atual.
- `scripts/audit_data9_rail_coverage.py`: exportação reproduzível de `inventory.json`, `backlog.json` e `summary.md`.
- `tests/test_data9_dq32_shared_coverage.py`: regressões e AppTest.

## Revisão de outras telas

| Tela | Fonte de transporte | Decisão |
|---|---|---|
| Explorar → Comparar (UX 5.0.3/5.0.5) | `decorate_comparison` | DATA 9 já integrado; manter |
| Explorar → Passeios → DQ 3.2 | `get_rail_evidence` histórico puro | Corrigir para utilizar a mesma projeção |
| Explorar → Cidades-base (ferramentas antigas) | amostra de rotas própria | Não copiar mínimos de ida para previsão completa de passeio/custo |
| Comparar favoritas (cinco bases) | contrato de 15 destinos, bilhetes de referência próprios | Permanecer como análise independente, com suas ressalvas de retorno |
| Pesquisa de moradia e descoberta de lugares | sem cálculo comparável de ida para cada par | Não confundir moradia/POIs com transporte pesquisado |

**Estado temporal:** todas as referências permanecem históricas/indicativas. Nenhuma referência de 2026 garante a viagem após o casamento em setembro de 2027.
