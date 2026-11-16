# Data Quality 2.0 · PR D — Integração independente em Comparar favoritas

## Dependências explícitas
- **PR A (#67)**: \`dq20_weekend_routes_model.route_matrix\`, \`combined_brussels_bruges\`, \`illustrative_weekends\`.
- **PR B (#68)**: \`dq20_urban_life_model.compare_urban_life\`.
- **PR C (#69)**: \`dq20_trip_logistics_model.compare_airport_access\`.
- Este PR **não duplica os arquivos das pesquisas**, não troca a cesta atual da UX 4.1 e não altera o \`TripPlan\`. Sem os três PRs integrados, o painel mostra explicitamente que a pesquisa está em revisão, sem lançar exceção.

## Interface
\`ux41_favorites_ui.py\` inclui uma seção recolhível "**Pesquisa aprofundada: passeios, rotina e logística (piloto)**" para qualquer duas ou três entre Mulhouse/Strasbourg/Freiburg. Ela contém as quatro perguntas:

1. Acessibilidade do mesmo conjunto de cinco destinos por base, mínimo histórico versus média de outra amostra, não equivalendo a fim de semana confirmado.
2. Hipótese de fins de semana com descanso e agrupamento Bruxelas–Bruges, sem total de transporte inventado.
3. Mobilidade urbana, clima, coworking e horário brasileiro opcional (não predefinido).
4. Aeroportos com ligações publicadas e ausência de voos ou tarifas 2027.
5. Lacunas críticas e fontes sob demanda.

A UX 4.4 financeira permanece intacta. Não existe nota 0–100, ranking ou vencedor.

## Testes
- \`tests/test_dq20_comparison_integration.py\` verifica fallback quando os PRs-base ainda estão independentes, guarda o TripPlan e testa integração completa quando os módulos estiverem disponíveis.
- \`python -m compileall -q .\`, \`python -m unittest discover -s tests -v\`.
- Validação visual no Streamlit não é comprovada por AppTest. A inspeção precisa ocorrer após autorização do usuário para publicação.

## Merge e publicação
**Bloqueados até aprovação explícita**. Ordem de integração sugerida #67 → #68 → #69 → #70, CI a cada etapa. Não alterar Google Drive, planos públicos ou autorizações privadas.
