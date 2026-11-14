# PROMPT — Auditoria financeira e orçamento de estilo de vida | Nossa Europa 2027

## Objetivo
Responder com clareza: "R$60 mil ou R$70 mil para o casal são viáveis?", "Quanto é reserva real?", "Quantas saídas semanais podemos pagar?", "Quais escolhas têm maior impacto no custo?" e "Quais preços ainda precisam ser validados?".

## Fonte de verdade
Usar `Europa_2027_COMPLETO_ORGANIZADO.xlsm`, base de conhecimento oficial e a sincronização já implementada do Drive. Não mudar as planilhas originais sem aprovação. Cenários históricos, para DOIS viajantes e viagem COMPLETA após casamento em 04/09/2027: teto R$60k/65 dias ou R$70k/70 dias, Itália ~10 dias, França 55/60 dias, reservas de emergência incluídas R$4k/R$5k. Simulações não são cotações.

## Regras econômicas
1. Separar passagem, Itália, França (aluguel, supermercado, restaurantes/bares, transporte local, passeios), instalação, seguro/taxas, reserva. Reserva já incluída no total; nunca contá-la duas vezes.
2. Na França, verbas históricas R$60k: aluguel 9650, supermercado 7785, bares/restaurantes 2895, transporte 1029, passeios 2300 = 23659. R$70k: aluguel 10937, supermercado 8878, bares/restaurantes 4954, transporte 1158, passeios 3500 = 29427. Conferir fórmula e ressaltar que orçamento geral e subitens podem ter atualização em tempos diferentes.
3. Simular padrão de saídas: 0–7 por semana, gasto POR CASAL e POR SAÍDA em euros; converter por câmbio hipotético explicitamente informado. Dias na França por cenário 55/60, convertidos em semanas como dias/7; multiplicar para custo projetado. O resultado substitui a verba de bares/restaurantes já incluída, não soma a despesa toda outra vez: delta = estimativa de saídas − verba original.
4. Permitir acréscimos independentes de excursões extras, passagens e aluguel (R$), claramente além das verbas originais.
5. Mostrar teto, total, reserva já comprometida, saldo além da reserva, saldo após simulação, extrapolação do teto, limite de gasto semanal já previsto, e ressalva de que saldo positivo mínimo não significa folga suficiente.
6. Não somar cesta histórica de supermercado aos valores já alocados (risco de dupla contagem). Não apresentar gastos adicionais fictícios como despesa real.
7. Usar exemplos de valores de refeição para casal do Numbeo (Mulhouse 67,50, Strasbourg 62,50, Metz/Nancy 60) como apenas referências colaborativas; simulações são hipóteses do usuário.
8. Status de confiança: cenários condicionais; sem passagem nem apartamento cotados para 2027.
9. Implementar módulo puro + testes (matemática, sem dupla contagem, reserva não disponível, cenário nulo, riscos), painel Streamlit dedicado abaixo do orçamento, documentação no GitHub.
10. Validar CI antes de pedir validação visual e não mudar decisões do Drive automaticamente.
