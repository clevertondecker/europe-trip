# Prompt de implementação — Evolução 1: Comparador de cidades-base francesas

## Contexto
Implementar no Streamlit "Nossa Europa 2027", repositório `clevertondecker/europe-trip`, um comparador interativo para Mulhouse, Strasbourg, Metz e Nancy. Casamento 04/09/2027, Itália primeiro e depois base francesa por cerca de 55–65 dias para dois viajantes. A escolha definitiva da cidade está EM ABERTO (decisão D-004 no documento 01_ESTADO_ATUAL).

## Fontes obrigatórias e integridade
1. Arquivo oficial `Europa_2027_COMPLETO_ORGANIZADO.xlsm` no Drive, abas 11 RANK CIDADES, 12 PESOS CIDADES e 13 SCORE CIDADES. Reutilizar seis notas editoriais 0–5 por cidade (J:O) e o conjunto de pesos do perfil original; não inventar scores objetivos.
2. Histórico `Europa_2027_Base_COMPLETA.md`: notas e anúncios são históricos de novembro/2026, NÃO ofertas, reservas ou médias reais para setembro–novembro/2027.
3. Documento `01_ESTADO_ATUAL`: D-004 ainda não decidida. Nunca converter a primeira colocada do ranking em cidade aprovada.
4. Informar origem, época, escopo e limitações de qualquer aluguel mostrado; excluir ofertas inadequadas/indisponíveis e jamais afirmar disponibilidade.
5. Não modificar arquivos oficiais, nem Secrets ou lógica de login ao Drive. A matriz de critérios editorial ficará em arquivo JSON versionado de leitura; o orçamento global da viagem NÃO deve incorporar automaticamente aluguel editorial sem validação.

## Requisitos funcionais
- Adicionar "Comparar cidades" ao menu lateral em estilo A+B (branco/azul, cartões responsivos).
- Mostrar 4 cidades, ranking histórico de referência e tabela comparativa.
- Oferecer sliders 0–100 para os pesos dos seis critérios: atrações/países 25, economia de aluguel 20, transporte interurbano 20, natureza 15, vida urbana 10, mobilidade sem carro 10; normalizar pesos para 100%, com tratamento claro de soma zero.
- Três perfis prontos extraídos da aba 12: Equilibrado; Economia de aluguel; Natureza.
- Recalcular os scores com média ponderada das notas editoriais históricas, exibir pesos reais normalizados, ordenar deterministicamente, permitir comparar duas cidades selecionadas.
- Mostrar aluguel de REFERÊNCIA histórica (envelope aproximado do modelo, em €/mês) e links de exemplos históricos de anúncios apenas como pesquisas, não cotações; nenhuma simulação deve sobrescrever o orçamento global.
- Exibir critérios com detalhes e limitações: internet, home office, contrato para 55–65 dias, contas, caução, aeroportos e acesso real ainda pendentes.
- Aplicar escapes HTML ao exibir conteúdos textuais externos e nunca incluir chave privada.
- Preservar mapa, roteiro, orçamento, pesquisas, sincronização Drive e fallback em snapshot.
- Testes unitários para scores de referência (Mulhouse 4.375, Strasbourg 4.360, Metz 4.190, Nancy 3.935), presets, empate, normalização, soma zero e valores de saída sem modificar originais.

## Validação e entrega
1. Criar módulo puro `city_compare.py`, dados `data/cities_france_2026.json`, testes `tests/test_city_compare.py`.
2. Integrar página no `app.py` e documentação no README.
3. Publicar commits no GitHub sem push no Mac; confirmar HEAD e execução do GitHub Actions.
4. Relatar limitações e pedir validação visual no Streamlit. Não escolher automaticamente a cidade-base e não avançar para outra evolução sem aprovação.
