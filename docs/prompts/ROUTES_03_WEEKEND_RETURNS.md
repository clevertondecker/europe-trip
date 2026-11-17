# PROMPT 3/7 — Ida, volta e condições de fim de semana

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
Transformar **tempos históricos de ida isolados** em informação útil sobre possibilidades de deslocamento aos sábados/domingos, SEM afirmar bate-volta confirmado para setembro–novembro de 2027 antes de existir horário oficial correspondente.

## Recorte
Após o contrato do PR 1, sem depender do estudo 2A, investigar em primeira onda os pares da cesta comum (Aachen, Baden-Baden, Colônia) frente às bases de referência Mulhouse, Strasbourg, Lille, e, quando houver dados comparáveis, Metz, Liège e Freiburg. Basel, Maastricht e Amsterdam permanecem `exploratory_candidate` enquanto não aprovadas e registradas como base oficial.

## Método com evidências oficiais
1. Ler `data/dq21_weekend_evidence_2026_11.json`, `dq30_mobility_evidence_model.py` e `get_rail_evidence()`. Reusar chaves de rota e contratos definidos no PR 1; não sobrescrever dados de ida anteriores.
2. Para cada observação verificar: operador, estação de origem/chegada, serviço, dia da semana e **data específica da amostra**, última saída e possibilidade de retorno se a fonte documentar, duração, transferências, janelas de conexão, source_url e checked_at.
3. Adotar estados explícitos `historical_outbound_only`, `historical_return_observed`, `operator_frequency_summary`, `2027_date_specific_verified`, `not_researched`, `ambiguous_conflict`. A disponibilidade de trem em 2026 **não** confirma viagem futura. Ausência de um trem em uma consulta **não** prova que nunca exista conexão.
4. Se a fonte fornecer apenas frequência geral, NÃO converter em horários concretos nem declarar `weekend_roundtrip_feasible`. Não calcular orçamento ou duração total de passeio sem a última milha.
5. Preservar observações com divergências, incluindo data/tipo de trem e diferenças entre sábado, domingo e feriados. Documentar frequências que só são válidas em uma estação/linha particular.
6. Distinguir bate-volta possível sob condições verificadas de passeios que demandariam pernoite, sem classificar automaticamente uma cidade-base como melhor.

## Entregas após aprovação
- Dataset aditivo e versionado de **observações verificadas**, com validação de proveniência e plano de integração ao adaptador existente (sem alterar precedência por omissão).
- Matriz por par/dia/condição: referência histórica, retorno pesquisado, ainda pendente, fonte e data.
- Testes para dia/ano, serviço divergente, pernoite não inferido, 2027 não confirmado, ausência de retorno, horários incompatíveis e fonte faltante.

## Aceite
Todos os registros novos possuem link válido e data de observação; resultados incompletos ficam incompletos; nenhum campo `return_2027_verified` vira true sem evidência da data realmente pesquisada. `TripPlan` e comparador atual inalterados.

## Fora de escopo
Reservas, tarifas futuras, otimização, roteiro definitivo, alteração da interface, ranking ou promessa de viabilidade de fim de semana.


## Parecer solicitado ao revisor
Comentários diretamente no PR: P0/P1/P2; contratos/adaptadores que devem ser reutilizados; dados concretos impossíveis de inferir; testes mínimos; ordem de execução/dependências e recomendação de ajuste ou implementação. Nada é executado automaticamente.


## Rastreabilidade da implementação — revisão final 17/11/2026

- PR de implementação separado para revisão: [#119](https://github.com/clevertondecker/europe-trip/pull/119).
- Implementação independente: exigir data concreta no calendário, direção, estação, transferências em ordem, abertura da atração e acesso compatível; duas viagens nunca bastam para afirmar passeio viável.
- Este PR permanece **somente especificação**. Nenhum merge/deploy de implementação está autorizado até revisão do conjunto. Os testes de CI no PR de implementação validam contratos/código, não substituem confirmação de horários, aluguéis e acesso para datas de 2027.
