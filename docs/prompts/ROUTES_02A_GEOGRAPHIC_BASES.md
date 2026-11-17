# PROMPT 2A/7 — Cidades-base alternativas e cobertura geográfica

> STATUS: **SOMENTE PROPOSTA PARA REVISÃO POR OUTRA IA.** Este PR contém apenas este prompt, não código funcional nem pesquisa nova. Não executar implementação, merge ou deploy antes de avaliação/autorizações explícitas. Depois de aprovado, executar na mesma branch ou conforme coordenação dos agentes.
>
> Projeto: Nossa Europa 2027 — `clevertondecker/europe-trip`. Referência obrigatória: auditoria de cobertura **PR #108** (30 bases, 46 destinos, 94 atrações; 1.380 pares base–destino, dos quais 54 com tempo histórico, 25 parciais, 1.271 não pesquisados e 30 locais). Como #108 pode ainda não estar na main, consultar o PR/branch e não presumir integração.
>
> Antes de programar: sincronizar `main`, verificar PRs concorrentes e CI, ler `AGENTS_COORDINATION.md`, `evidence_query_model.py`, `rail_evidence_unified_model.py`, `ux503_destination_base_comparison_model.py`, os dados de origem e testes. Respeitar ownership: integrador único para arquivos compartilhados. Cada PR deverá ter diff focado, validação de fontes, testes, documentação e CI verde.
>
> **Restrições gerais:** viagem somente APÓS 04/09/2027, sazonalidade set.–nov. 2027; não inventar horários, preços, tempos, rotas, conexões, retornos ou alugueis de 2027. Ausência de dados ≠ ausência de transporte. Tempo estação–estação ≠ porta–porta. Preservar `TripPlan`, base oficial, desejos/prioridades, backups, persistência, navegação legada e a semântica de `get_rail_evidence()`. Nenhum ranking automático por volume de evidências.
>
> **A revisão por outra IA deve entregar:** (a) pontos P0/P1/P2, com explicação; (b) contratos existentes reutilizados; (c) dados/fontes ausentes e como verificar sem pressuposições; (d) riscos de regressão ou duplicação; (e) sugestões de teste e escopo; (f) parecer "apto para implementação / ajustar prompt". NÃO executar código apenas porque este PR foi aberto.


## Objetivo
Testar regiões da Europa **realmente diferentes** antes de aprofundar pesquisa de trens: descobrir se uma base abre acesso a países e destinos novos, mantendo a mesma cesta do wishlist para comparação neutra.

## Candidatas (hipóteses, não finalistas)
- **Referências já cadastradas:** Mulhouse, Strasbourg, Lille.
- **Alternativas já cadastradas:** Metz, Liège, Freiburg im Breisgau.
- **Candidatas novas a validar antes de cadastro como base:** Maastricht (Países Baixos), Basel (Suíça), Amsterdam (Países Baixos). Verificar sua existência atual no registro de 30 bases, independentemente de constarem como *destinos*. Não supor que podem aparecer no seletor enquanto não estiverem cadastradas.
- Possível discussão de 2ª onda: cidades menores perto de grandes nós, desde que tenham fundamentação; não expandir indefinidamente sem justificativa.

## Pesquisa e método
1. Confrontar IDs com `data/base_city_research_expanded_2026_11.json` e `build_destination_discovery()`, documentar claramente `already_registered` ou `exploratory_candidate`; NÃO editar `TripPlan.base_city` nem forçar as novas candidatas no comparador atual.
2. Registrar por região os países e corredores potencialmente acessíveis: Alsácia/Alto Reno; Lorraine–Luxemburgo; Flandres–Bélgica/Países Baixos; Reno Alemanha/Suíça; Holanda. **Não** alegar transporte viável com base apenas na proximidade.
3. Selecionar **uma cesta fixa de destinos ativos** para todas as bases (usar wishlist somente em leitura; em pesquisa estática adotar cenários explícitos e não assumir a lista privada do usuário).
4. Estimar demanda de pesquisa: primeiro 9 bases × 3 destinos demonstrativos Aachen, Baden-Baden, Colônia; depois destinos `must_visit` e `interested` de cenários explícitos. Diferenciar ausência de evidência e observação histórica.
5. Para novas cidades-base, documentar prós/contras **qualitativos e não ranqueados**: acesso ferroviário internacional verificado, moradia mobiliada por 2–3 meses, custo de vida, trabalho remoto, impostos/residência conforme legislação oficial, idioma, mobilidade. **Não presumir que residência de 2 meses na França é compatível com se hospedar em Suíça/Países Baixos**.
6. Não cadastrar novas bases automaticamente; apresentar proposta de registro com impacto nos contratos de `load_research()`, `shortlist` e no seletor UX 5.0.3. Cadastro posterior exige aprovação separada, especialmente para preservar o invariante de 10–12 shortlist do modelo.

## Entrega após aprovação
- Matriz de 9 candidatas com corredor geográfico, estado de cadastro, países potencialmente acessíveis e evidências/pendências verificadas.
- Documento de análise *exploratória* para três não cadastradas; backlinks às fontes oficiais e data. Dados ferroviários somente com observações verificadas.
- Se viável, dataset puramente exploratório separado, não um segundo registro de bases oficial.

## Testes e aceite
Testes de ID e alias, ordenação e cesta fixa, marcação explícita de `new_candidate`, não mutação da shortlist/TripPlan/wishlist, ausência de vencedor, cobertura real versus não pesquisa. Nenhum nome de país/ligação é declarado "acessível em bate-volta" sem evidência e retorno verificados.

## Fora de escopo
Promoção automática de novas bases ao app, expansão da wishlist, novos cálculos, mudanças de UX, decisão final de país de moradia.


## Contrato de revisão
Este é um documento de instruções. O diff desta PR **não implementa a funcionalidade**. Comentários de outra IA devem ser publicados neste PR, preferencialmente organizados por P0/P1/P2 e com mudanças propostas ao texto; só após aceite será autorizada a implementação.
