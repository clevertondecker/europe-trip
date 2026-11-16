# UX 4.2 — Navegação simplificada em Cidades-base

## Problema e objetivo
A navegação anterior empilhava `Visão da cidade/Pesquisa ampliada`, quatro modos do explorador e três atividades de pesquisa. Agora a jornada normal `Explorar → Cidades-base` apresenta um único seletor com **Explorar cidades**, **Comparar favoritas** e **Passeios e conexões**. Os dados, fórmulas e o plano oficial não foram modificados.

## Rastreabilidade

| Função legada | Destino após UX 4.2 | Estado preservado | Verificação |
|---|---|---|---|
| Visão da cidade / Pesquisa ampliada | Explorar cidades | `ux40_selected_city` e `expanded_bases_detail_city` | Smoke AppTest |
| Lista das 30 cidades e filtros | Explorar cidades → Ver todas as candidatas | `ux40_saved_country`, `ux40_saved_finalists`, `ux40_saved_corridor`, `ux40_saved_evidence` | Testes UX 4.0 existentes |
| Ficha: moradia, bairros, clima, trabalho remoto | Explorar cidades | `ux40_selected_city` | Testes de pesquisa existentes |
| Favoritas 2–3 cidades, comparação de rotas de 15 destinos | Comparar favoritas | `ux41_favorites`, `ux41_saved_destinations` | Testes UX 4.1 existentes |
| Comparação aprofundada das cinco bases | Comparar favoritas → Referência histórica | Filtros `five_base_*` | Testes das cinco bases |
| Destinos próximos | Passeios e conexões | `scenario_base_selected` | Testes do explorador |
| Comparar mesmas viagens | Passeios e conexões → Comparar os mesmos passeios | Dados e estado legados | Testes do explorador |
| Uma ou duas bases | Passeios e conexões → Estudar uma ou duas bases | Dados e estado legados | Testes do explorador |
| Backups e seleção exploratória | Ferramentas avançadas e cenários | Planos e cenário legados | Testes de persistência |
| Acesso à navegação anterior | Sidebar → Fontes e ferramentas avançadas | `main_navigation` | Testes UX de compatibilidade |

## Garantias
- O seletor duplo de `Pesquisa ampliada` não aparece na jornada normal.
- A navegação interna existente em `ux_navigation.py` permanece um adaptador compatível.
- A UX 4.1 e o fluxo privado de backups são reutilizados; nenhuma gravação pública.
- `TripPlan`, Drive, GCS, fórmulas financeiras e fontes de mercado não são alterados.
- Preços e tempos ausentes continuam sem valores fabricados.
- Teste visual em navegador real (375/768/1280 px), teclado e GCS autenticado dependem de ambiente autorizado e **não estão comprovados por AppTest**.

## Revisões
**Engenharia:** mudanças localizadas nas camadas de navegação e apresentação, sem novos contratos de domínio. Testar compatibilidade com widgets legados, estados e retornos.

**UX (revisão crítica de critérios, não revisão humana independente):** uma ação por atividade visível; relatórios e controles antigos permanecem recolhidos. Conferir após publicação o tamanho das tabelas e a visibilidade das funções em mobile, especialmente a lista completa sob expansor.

## Validação
`python -m compileall -q .`
`python -m unittest discover -s tests -v`

O CI valida sintaxe, testes e Streamlit AppTest. Validar também a jornada real em navegador antes de afirmar aceite visual.
