# Prompt executado — Roteiro padrão do perfil em todas as telas

## Problema reproduzido
Com perfil Econômico, base Mulhouse e teto R$ 70 mil, Meus passeios
mostra 0 destinos, 0 atrações e projeção R$ 72.620. Os passeios já
pré-selecionados pelo algoritmo só aparecem em Simular roteiros /
Orçamento, e o usuário não percebe o roteiro inicial de seu perfil.

## Implementação
1. Criar um único seletor `active_preset` que usa `build_profile_scenarios`
   para identificar a proposta do perfil ativo, respeitando base, teto,
   preferências, câmbio, aluguel, dados de fonte e excursões.
2. **Meus passeios:** mostrar um bloco prioritário "Roteiro pré-definido"
   com destinos, atrações, verba reservada, custos conhecidos,
   pendências, projeção e botão "Usar este roteiro em Meus passeios".
   Mostrar separadamente os passeios confirmados. A lista vazia não
   deve ocultar o roteiro sugerido.
3. Adoção deve ter confirmação com atrações e datas, preservar escolhas
   já confirmadas, invalidar rascunhos obsoletos e produzir somente uma
   revisão de TripPlan. Nunca salvar online sem a ação de proprietário.
4. **Visão geral:** mostrar a mesma proposta e marcadores diferentes
   para passeios confirmados e sugeridos no mapa; deixar claro que não
   há reservas.
5. **Descobrir:** identificar a proposta ativa e distinguir resultados
   de pesquisa de passeios confirmados.
6. **Calendário:** apresentar datas propostas separadas do calendário
   confirmado, sem incluí-las automaticamente.
7. **Orçamento:** identificar explicitamente que os primeiros indicadores
   representam somente escolhas confirmadas; manter os três
   orçamentos completos com roteiros pré-selecionados e aprovação.
8. **Simular roteiros:** preservar comparador e rascunhos, mesmos perfis
   e mesmo algoritmo. Não exigir adesão ao roteiro para consultar.
9. Testar troca de perfil/base, navegação, preview sem mutação,
   cancelamento, aprovação, contagem de passeios e sincronização legado.
10. Preservar fórmulas e o princípio de provisão de excursões, sem
    duplicar gastos nem alegar que cotações de 2027 são verificadas.
11. Integrar à main somente quando GitHub Actions passar.

## Critério funcional
Com TripPlan vazio, a pessoa já vê um roteiro sugerido concreto em
Meus passeios e Visão geral, mas os campos oficiais continuam zero
até a ação explícita de adoção. Todos os rótulos comunicam esse estado.
