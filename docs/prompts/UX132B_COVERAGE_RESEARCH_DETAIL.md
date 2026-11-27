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


## Review adversarial — 27/11/2026

### Findings e decisões
- A projeção canônica preservava a precedência do mínimo, mas UX132B atribuía ressalvas de ROUTES7 ao histórico. Corrigido apenas na apresentação: histórico usa a observação com mesma URL, data, dataset e mínimo; a referência indicativa corroborada é separada, com sua URL de reconsulta, data e ressalvas. Snapshots não reproduzidos não são apresentados como mínimos documentados. Observações adicionais são separadas, incluindo estações e notas próprias. Sem alterações na precedência ou nos datasets.
- O seletor de cidade foi mantido: Streamlit >=1.66 suporta seleção de linha, mas o estado da seleção do dataframe é somente leitura e depende de posições. A persistência por ID e a recuperação após filtros exigiriam sincronização extra. O selectbox é acessível por teclado e mantém a seleção restaurável; não adicionar uma segunda forma de selecionar.
- Busca, ordenação e recorte foram reunidos na mesma linha; filtro de lacunas permanece checkbox. O rótulo canônico já contém duração, então a coluna duplicada foi removida. Datas, ressalvas e outras observações ficam no expander. Aviso distingue cobertura documental de viabilidade.
- O estado de apresentação usa os helpers existentes _restore_widget/_remember e chaves shadow por eixo, incluindo seção, recorte, busca, ordenação, filtro, cidade, status e conexão. Seleção é validada antes da criação do widget; a conexão é vinculada ao contexto da cidade. Recortes vazios não alteram o roteiro nem os indicadores globais.
- A medição aprovada do UX132A #269 (run 45991778758) apresentou mediana 31,4 ms e máximo 31,8 ms para projeção global. Não justifica cache ou indexação adicional. UX132B retém a mesma matriz durante cada execução e percorre os pares uma vez para detalhar a cidade selecionada; os agrupamentos existentes já servem aos totais e não exigem uma segunda estrutura persistente. Diagnóstico mede também detalhe em três execuções. Latência total no navegador não medida.
- UX132C: manter filtros ferroviários específicos da seção; nenhum novo domínio, página, agregação de qualidade ou abstração especulativa nesta entrega.

### Validação
- Testes adicionados: coexistência de evidências históricas e indicativas com URL/data/estações/notas próprias; rejeição de alternativa não corroborada; paridade de categoria/rótulo/mínimo com comparador; preservação de filtros por eixo ao ocultar widgets; seleção inválida e recuperação; navegação real para lista e retorno, edição de escopo e handoff da comparação.
- Pipeline do HEAD revisado é a fonte da validação executável; resultados finais ainda pendentes no momento deste registro. QA visual no navegador ainda não realizado. PR permanece draft, sem autorização para merge.
