# Prompt executado — Explorador de cidades-base e corredores ferroviários | Nossa Europa 2027

## Missão
Evoluir o Streamlit `clevertondecker/europe-trip` para permitir comparar
cidades-base francesas alternativas **sem modificar o roteiro confirmado**.

Contexto: duas pessoas, casamento em 04/09/2027, viagem Itália → França após
o casamento, parte da França em trabalho remoto, cenários de orçamento 60/70 mil.
Fontes de 2026 são referências e não reservas/cotações para 2027.

## Funcionalidade
1. Preservar `TripPlan` v1 e as quatro bases canônicas: Mulhouse,
   Strasbourg, Metz, Nancy.
2. Acrescentar candidatas **em catálogo separado**: Lille, Arras, Dijon, Reims.
   Não incluir novas bases no `TripPlan.BASES` sem completar a integração
   de hospedagem, atrações, rotas, recomendações, calendário e backups.
3. Alimentar o catálogo com pesquisas rastreáveis de corredores:
   Lille→Bruxelas/Gand/Bruges/Rotterdam/Amsterdam/Colônia/Paris;
   Arras→Lille; Strasbourg→Baden-Baden/Freiburg/Stuttgart;
   Metz→Luxemburgo/Nancy; Dijon→Beaune/Lausanne/Lyon;
   Reims→Champagne/Paris. Identificar lacunas explicitamente.
4. Diferenciar tempo mais rápido de trem **só ida** de duração de ida+volta
   e do tempo porta-a-porta não conhecido. Não inventar trens de retorno.
5. Registrar tarifação `desde` por passageiro e trecho, país, URL, data
   de pesquisa e condições. Preços ausentes são `null`, nunca zero.
   Multiplicação por 4 trechos (2 adultos ida e volta) é **ilustração
   condicional**, não cotação da viagem nem preço garantido.
6. Novo seletor `Explorar bases` na navegação do Roteiro, com:
   - Destinos próximos com bandeiras, fonte e mapa somente de pinos;
   - Comparação das **mesmas viagens** para até 8 bases, exibindo a
     cobertura de tempos e tarifas; sem ranking enganoso de preço parcial;
   - Simulação **Uma ou duas bases**: duas rendas de moradia mobiliada
     introduzidas pelo usuário, número de dias, custo da mudança e
     cauções reembolsáveis destacadas em separado.
7. Reutilizar `scenario_total` para substituir a verba de aluguel
   já contabilizada no orçamento; não somar aluguel de novo.
   Manter as despesas de lazer iguais nos três cenários, até pesquisar
   trajetos completos das propostas. Não lançar cauções como gasto.
8. Apresentar aluguéis históricos €/m² de mercado comum somente como
   referências editoriais, **nunca** transformá-los automaticamente em
   locação mobiliada por dois meses.
9. Propostas/favoritos são salvos somente na sessão, sem gravar no GitHub.
   Uma base canônica só poderá alterar o plano após confirmação explícita.
   Bases novas não podem ser adotadas até completar o suporte arquitetural.
10. Não modificar cenários oficiais, atrações confirmadas, orçamento
    persistido nem a infraestrutura de salvamento.
11. Adicionar atalho a partir da Visão geral, testes unitários e `AppTest`
    cobrindo a navegação, zero de custos não cotados, cálculo de aluguel
    sem dupla contagem, troca explícita de base e isolamento do TripPlan.
12. Validar no GitHub Actions, corrigir regressões e integrar somente
    com checks aprovados. Criar documentação com limitações e pendências.

## Cálculos esperados
- Lille→Amsterdam: referência de 169 min só ida, tarifa `desde €69`/pessoa
  por trecho, total **condicional** €276 para 2 pessoas ida e volta somente
  se os 4 trechos forem encontrados na mesma tarifa mínima.
- Quando Metz não tiver tarifa para os destinos escolhidos, o subtotal
  de tarifa deve ser `None` / `Não cotado`, e não €0.
- Duas bases com 20 dias Lille + 40 Strasbourg, rendas de €1600 e
  €1400 por 30 dias: habitação teórica €2933,33, antes da mudança.
  Cauções €900+€800 = €1700 de caixa potencial, **fora do custo**.
- Mudança de base confirmada atualiza `TripPlan.revision` apenas uma vez.
- Favoritar, comparar, simular e mostrar mapa não alteram a revisão.

## Limitações
A pesquisa é de novembro de 2026: não há valores de aluguel mobiliado
válidos para a viagem, horários de retorno 2027, preços normais de
todas as rotas, ingressos, refeições, hospedagem em outros destinos,
conexões detalhadas nem autorização de trabalho remoto confirmados.
Nenhum total parcial pode ser apresentado como orçamento final.
