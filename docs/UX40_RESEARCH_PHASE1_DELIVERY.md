# Nossa Europa 2027 — UX 4.0, Fase 1 (Pesquisa Ampliada)

## Diagnóstico anterior

A tela começava com três métricas técnicas, um aviso longo, cinco bases dentro de um expander **aberto por padrão** e uma tabela com 30 candidatas; só depois aparecia a escolha de cidade e a coleção integral de anúncios, notas e rotas. O usuário precisava ler o relatório antes de encontrar a ação principal. O controle de filtro de 15 destinos e a simulação hipotética existentes não podiam ser removidos.

## Arquitetura implementada

**Entrada existente:** Explorar → Cidades-base → Pesquisa ampliada. As quatro áreas de navegação principais e `app.py` / `ux_navigation.py` não foram alterados.

**Controle contextual** `ux40_research_activity`, com três atividades:

1. **Comparar cidades** (padrão): cartões compactos de Offenburg, Trier, Mulhouse, Strasbourg e Lille, derivados de `base_comparison()` e `housing_sample()`. Cada cartão indica cidade, país, amostra de imóveis 2026, quantidade dentro de 30–60 m², rotas de ida com tempo documentado, situação da pesquisa e botão "Abrir detalhes". A tabela completa das cinco bases, seleção original de 15 destinos, anúncios, rotas, avisos e simulação financeira manual ficam preservados num expander **fechado por padrão**, sem eliminar seus controles nem recalcular valores.
2. **Explorar uma cidade**: selectbox de 30 cidades, resumo e métricas, expansão por moradia, trens/passeios, vida cotidiana/bairros/clima, fontes e pendências técnicas. Botão "Voltar à comparação". Selecionar uma cidade nessa tela **não altera** `scenario_base_selected` ou `TripPlan`. A seleção é armazenada apenas na chave `expanded_bases_detail_city`.
3. **Todas as candidatas**: filtro de país, finalistas, corredor e evidências de moradia já existentes. Tabela de 30 registros, com ação para abrir ficha sem mudar roteiro.

**Aviso geral**: seção única "O que ainda não podemos confirmar" com hospedagens 2027, ida versus volta, falta de indicadores comparáveis e fontes; avisos pontuais de preços/fontes permanecem em seus contextos. A quantidade de pesquisas **não** é nota de qualidade ou ranking.

## Estado e navegação

- Chaves locais: `ux40_research_activity`, `ux40_open_<city_id>`, `ux40_back_compare`, `ux40_corridor_filter`, `ux40_evidence_filter`, `ux40_list_selected`, `ux40_list_open`.
- Estado persistente espelhado: `ux40_selected_city`, `ux40_saved_country`, `ux40_saved_finalists`, `ux40_saved_corridor`, `ux40_saved_evidence`, `ux40_saved_five_destinations` e `ux40_saved_five_detail`, para recuperar widgets quando Streamlit remove uma atividade do DOM.\n- Chaves legadas preservadas: `expanded_bases_detail_city`, `expanded_bases_country_filter`, `expanded_bases_only_shortlisted`, `five_base_detail`, `five_base_destinations`, `five_base_show_unknown` e `five_base_manual_*`.
- `base_explorer_ui.py`, `five_base_comparison_model.py`, `base_research_expanded_model.py` e fórmulas financeiras continuam intactos.

## Antes / depois

| Antes | Depois |
|---|---|
| Longo relatório inicialmente visível | Ação "Comparar cidades" com cartões breves no topo |
| Cinco bases escondidas num relatório denso | Cinco bases visíveis e botões para seus detalhes |
| Filtros e tabela de 30 cidades sempre antes da análise individual | Lista de 30 candidatas disponível sob atividade própria |
| Anúncios e trens individuais exibidos em sequência | Dados técnicos e fontes em expansores sob demanda |
| Avisos gerais repetidos no fluxo inicial | Metodologia geral num único expander, com limites pontuais preservados |

## Segurança, cobertura e qualidade

- **Somente UX/presentação**: nenhum dataset alterado, nenhuma pesquisa refeita, orçamento, cotações, pesos, fórmula ou nota nova.
- **Sem alterações** no `TripPlan`, GCS, Drive, dados privados, datas, cotações ou roteiros.
- Faltam reservas efetivamente confirmadas para 2027, idas/voltas ferroviárias e cestas de custos comparáveis; a nova organização não muda esses fatos.
- Testes novos: `tests/test_ux40_research_navigation.py`, cobrindo cartões com dados derivados, contagens e filtros, transição botão→ficha→voltar, persistência e `TripPlan`. Também executar toda a suíte antiga com CI.
- Inspeção visual real em 375/768/1280px e revisão UX verdadeiramente independente **não foram realizadas**. AppTest não equivale a navegador.

## Fase seguinte sugerida

Usar o aplicativo com cinco bases e duas ou três trocas de atividade; corrigir somente regressões evidenciadas por navegação real, sem iniciar novas features desnecessárias. **Não publicar nem mesclar antes de aprovação explícita.**

## Ajustes após a primeira execução de CI

O primeiro CI detectou dois comportamentos esperados da nova navegação: o teste legado ainda buscava filtros na tela inicial e Streamlit descartava estados de widgets de atividades desmontadas. Adaptado o teste legado ao fluxo contextual e criado espelhamento permanente das seleções (incluindo os 15 destinos) em `st.session_state`. `five_base_comparison_ui.py` muda apenas callbacks de estado dos widgets, não sua lógica de domínio.
