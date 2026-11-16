# Nossa Europa 2027 — UX 4.1 Favoritas e comparação prática

## Diagnóstico antes da UX 4.1

A UX 4.0 simplificou a entrada com três atividades, mas a principal comparação ainda começava com cinco cartões documentais e exigia abrir três fichas para avaliar cidades distintas. Os 15 destinos ferroviários só possuem uma matriz uniformemente revisada para as cinco bases aprofundadas; as outras 25 cidades têm níveis de pesquisa diferentes. Um contador de rotas pesquisadas **não mede qualidade de mobilidade**.

## Entrega

- **Minhas favoritas** permite escolher/remover até três cidades dentre as 30, sem decisão definitiva. A lista começa vazia ou é recuperada do backup privado existente.
- **Comparação rápida** apresenta colunas de 2–3 cidades e linhas com moradia (amostras, faixa, superfície 30–60 m², capacidade de dois adultos documentada), cobertura ferroviária na mesma cesta, bairros/coworkings/clima quando disponíveis e lacunas.
- **Passeios desejados** compartilha a mesma seleção dos 15 destinos para todas as cidades; exibe somente tempos validados no conjunto comparável das cinco bases, com fonte, tipo de trem quando registrado e distinção de duração só de ida.
- **Síntese objetiva** deriva apenas contagem de evidências, não sorteia cidade vencedora; observa ausência de comparabilidade em imóveis de tamanhos diferentes e em trajetos de outras 25 cidades.
- **Detalhes, fontes e limitações** ficam em seções recolhíveis. Botões abrem ficha da favorita na atividade Explorar uma cidade sem alterar seleção e sem mudar roteiro.
- O estudo anterior de cinco bases continua acessível sob uma seção expansível.

## Persistência e segurança

Reutiliza **o mesmo arquivo de continuidade privada UX 3.6**, adicionando o campo **opcional** `city_favorites`. Backups anteriores sem o campo continuam legíveis e são interpretados como lista vazia. O campo é independente do TripPlan e **não** revisa o plano.

- Quando o proprietário autenticado tem bucket privado configurado, pode clicar em **Salvar favoritas no espaço privado**. Este comando reutiliza `save_private_now`, com validação de geração e tratamento de conflito; a resposta de sucesso só aparece após confirmação de salvamento.
- O arquivo local existente de backup/recuperação também passa a incluir as favoritas, sem modificar o método de restauração do plano.
- Sem armazenamento privado, pode baixar/importar um JSON **somente com a lista de IDs**, limitado a 16 KB, schema estrito; nada é enviado ao GitHub público.
- A escolha persiste em `st.session_state["ux41_favorites"]` quando navega entre atividades. Importação é aplicada antes de criar o widget para não provocar erro de alteração de estado do Streamlit.
- A cidade oficial só muda nos fluxos aprovados existentes; esta funcionalidade **não chama** `planning_session.update_fields`.

## Dados não equivalentes: tratamento obrigatório

As cinco bases da comparação ferroviária compartilhada são Offenburg, Trier, Mulhouse, Strasbourg e Lille. Apenas essas cinco possuem o mesmo levantamento de 15 destinos no modelo `five_base_comparison_model.py`. Para outra cidade, mesmo que haja referências ferroviárias espalhadas em outros conjuntos de dados, a UX 4.1 mostra **"Sem matriz equivalente"** em vez de colocar um zero numérico ou declarar viagem impossível. A UX 4.2 poderá completar esses pares sem criar tempos artificiais.

As faixas de aluguel são apenas os anúncios históricos da cidade. A quantidade de apartamentos comparáveis por área ou de ocupação declarada não confirma preço, disponibilidade, taxas ou adequação a 60 noites em 2027.

Dados ausentes e de infraestrutura remota permanecem desconhecidos. Não há ranking, score, atualização de orçamento ou previsão de custos.

## Arquivos modificados

- `ux41_favorites_model.py`: domínio puro, projeção e arquivo portátil.
- `ux41_favorites_ui.py`: favoritos, comparador, detalhes e persistência.
- `base_research_expanded_ui.py`: favoritos no topo da atividade Comparar cidades.
- `continuity_archive_model.py`: campo opcional e validado.
- `continuity_ui.py`: incluir e restaurar favoritas no backup privado existente.
- `tests/test_ux41_favorites.py`: seleção, limite, equivalência, dados ausentes, compatibilidade de backup e isolamento do plano.

## Próxima evolução sugerida (UX 4.2)

Completar a mesma matriz de 15 destinos para as outras finalistas, validar horários de retorno em fins de semana e fontes de aluguel mobiliado para duas pessoas. É uma melhoria de **pesquisa de dados**, não precisa reabrir o orçamento ou adicionar um quinto menu.

## Verificação

Testes unitários e Streamlit AppTest devem ser executados pelo CI; corrigir todo resultado negativo antes de solicitar aprovação. Inspeção visual real em desktop e mobile ainda precisa ser realizada se houver navegador apropriado; AppTest **não substitui** inspeção visual. Nenhum merge, deploy ou gravação de preferências no GitHub público antes da aprovação.
