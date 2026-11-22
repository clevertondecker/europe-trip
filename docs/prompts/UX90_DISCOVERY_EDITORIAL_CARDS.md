# UX90 — Catálogo editorial de destinos

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
Explorar → Descobrir exibe KPIs do catálogo, seleção temporária e textos técnicos antes das fotografias. O usuário precisa chegar rápido às cidades e saber se vale conhecê-las, não apenas ver fotos.

## Arquivos
`app.py`, `ux501_destination_discovery_ui.py`, `ux501_destination_discovery_model.py`, `ux501_destination_photo_service.py`, `destination_photo_assets.py`, `ux47_photo_ui.py`, `ux502_destination_interests_ui.py`, `trip01_supplemental_discovery.py` e testes respectivos.

## Implementação solicitada
1. A primeira área útil será **busca por destino/atração**, filtros por país/experiência e **grade de cartões fotográficos responsivos**; retirar KPIs, seleção temporária UX501 e textos técnicos do topo. Conservar função legada acessível de modo discreto.
2. Cada cartão: foto com crédito/fonte/fallback, cidade + país/região, descrição objetiva de 1–2 linhas, perfil de experiência, **duração de visita apenas se documentada**, até três atrações e ações **Ver detalhes** / **Adicionar à minha lista**.
3. Detalhes dentro do contexto: atrações, fotos adicionais quando disponíveis, duração, passeios próximos, sazonalidade setembro–novembro/2027, tempo/custo de logística somente com fonte; distinguir deslocamento de tempo de visita. Dados ausentes aparecem como pendentes, nunca como zero.
4. Adicionar à lista reutiliza exclusivamente wishlist UX502 (com feedback e prioridade), sem inserir no TripPlan. Voltar de detalhes/lista preserva busca, filtros, página e seleção.
5. Fotos devem preservar autoria/licença/link e preferir arquivos locais ou API confiável; buscar mídia apenas para resultados visíveis e manter cache.

## Testes/aceite
AppTests para 0/1/12/mais destinos, filtros combinados, paginação, feedback de inclusão e persistência UX502; fotos existentes, ausentes e erro de carregamento; mobile/desktop; nenhum custo inventado, nenhum layout quebrado, nenhum efeito colateral no TripPlan. **A tela deve mostrar fotos + por que visitar + atrações antes de informações técnicas.**

## Fora de escopo
Sem alterar algoritmos de recomendação, modelos financeiros ou catálogo de pesquisa. Não criar galeria paralela à tela Descobrir.