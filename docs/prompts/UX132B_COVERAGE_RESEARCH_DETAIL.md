# UX132B — Cobertura documental: filtros e rastreabilidade

Atue como Staff Software Engineer e Principal Product Designer no Nossa Europa 2027 (Streamlit/Python). Pré-requisito: UX132A #269 integrado.

## Objetivo
Tornar a área existente Explorar → Comparar bases → Cobertura dos dados acionável para planejar pesquisas. Não criar outra página, matriz, editor de dados ou ranking.

## Implementação
- Preservar KPIs globais e navegação. Nos eixos Cidades-base e Destinos, acrescentar busca por nome (sem distinção de acentos), opção apenas com lacunas e ordenação explícita por nome, maior quantidade de lacunas ou menor cobertura. Manter ordem alfabética como padrão. Filtros não alteram denominadores nem números globais; seleção de detalhe deve permanecer válida.
- Substituir a tabela de pendências existente por uma única tabela de conexões no detalhe, com filtro padrão "Sem tempo pesquisado" e opções Histórico, Indicativo, Local e Todas. Mostrar origem → destino e status; mínimo de ida, fonte e data quando documentados. Local não é lacuna ferroviária; sem tempo não é ausência de conexão.
- Permitir consultar uma conexão com referência: fonte correspondente ao mínimo exibido (não confundir fonte histórica e alternativa), observações e ressalvas de estações/variações, sem inferir retorno, tarifa ou 2027. Reusar a projeção canônica DATA24 e rótulos compartilhados; não pesquisar externamente durante rerun nem inventar fontes.
- Preservar UX132A, DRAFT, CHOICE, SCOPE, wishlist, orçamento e TripPlan. Sem dados privados ou escrita de dados. Não adicionar cache antes de medir. Atrações, moradia, vida cotidiana e trabalho remoto permanecem UX132C.

## Aceite
Testes puros para filtros, ordenação, vazios, paridade de categorias, direção, fontes e nova evidência; AppTest para alternar filtros, seleção inválida, exibir referências e voltar à comparação. Medir projeção no catálogo real, validar pipeline no HEAD final e registrar limitações do QA visual. Draft sem merge até autorização específica.
