# PROMPT 6/7 — Comparador com evidências ferroviárias e última milha

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
Exibir o resultado dos pacotes anteriores numa comparação **clara e honesta**, sem fazer a UX parecer um sistema de recomendação automática de cidade-base. Reutilizar a UX 5.0.5 como base visual.

## Dependências
Contrato 1 e dados de rotas/última milha com estados e identidades estáveis. **O primeiro incremento do comparador não depende da expansão 2A/2B**; integrar 3/4/5 quando houver dados compatíveis e testados. Preferir trabalhar depois de integrar e testar datasets. Consultar `ux503_destination_base_comparison_ui.py`, `ux503_destination_base_comparison_model.py`, `ux505_base_comparison_presentation.py` e `evidence_query_model.py`; esse PR **não cria pesquisa nova**.

## Experiência proposta
1. Manter título e explicação da UX 5.0.5: **"Como seria visitar nossos destinos a partir de cada cidade?"** Comparação manual de 2 a 5 bases, mesma cesta de desejos, filtro visual apenas em sessão, nenhuma decisão automaticamente escolhida.
2. Na matriz principal por cidade-base × destino, continuar mostrando **tempo histórico de ida entre estações**, fonte e estado. Só mostrar retorno de fim de semana quando houver pesquisa apropriada; não transformar amostra de 2026 em garantia de 2027.
3. Apresentar detalhes opcionais por **estação e atração**: chegada, caminhada/transporte urbano pesquisado e seus limites, com link, data e hora/serviço da pesquisa quando disponível.
4. Explicar visualmente as lacunas por componente: (a) hospedagem→estação de saída; (b) trem estação→estação; (c) estação de chegada→atração; (d) retorno. Nunca interpretar uma lacuna como duração zero.
5. Apresentar indicadores **de cobertura documental**, separados de **qualidade logística**, sem ranking e sem eleger "melhor cidade" porque tem mais fontes.
6. Avaliar responsividade: matriz resumida legível em desktop, cartões/detalhes em mobile, fontes recolhidas; manter modo avançado antigo. Seleções e prioridades não devem ser regravadas ao navegar.

## Arquitetura e testes
- Preferir projeções de apresentação puras, acopladas a adaptadores existentes. Não duplicar roteamento ferroviário nem persistir destinos numa segunda lista.
- Testes de lista vazia, 2–5 bases, mesma cesta, prioridade, dados incompletos, trajeto local, múltiplas estações, divergência, retorno histórico não confirmado, último trecho reutilizado, mudança de seleção, preservação TripPlan e ausência de autosave.
- Inspeção visual desktop/mobile real quando houver ambiente. Não alegar testes visuais sem inspeção.

## Aceite
Usuário entende, em segundos, quais dados são históricos, quais são da caminhada, o que ainda falta pesquisar e por que **nenhuma vencedora automática** está disponível.

## Fora de escopo
Algoritmo de recomendação, otimização, novos destinos, pesquisa ferroviária, alteração da base oficial, gastos calculados sem fontes, UX 5.1, reestruturação global `app.py`.


## Parecer solicitado ao revisor
Comentários diretamente no PR: P0/P1/P2; contratos/adaptadores que devem ser reutilizados; dados concretos impossíveis de inferir; testes mínimos; ordem de execução/dependências e recomendação de ajuste ou implementação. Nada é executado automaticamente.


## Rastreabilidade da implementação — revisão final 17/11/2026

- PR de implementação separado para revisão: [#122](https://github.com/clevertondecker/europe-trip/pull/122).
- Implementação independente: projeção turística/moradia mais associação de trem, retorno, estação e última milha com checagens de direção/data; nenhum total porta a porta sem componentes compatíveis.
- Este PR permanece **somente especificação**. Nenhum merge/deploy de implementação está autorizado até revisão do conjunto. Os testes de CI no PR de implementação validam contratos/código, não substituem confirmação de horários, aluguéis e acesso para datas de 2027.
