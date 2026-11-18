# Prompt — DATA 13: atingir 50% de cobertura da matriz ferroviária (um PR)

**Papel:** Senior Python Engineer, Rail Evidence Researcher, Data Quality Engineer e Code Reviewer.

**Repositório:** clevertondecker/europe-trip
**Branch:** feature/data13-directed-rail-coverage-audit

## Objetivo quantitativo

- 30 cidades-base × 46 destinos = 1.380 células, sendo 30 trajetos locais.
- Universo elegível: **1.350 pares ferroviários direcionais** entre cidades diferentes.
- Antes do PR: **227** pares com mínimo histórico ou referência indicativa.
- **Meta: 675 pares / 1.350 = 50%.**
- São necessárias **448 novas células de exibição comprovadas**, e NÃO simplesmente 448 linhas em JSON.
- Cobertura abaixo de 50% deve ser reportada como entrega parcial; não inventar registros para alcançar meta.

## Execução
1. Auditar cada par pela projeção compartilhada `opportunity_overview`, sem recalcular tempos.
2. Pesquisar individualmente pares prioritários de TODAS as bases com operadora:
   SNCF Connect/TER Grand Est, DB, CFL, SNCB e SBB. Quando não houver fonte
   oficial suficiente, usar fontes secundárias reconhecidas, marcadas com baixa confiança.
3. Em cada par: origem e destino canônicos; mínimo **publicado** em minutos;
   URL direta da página que contém a duração; data da consulta, modalidade,
   direção `outbound_only`, confiança consistente e escopo 2026.
4. Registrar apenas pares com fonte que mostre efetivamente o tempo. Não inferir
   duração por distância, geolocalização, inversão da rota ou soma arbitrária de segmentos.
5. Preservar histórico, ROUTES7, DATA9, DATA10, DATA11, DATA12 e adicionar DATA13
   como último fallback, nunca sobrescrevendo informações de maior precedência.
6. Exibir novos registros na DQ3.2 e no comparador existente, mantendo etiquetas
   de mínimo indicativo e procedência.
7. Criar auditoria reproduzível (30 × 46) que publique por base:
   histórico, indicativo, novo no front, desconhecido, local e percentual.
   Testar invariant: histórico + indicativo + desconhecido + local = 46.
8. Se não for possível validar 448 novas referências, manter itens sem tempo
   e informar exatamente quantas faltam. Uma tentativa de pesquisa não é
   evidência de trajeto.
9. Não alterar TripPlan, orçamento, persistência, seleção de destinos ou
   nenhuma decisão D-004. Não afirmar tempo típico, retorno, preço de 2027
   ou viabilidade de bate-volta.

## Testes e aceite
- `python -m compileall -q .`
- `python tools/validate_research_data.py`
- `python tools/audit_data13_coverage.py --json`
- `python -m unittest discover -s tests -v`
- `CI` final verde; comparar SHA do PR.
- Critério 50%: `historical_plus_indicative >= 675`. Se não for atendido,
  PR deve explicitar cobertura parcial e não se declarar concluído.
- Inspeção da DQ3.2 com bases Metz, Nancy, Colmar, Haguenau e Mulhouse.

## Entrega inicial desta execução (parcial)
- Observações direcionais com tempo encontrado em páginas oficiais SNCF Connect.
- Modelo DATA13 validado pelo mesmo contrato rígido do DATA10.
- Fallback compartilhado DQ3.2 e auditoria automática de cobertura.
- **A meta de 50% ainda requer mais pesquisa**, e o PR deve registrar isso.

## Segurança
Sem segredos, sem scraping de sites autenticados, sem algoritmos que misturem
referências com bilhetes de 2027. Links verificáveis por par são obrigatórios.
