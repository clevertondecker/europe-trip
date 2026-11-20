# PROMPT DE IMPLEMENTAÇÃO — UX 6.2

**Situação:** apenas especificação para revisão; **não implementado**.
**Prioridade:** P0
**Dependência:** Implementar após UX 6.1; esta branch foi criada de main, reconciliar com o PR anterior antes de codificar.

## Papel do agente
Atue como Staff Software Engineer, Senior Python/Streamlit Engineer, UX/Product Engineer e Data Integrity Reviewer.

## Objetivo
Transformar o cartão de um destino desejado em um fluxo único 'Conhecer atrações → Selecionar (1 a 5) → Adicionar ao roteiro', sem segundo editor nem inclusão automática.

## O que implementar
1. No destino exibido em Meu planejamento (UX 6.1), fornecer ação contextual **Escolher atrações** que abre o editor canônico atual com o destino pré-selecionado e volta ao ponto de origem.
2. Reutilizar ux55_visual_outing_ui.py para descoberta detalhada: imagem licenciada e fallback, descrição, duração editorial, preço por pessoa e modalidade, ticket.per, ticket.validity, ticket.notes, moeda, fontes, ressalvas de disponibilidade; nunca exibir custo desconhecido como zero. Especial atenção a adult_return (ida + volta).
3. Preservar a lógica de seleção com flow_pending_attractions e **commit_outing() como único ponto de confirmação**. 1 a 5 atrações por passeio. Não duplicar estado ou persistência, não criar um plano paralelo.
4. Resolver **de forma explícita e testada** o problema dos destinos suplementares (Obernai e Lucerna): aparecem no catálogo de descoberta mas não no catálogo tipado do TripPlan. Desenhar uma integração/camadas de adaptação com IDs estáveis e validação de dados, sem sobrescrever arquivos ou snapshots históricos (30×46 ferroviário). Se alguma promoção canônica exigir migração de contrato, separar e documentar antes de realizar. Não habilitar botão que só falha no commit.
5. Ao confirmar, apresentar o passeio como 'No meu roteiro' sem data; mudar para 'Organizado' apenas depois de período ou data. Conservar o interesse original e marcar 'Já incluído no roteiro' na projeção.
6. Edição deve usar os mesmos componentes e o mesmo commit; remoção confirmada apenas do roteiro, sem apagar lista desejada.
7. Itália: não regredir proposta Roma/Costa Amalfitana, edição e diferença de etapa. Não associar informações de transporte francês à Itália.
8. O retorno de Explorar/Comparar ao editor deve preservar filtros, busca, destino e página; suporte à mudança de etapas, sem widget keys órfãs.

## Pontos atuais de integração
- itinerary_flow_ui.py: _render_add, _edit_destination e commit_outing
- ux55_visual_outing_ui.py, attractions_model.py e itinerary_flow_model.py
- ux501_destination_discovery_ui.py e trip01_supplemental_discovery.py
- ux45_navigation_context.py, ux502_destination_interests_model.py
- data/attractions_2027.json, data/trip01_supplemental_destinations_2027.json
- continuity_archive_model.py para compatibilidade de backups

## Critérios de aceite e testes
- End-to-end: selecionar Obernai na wishlist → ver atrações reais e fontes → escolher 1 a 5 → confirmar → visualizar no TripPlan → salvar/exportar/recarregar → editar/remover, sem perda de IDs.
- Idem com uma cidade já canônica como Colmar; teste negativo para destino sem atrações compatíveis, IDs falsos ou mais de 5.
- O mesmo passeio não é adicionado duas vezes; reabrir mantém seleção e período; alternar Itália/França ou destino não vaza draft.
- Passagem para 'A organizar' / 'No meu roteiro' é consistente; dados de trem ou preços desconhecidos continuam pendentes.
- Não mexer em evidência ferroviária histórica apenas para satisfazer testes ou criar falsa cobertura.
- CI completo e testes Streamlit de retorno de navegação, controles, salvamento e segurança da operação.

## Contexto e regras obrigatórias
Repositório: https://github.com/clevertondecker/europe-trip
Produto: Nossa Europa 2027 (Streamlit/Python), lua de mel na Itália + temporada europeia.
Este PR foi aberto **somente com este prompt**, para review do escopo. Ainda não há implementação funcional. Após aprovação explícita, implementar **nesta branch** e executar testes/CI. Não fazer merge de PR apenas documental.
- TripPlan continua a única fonte autoritativa de passeios confirmados no plano; preferências e pesquisas não são reservas.
- Preservar IDs existentes, compatibilidade de dados/arquivos, isolamento de fontes, fluxos de autenticação, regressões e segurança.
- Sem inventar custos, trens, horários, disponibilidade de 2027, fotos/licenças ou estado de decisão.
- Evitar novos editores paralelos, duplicação de estado de Streamlit e alterações não solicitadas no planejamento oficial.
- Verificar os contratos e os testes existentes antes de editar; adicionar testes de domínio + AppTest; testar troca de etapa Itália/França, restauração, navegação e histórico onde aplicável.
- Rever a branch contra main antes de implementar, pois estes cinco PRs são independentes e poderão ser executados sequencialmente.
- Entregar implementação + explicação da UX + testes + riscos e limitações. Não fazer merge até revisão e autorização posteriores.
