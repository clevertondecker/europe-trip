# PROMPT 4/7 — Última milha reutilizável das atrações

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
Pesquisar **uma única vez por estação de chegada e atração** o acesso real (caminhada/transporte urbano) para que múltiplas bases possam reutilizá-lo. O comparador tem 94 atrações canônicas/reconciliadas e 2 referências de acesso ainda sem duração verificada (auditoria #108).

## Fontes e IDs
Inspecionar `ux501_destination_discovery_model.py`, `attractions_model.py`, `dq32_macro_opportunities_model.py`, `dq30_mobility_evidence_model.py`, `data/dq30_mobility_pilot_2026_11.json` e possíveis fontes oficiais de estações, transportes municipais e locais turísticos. Respeitar identidade por ID da atração, cidade, país e estação; conservar sinônimos reconciliados sem criar atrações duplicadas.

## Escopo da primeira onda
Concentrar em Aachen (Catedral), Baden-Baden (Lichtentaler Allee) e Colônia (Catedral), com demais atrações **do catálogo dessas cidades** se houver fontes claras. Não inventar que uma atração ausente do catálogo é automaticamente canônica. A referência de 15 minutos da estação ao Musée Unterlinden/Colmar é um exemplo isolado e não deve ser aplicado a outras atrações nem virar ID fictício.

## Método
1. Criar evidências por `arrival_station_id + attraction_id`: origem exata da caminhada/linha, ponto de acesso oficial, modo, tempo e distância (quando **pesquisados**, não derivados), fonte, data, condições de acessibilidade e ressalvas de último trecho.
2. Escolher estação pela rota realmente observada; não supor que todo trem chega à estação central, e não fundir homônimos.
3. Registrar `station_to_attraction_walk`, `urban_transit`, `unknown`, `local_unknown` e `partial`. Se só houver endereço, manter `duration_min = null`.
4. Reutilizar evidência para diferentes cidades-base que chegam à **mesma estação**; NÃO criar 2.820 tempos distintos, nem somar durações de 2026 e horários futuros não compatíveis.
5. Preservar URLs, autoria/licença de mapas se aplicável, checked_at e etapas; distinguir trecho estação–atração de hospedagem–estação.

## Entregas após aprovação
- Catálogo adicional de acesso por estação/atração com proveniência, documentação de regras de correspondência e lacunas.
- Testes de deduplicação, estação diferente, visita local com acesso desconhecido, fontes sem duração, segurança de identidade, acesso a partir de duas bases reaproveitando o mesmo registro, nulos e nenhum cálculo por linha reta.
- Não modificar a contagem de atrações nem `TripPlan`.

## Aceite
O novo dataset é reaproveitável entre bases e distingue claramente tempos de caminhada/bonde de tempos ferroviários. Todas as durações não nulas são verificadas e vinculadas à fonte apropriada.

## Fora de escopo
Geocodificação automática, roteamento por latitude/longitude, agendamento, mapas interativos novos, tempos porta-a-porta presumidos, cálculo de tarifas.


## Parecer solicitado ao revisor
Comentários diretamente no PR: P0/P1/P2; contratos/adaptadores que devem ser reutilizados; dados concretos impossíveis de inferir; testes mínimos; ordem de execução/dependências e recomendação de ajuste ou implementação. Nada é executado automaticamente.
