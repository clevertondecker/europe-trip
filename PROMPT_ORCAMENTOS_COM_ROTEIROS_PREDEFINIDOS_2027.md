# Prompt executado — Cada orçamento com roteiro predefinido e custos transparentes

## Contexto e problema
No Nossa Europa 2027, a projeção global já inclui uma provisão de excursões.
Entretanto, o usuário via o mesmo orçamento sem saber quais passeios pressupostos.
Os perfis Econômico, Equilibrado e Aproveitar ao máximo já geravam destinos
e atrações (2, 4 e 6 destinos propostos, preservando os oficialmente escolhidos),
mas a aba Orçamento não oferecia adoção direta nem detalhamento claro de
quanto da provisão foi comprometido.

## Objetivo implementável
1. Na aba **Orçamento**, exibir três roteiros pré-montados, derivados de
   travel_profile_scenarios.build_profile_scenarios (não dados inventados).
2. Cada perfil mostrar: destinos/atrações, novas inclusões, datas provisórias,
   custos de trens/ingressos conhecidos, provisão existente, saldo nominal,
   custos sem cotação, projeção global e margem do teto atual (60k/70k).
3. Permitir escolher **Usar roteiro** e revisar exatamente todas as inclusões,
   datas e avisos antes de aplicação. Sem aprovação não alterar TripPlan.
4. Ao confirmar, usar approve_profile_scenario + accept_approved_plan com
   atualização de uma única revisão e preservação dos passeios já oficiais;
   redirecionar a Meus passeios, com aviso para salvar online.
5. **Meus passeios** deve exibir provisão mesmo vazio, gastos conhecidos dos
   passeios oficiais, saldo nominal não garantido, pendências e custo por card.
6. Não duplamente contabilizar despesas já previstas; somente custos
   históricos conhecidos acima da provisão elevam a projeção. Explicar
   que um valor global constante não significa passeios gratuitos.
7. Ao trocar base, teto ou hipóteses, reconstruir cenários a partir da situação
   atual. O roteiro não é reservado nem salvo remotamente sem ação explícita.
8. Preservar estruturas e validação de dados existentes, testes e backups.
9. Testar seleção, cancelamento, confirmação, perfil sem pacote oficial,
   variação de teto, não mutação do plano antes do aceite e cálculo da provisão.
10. Validar GitHub Actions e integrar à main somente com CI verde.

## Restrições de transparência
- Roteiros sugeridos não são reservas nem escolhas oficiais até aplicação.
- As tarifas e referências de aluguel foram pesquisadas em 2026; não são
  cotações ao vivo para 2027.
- A provisão inclui excursões genéricas; não há modelagem individual completa
  de refeições, transporte urbano e pernoites extras.
- Não alterar fórmula ou inventar multiplicadores para fazer cada perfil
  necessariamente apresentar preços diferentes.
