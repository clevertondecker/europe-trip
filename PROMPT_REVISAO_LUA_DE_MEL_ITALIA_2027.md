# Prompt executado — Revisão crítica e otimização da lua de mel na Itália | Nossa Europa 2027

## Missão
Executar a revisão de aproximadamente **10 dias da Itália**, mantendo
**Roma e Costa Amalfitana obrigatórias**, com foco em romance,
tranquilidade, custo total, pouco transporte e dados oficiais.

## Contexto imutável
Casamento 04/09/2027; partida somente depois. Dois viajantes.
Itália antes da França. Cenários orçamentários globais para o casal
R$60.000 e R$70.000, incluindo passagens, seguro e reserva.
Base francesa e voo Itália→segunda etapa ainda em aberto.
No Drive, `01_ESTADO_ATUAL` e `03_PENDENCIAS_E_PROXIMOS_PASSOS`
são referências de decisões; NÃO editar nem gravar novas escolhas
sem aprovação expressa.

## Tarefas executadas
1. Ler `main` recente, `RELATORIO_ROTEIRO_INTERATIVO.md`,
   `itinerary_planner.py`, `data/itinerary_options_2027.json`,
   `data/trip.json`, `docs/AUDITORIA_ROTEIRO_2027.md` e
   documentação decisória do Drive.
2. Verificar tarifas e horários em páginas oficiais do
   Coliseu, Vaticano, Panteão, Trenitalia, Italo, SITA Sud,
   Travelmar, NLG, Pompeii Sites e ANM Napoli, separando
   **preços publicados em 2026** de cotações para 2027.
3. Propor três roteiros editorialmente coerentes de
   **10 dias de calendário, 9 noites**:
   - Equilibrado: Roma 4 / Maiori 5;
   - Econômico/logístico: Roma 4 / Salerno 4 / Nápoles 1;
   - Lua de mel/experiência: Roma 4 / Minori 5.
4. Permitir comparar +1 noite (10 noites, **11 dias** no
   roteiro típico) sem mudar o plano canônico.
5. Reorganizar atrações de Roma por proximidade e esforço,
   com horários/reservas e dia de chegada tranquilo.
6. Comparar Salerno, Maiori, Minori e Amalfi com praia,
   clima, romantismo, conexão ferrovia, mala e distância
   ao aeroporto; não supor preços de hotel para 2027.
7. Classificar Capri e Pompeia como opcionais e não sobrepor
   os dois ao descanso; Ravello/Amalfi e Positano em dias
   separados, praia e Minori em dia relaxado.
8. Construir nove etapas logísticas de FCO→hotel até
   NAP→base francesa, com modo, riscos, bagagens, fontes
   e **plano B sem ferry**, nunca inventar porta a porta.
9. Calcular apenas subtotal de **bilhetes históricos
   individualizados**, com unidades por pessoa/trecho ou
   ida e volta e taxas separadas. Voos já estão provisionados
   fora do bloco Itália; não aplicar dupla contagem.
10. Criar simulação **manual** de hotéis/noite, alimentação
    do casal, transporte adicional e atrações. Campo não
    informado fica pendente; caução/voo fora; sem atualização
    da planilha oficial.
11. Integrar em `Roteiro → Itália` e no guia italiano legado
    sem mexer nos pacotes franceses, valores oficiais,
    decisões no Drive nem `TripPlan.schema_version=1`.
12. Registrar em `docs/PENDENCIAS_DADOS_2027.md` as lacunas
    das cinco bases francesas/alemãs e da Itália.
13. Implementar testes unitários e Streamlit AppTest.
14. Criar branch e PR **rascunho**; executar CI.
    **NÃO aprovar, fazer merge na main ou publicar no Streamlit
    antes da aprovação do usuário**, conforme instrução do anexo.

## Critérios de aceite
- 4 Roma + 5 costa = 9 noites / 10 dias, sem contagem errada.
- Roma e Costa obrigatórias em todos os roteiros.
- Preços Travelmar e NLG de 2026 com regras de
  desembarque, sazonalidade e conexão indicadas.
- Ingresso de Panteão €7 e de Pompeia €20
  por adulto conforme publicação de 2026.
- Sem confundir preço de passagem de um trecho de trem
  com custo total porta a porta da viagem do casal.
- Sem classificação falsa de alternativa barata com
  muitas despesas ainda ausentes.
- Novas preferências não alteram roteiro vigente.
- A proposta só está pronta para a main com aprovação
  humana e testes completos aprovados.
