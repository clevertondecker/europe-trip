# UX132A — Cobertura documental de pesquisa no app

Atue como Staff Software Engineer e Principal Product Designer (Python/Streamlit). Repositório Nossa Europa 2027.

## Objetivo
Em Explorar → Comparar bases, adicionar a terceira opção “Cobertura dos dados” ao controle Área da pesquisa. Acesso direto mesmo sem wishlist, escopo confirmado ou cidades selecionadas. Área informativa independente da decisão de base, não ranking ou novo comparador.

## Escopo
- Exibir visão geral do universo global: bases, destinos, pares não locais, pares com tempo e cobertura documental.
- Exibir Cidades-base e Destinos com nomes canônicos, cobertura, numerador/denominador, históricos, indicativos, locais e lacunas. Filtro das cinco bases prioritárias e todas as bases; seleção de uma linha para identificar lacunas de tempo, sem editar a pesquisa.
- Reutilizar data24_audit_model.rail_coverage e coverage_counts, a mesma projeção ferroviária do comparador; nenhum dataset manual, nenhuma chamada de rede, nenhuma hipótese de ida/volta ou de 2027. Calcular apenas quando a área é aberta; não usar o relatório Markdown como fonte de dados.
- Seguir estilos e componentes nativos existentes. Não misturar cobertura com qualidade/viabilidade, não ordenar automaticamente como ranking de cidades. 0/0 = não aplicável; excluir pares locais do denominador.
- Preservar CHOICE, SCOPE, DRAFT, wishlist, TripPlan, orçamento, persistência, navegação e handoffs ao alternar áreas. Tratar None no segmented_control.
- Não restaurar o painel legado removido por DATA24A: somente visão documental compacta, sem segunda matriz global concorrente. Detalhes avançados de fontes e filtros ficam em UX132B; atrações, moradia, vida cotidiana, trabalho remoto em UX132C.
- DATA25B #268 independente: usar dados presentes no checkout, sem hardcode de números; verificar atualização automática após integração.

## Aceite
Testes puros para paridade das contagens, local, 0/0, filtro e lacunas; AppTest para entrada sem desejos, troca de área e preservação de escolhas, inclusive escopo confirmado. Garantir navegação e ausência de mutações. Rodar CI no HEAD final; QA visual real quando disponível. Manter draft, sem merge sem autorização.

## Refinamentos após review (27/11/2026)
- Manter a localização em Comparar bases nesta entrega; reavaliar navegação independente após UX132C, sem criar nova página agora.
- Cabeçalho “Cobertura documental”; não apresentar disponibilidade de dados como confiabilidade.
- Detalhe com percentual, barra, numerador/denominador, quantidade de lacunas e tabela de origem/destino e pendência. Não usar valores ilustrativos nem inventar destinos.
- Validar seleção antes de montar o widget após alterar recorte. Cobrir fallback de None, DRAFT durante edição, ida/volta à lista e handoff manual.
- Testar a inclusão de uma referência DATA25 real via overlay controlado: altera os numeradores e lacunas dos dois eixos, preserva denominadores e não grava datasets.
- Medir três projeções consecutivas do catálogo real na CI (UX132_COVERAGE_TIMING: amostras, mediana, máximo), com igualdade de resultados. Registrar duração de projeção em log debug no app. Sem cache novo nem limite de tempo frágil antes de observar os resultados; se necessário, avaliar invalidação por revisão efetiva dos dados. A medição não equivale à latência total de renderização no navegador.
