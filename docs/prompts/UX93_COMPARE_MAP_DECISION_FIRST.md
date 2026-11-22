# UX93 — Comparação e Mapa orientados a decisões

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
Comparar bases apresenta cartões longos com estatísticas, pendências e checkbox antes de uma síntese. O mapa e os comparadores antigos ficam espalhados. É difícil saber por que uma cidade é adequada para os destinos desejados.

## Arquivos
`rec03a_suggestions_ui.py`, `rec03b_handoff_ui.py`, `ux87_inline_base_comparison_ui.py`, `ux503_destination_base_comparison_ui.py`, `ux505_base_comparison_presentation.py`, `ux506_decision_readiness_projection.py`, `map_presentation_ui.py`, `base_research_expanded_ui.py`, `app.py` e testes REC02/REC03.

## Implementação solicitada
1. Confirmar escopo uma vez, reutilizando **CHOICE** e destinos imperdíveis existentes; mostrar resumo de quantos destinos entram na análise e permitir **Editar escopo**.
2. Mostrar primeiro 3–5 candidatas fundamentadas quando houver evidência, com resumo simples de pontos fortes, cobertura dos destinos desejados, lacunas e confiança. Oferecer **Ver todas as cidades (34)** sem inventar ranking.
3. Comparação inline entre selecionadas no **mesmo escopo**; separar tempo de ida, retorno, última milha, custos conhecidos e dados ainda não pesquisados. Uma melhor referência parcial não é vencedora absoluta. Evidências/fontes e pesquisa histórica ficam em detalhamento.
4. Manter comparação manual PREVIOUS/MANUAL_KEYS e estudo histórico em acesso avançado, preservando deep links e handoffs; não oferecer dois fluxos principais concorrentes.
5. Mapa principal com pontos reais e legenda de desejado/incluído/base candidata. Filtros de etapa e abertura de detalhes/foto no contexto; não desenhar rotas/tempos inventados nem criar editor paralelo.

## Testes/aceite
0/1/5/34 bases; escopo vazio e parcial, 2–5 opções, diferentes níveis de evidência, imperdíveis, trocas e retornos; preservação do TripPlan e seleção; mapa responsivo e acessível, sem informação fictícia. Manter AppTests REC02/REC03/UX87/UX88 e validação real em navegador.

## Fora de escopo
Sem ampliar dataset ferroviário, alterar evidências ou custo oficial. Apenas apresentação/read-models.