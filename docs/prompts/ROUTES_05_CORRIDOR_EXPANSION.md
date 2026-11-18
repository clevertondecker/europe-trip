# PROMPT 5/7 — Expansão das pesquisas por corredores ferroviários

> **STATUS: PROMPT PARA REVISÃO POR OUTRA IA — NÃO IMPLEMENTADO.** Este PR draft contém apenas esta especificação. Não começar a modificar código, datasets, produção ou persistência antes de aprovação do escopo. Não fazer merge ou deploy neste estágio.
>
> Repositório: `clevertondecker/europe-trip`. Auditoria de apoio: **PR #108** (30 bases × 46 destinos = 1.380 combinações; 94 atrações; somente 54 idas históricas pesquisadas; nenhuma viagem porta-a-porta completa). #108 está/estava em revisão: consultar PR/branch antes de assumir integração à `main`.
>
> Preparação: consultar a `main` e PRs abertos, CI, `AGENTS_COORDINATION.md`, contratos ARCH/UX, `evidence_query_model.get_rail_evidence()`, `rail_evidence_unified_model.py`, `ux503_destination_base_comparison_model.py`, e todos os dados afetados. Propor interfaces e diffs pequenos; somente o integrador altera módulos compartilhados.
>
> Guardrails: viagem após **04/09/2027**, provável janela setembro–novembro/2027. Não inventar horários/tarifas/retornos de 2027, não calcular trechos por distância geográfica, não inferir ausência de conexão a partir de pesquisa ausente, não transformar tempo de trem entre estações em tempo até a atração, não criar vencedor automático. TripPlan, escolhas oficiais, desejos e backups continuam autoritativos e intactos.
>
> Revisão externa requerida: registrar P0/P1/P2, identificar compatibilidade e ownership dos módulos, fontes auditáveis, ambiguidades de data/status, impactos sobre modelos legados e cenário de testes; recomendar "apto" ou "rever prompt". Nenhuma implementação é autorizada pela abertura deste PR.


## Objetivo
Ampliar a cobertura ferroviária com **qualidade e reutilização**, não transformar 1.271 pares sem evidência em milhares de tempos especulativos. Priorizar desejos reais e diversidade de países.

## Dependências
Contratos do PR 1; **piloto de cesta pública e fixa com cidades-base/destinos já cadastrados NÃO depende dos estudos 2A e 2B**; usar estrutura de retorno (3) e última milha (4) quando implementadas. Após validar o piloto, o estudo 2A e as descobertas 2B poderão orientar a expansão. A auditoria #108 define o baseline. Garantir base fixa de comparação antes de comparar alternativas.

## Lotes propostos (pesquisa, não rankings)
- **A: Alto Reno/Alsácia:** Mulhouse, Strasbourg, Freiburg, Basel (Basel como nova candidata se não cadastrada); conexões com destinos já registrados em França, Alemanha e Suíça.
- **B: Lorraine/Luxemburgo/Alemanha:** Metz, Liège (como conexão de corredor), Luxemburgo e arredores; validar operadores e estações.
- **C: Norte França/Bélgica/Países Baixos:** Lille, Liège, Maastricht e Amsterdam (novas candidatas onde não constam como base), Bruxelas, Bruges, Aachen e outros destinos registrados.
- **D: longa distância:** executar *apenas* se houver interesse explícito e fontes consistentes; diferenciar trem de alta velocidade, regional e viagens com pernoite.

## Orçamento de pesquisa e escala
Cada lote de implementação futuro deve focar cerca de **10–25 pares novos** com fonte verificável, não todo o produto cartesiano. Selecionar preferencialmente destinos `must_visit` e `interested`; quando o usuário não disponibilizar seus dados privados, usar uma cesta demonstrativa declarada. Informar explicitamente quais 46 destinos continuam sem pesquisa em cada base.
Evitar pesquisa duplicada por direção/alias, mas **não inferir simetria**: A→B não comprova B→A, e uma estação específica não representa todos os centros urbanos.

## Procedimento
1. Para cada lote conferir `get_rail_evidence()` e resultados do PR #108 antes de nova consulta.
2. Pesquisar primeiro horários e referências de operadoras oficiais (SNCF Connect, Deutsche Bahn, SNCB/NMBS, NS International, SBB/CFL conforme corredor). Fonte deve corresponder ao par/serviço, não apenas à homepage.
3. Registrar operador, estações, amostra de data, tempo histórico, típico apenas quando de fato disponível/comparável, transferências, janela de validade, divergências e links.
4. Não declarar "roteiro viável", "melhor base", "mais países acessíveis" ou "trajeto indisponível" sem evidência específica; não atribuir tarifas de 2027.
5. Preservar histórico e diferenças de fonte, e documentar impacto de adicionarmos novas bases sem forçar atualização da lista oficial.

## Entregas após aprovação
Datasets por corredor/lote com validação, proveniência, CSV de cobertura antes/depois e pendências; documentação por lote. Testes de alias, conflitos, direção, fonte/date/operador, dados incompletos e não alteração do planejamento.

## Aceite
Cada registro não nulo é auditável. Cobertura medida **separadamente** de qualidade logística. Sem criação automática de ranking, sem expansão não aprovada de bases e sem falsa precisão.

## Fora de escopo
Pesquisa de todos os pares, alteração do comparador visual, geração de reservas ou itinerário automático.


## Parecer solicitado ao revisor
Comentários diretamente no PR: P0/P1/P2; contratos/adaptadores que devem ser reutilizados; dados concretos impossíveis de inferir; testes mínimos; ordem de execução/dependências e recomendação de ajuste ou implementação. Nada é executado automaticamente.


## Rastreabilidade da implementação — revisão final 17/11/2026

- PR de implementação separado para revisão: [#121](https://github.com/clevertondecker/europe-trip/pull/121).
- Implementação independente: iniciar piloto fixo público 3 bases × 3 destinos cadastrados; não depende do estudo #110/#111. Referências de páginas de operadores sem duração não confirmam horário, retorno ou 2027.
- Este PR permanece **somente especificação**. Nenhum merge/deploy de implementação está autorizado até revisão do conjunto. Os testes de CI no PR de implementação validam contratos/código, não substituem confirmação de horários, aluguéis e acesso para datas de 2027.
