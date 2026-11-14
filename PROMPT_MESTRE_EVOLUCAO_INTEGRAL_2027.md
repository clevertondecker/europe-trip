# PROMPT MESTRE — Evolução integral Nossa Europa 2027

## Missão e autorização
Implementar em sequência, sem aguardar aprovações intermediárias, as cinco fases acordadas: (1) integridade/arquitetura dos dados; (2) simulação financeira integrada; (3) roteiro e mapas; (4) decisão de cidade-base; (5) acompanhamento e UX. Publicar no GitHub usando o conector (sem push do Mac), executar testes de regressão a cada fase e informar o que não foi possível verificar. NÃO alterar a fonte oficial Drive, nenhuma reserva, pagamento, permissão, segredo ou decisão D-004.

## Premissas
Casal de duas pessoas, casamento 04/09/2027; partida depois; Itália primeiro (~10 dias), base francesa ~55–65 dias; viagem ~65–75 dias, férias iniciais 20–30 dias, home office a validar; transporte público sem carro. Orçamento total do casal R$60k ou R$70k, com reserva emergencial incluída. Bases candidatas Mulhouse, Strasbourg, Metz, Nancy. Preferência por experiência de viagem e design A+B moderno, branco/azul/teal.

## Fase 1 — dados, governança e arquitetura
- Unificar catálogos de mapa e itinerário preservando IDs diferentes e proveniência; incluir todos os destinos sem inventar rotas.
- Corrigir filtros vazios: nenhuma opção marcada = resultado vazio.
- Em todos os números, distinguir histórico/editorial, preço publicado, cotação, estimativa, data de coleta, validade e número de viajantes.
- Financeiro: valor e subcategorias devem vir do cenário sincronizado do Drive quando disponíveis; fallback histórico rotulado se não. Verificar reconciliação total/parcelas e nunca usar subrubricas antigas como 'live'.
- Testes automatizados para mapeamento, unicidade, parsing, fallback, preços e filtro.
- Separar lógica de dados e componentes em módulos sem reescrever inadvertidamente o app inteiro.

## Fase 2 — orçamento integrado
- Um único simulador, combinando cena de R$60k/R$70k, cidade-base hipotética, preço de aluguel alternativo (ou acréscimo à verba), duração, câmbio, saídas/semana/custo por casal, extras de voos, passeios e transporte.
- Cada nova despesa **substitui** verba correspondente ou adiciona apenas um DELTA identificado, nunca soma a categoria já incluída novamente.
- Mostrar total atualizado, margem além da reserva protegida já contabilizada, diferença para teto, percentual e status (estourado/apertado/com folga condicional).
- Mostrar cenários Econômico, Equilibrado, Ativo como hipóteses de comportamento, nunca preços verificados.
- Manter dados originais do Drive inalterados.

## Fase 3 — roteiro e mapa
- Centralizar destinos, manter Itália→França, comparar bases italianas e francesas sem aprová-las; mapas Itália/França a partir do mesmo catálogo; visualizar conexões somente com origem/destino conhecidos e preço/tempo de referência.
- Calendário ilustrativo por dia a partir de saída hipotética >04/09/2027, preservar datas de férias e trabalho remoto; duração consistente com cenário e Itália ~10 dias.
- Seleção de passeios com custo de bilhete por casal, separar CHF/EUR e tarifas condicionais; registrar desconhecidos; nunca tratar trem de estação a estação como percurso porta-a-porta.
- Custo agregado de excursões serve para explicar verba já prevista, sem dupla contagem nem reserva.

## Fase 4 — comparação de cidades
- Conectar pontuação histórica e amostra de mercado às mesmas fichas, incluindo nível de confiabilidade, aluguel como referência não-confirmada e lacunas por cidade.
- Apresentar cenários de aluguel por cidade apenas como hipóteses editáveis, nunca oferta 2027. Permitir levar uma hipótese ao simulador financeiro sem alterar D-004.
- Adicionar trilha para novas cidades seguindo 8 gates do arquivo de auditoria, sem notas inventadas.

## Fase 5 — pesquisas, design e desempenho
- Página de pesquisas: agrupamento por P0–P3, filtros de situação e vínculo com fonte/decisão. Nunca permitir alteração do Drive sem autorização de escrita.
- Home: progresso real de pesquisa, indicadores de lacunas, atalhos para orçamento, roteiro e decisões; não inventar data de compra/reserva.
- UX: reduzir botões repetidos de fonte, usar componentes visuais consistentes, responsividade, controle de estado dos seletores, avisos concisos de dados datados.
- Ajustar CSS legado e adicionar testes de UI/contratos de dados.

## Qualidade e limites
- Fonte única de verdade de decisões/tarefas/orçamento: documentos/abas Drive já conectados com snapshot explícito. Pesquisa histórica GitHub versionada é estática até novo commit.
- Para cada fase: código, testes, GitHub Actions verde antes de avançar.
- Fontes de preço sem datas de 2027 não se tornam preço 'real'. Ausência de conexão a serviços de rota impede tempos porta-a-porta confirmados, não inventar.
- Entrega final com links de commits/testes e pendências honestas. Não anunciar funcionamento no navegador sem conferência real.
