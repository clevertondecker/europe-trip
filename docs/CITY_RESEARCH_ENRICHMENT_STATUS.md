# Enriquecimento de cidades-base — lote 1 · 16/11/2026

## Entregas reproduzíveis

- 30 cidades cadastradas, IDs imutáveis, incluindo 12 finalistas de quatro países (França, Alemanha, Bélgica, Luxemburgo).
- Dataset complementar público `data/city_profiles_enriched.json` com ficha de contexto, intervalo de aluguel *histórico do legado*, lacunas de custo de vida, conectividade e climatologia explícitas como `null` quando não verificadas.
- 45 observações públicas rastreáveis (24 notas de contexto para as finalistas, 16 estatísticas municipais INSEE francesas e cinco registros municipais alemães), cada uma com URL, data, tipo e limitação, obtidas de operador ferroviário ou fonte de turismo/serviço municipal. São notas de contexto e **não** cotações de imóveis, preços ou avaliação de qualidade de vida.
- `city_profiles_model.py`: valida exatamente o mesmo conjunto de IDs do cadastro canônico, impede alterar status de hospedagem verificada e publicar notas de adequação numéricas; compara 2–3 perfis sem fingir custos.
- `docs/CITY_RESEARCH_SOURCE_REGISTRY.md`: adição das 12 fontes locais para reutilização em novos municípios.

## Cobertura verificada e lacunas explícitas

- Fichas de 30/30 cidades: **identidade, país e corredor já cadastrados**.
- Finalistas com duas notas locais para 12/12, mais população municipal oficial para seis finalistas francesas e cinco alemãs, além de dez cidades francesas não finalistas. Os períodos e conceitos de população variam entre países e são exibidos com ressalvas.
- Imóveis mobiliados completos e disponíveis para 56–60 noites em 2027: **0 confirmados**.
- Cesta de supermercado/restaurante comparável para 12 finalistas: **pendente** (o estudo antigo de 4 cidades não supre todas).
- Médias climáticas municipais de setembro/outubro/novembro com período comparável para 30 cidades: **pendente**.
- Bate-voltas completos da cesta de 15 destinos, com retorno e última milha: **pendente**.
- Nota final de cidade: **indisponível**.

**Escopo deste lote:** estrutura auditável + informações municipais iniciais, não declarar enriquecimento pleno das seis dimensões. Prosseguir com pesquisas oficiais estruturadas, cidade por cidade; isso exige coleta substancial de indicadores adicionais. Não relabelar referência genérica INSEE/Destatis/Statbel como dado municipal efetivamente extraído.

## Fontes e direitos

Catálogo inicial PR #55, complementado aqui. Turismo oficial pode ter viés promocional; fontes comerciais com bloqueio contra scraping permanecem consulta complementar. Nenhuma fotografia foi importada/republicada sem autorização identificada. Referências históricas preservadas.

## Revisão A / B

Engenharia de dados: a camada não modifica os registros canônicos nem os valores financeiros, evita duplicar rota e explicita ausência.
Revisão crítica UX (não agente independente): ficha com informações reais antes da matriz é mais compreensível, mas não substituir "Pendente" por zeros. Exigir teste visual real e revisão isolada sobre SHA antes de alegar conclusão de UX.

**Testes:** `tests/test_city_profiles_enriched.py`; suíte geral e CI são gates. Não escrever em GCS, Drive ou dados pessoais.
