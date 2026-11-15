# Pendências de dados — Europa 2027
Última auditoria: 15/11/2026. Não confundir prioridade de pesquisa com decisão aprovada.

| Prioridade | Pendência | Por que importa | Fontes/ação para resolver | Estado |
|---|---|---|---|---|
| P0 | Armazenamento do `TripPlan` em GitHub **público** | Datas e padrões de viagem ficam públicos e podem persistir no histórico | Escolher backend/repositório **privado**, planejar migração e retenção com aprovação explícita | **Não resolvida; mitigação só para campos extras/e-mail** |
| P0 | Autorização do trabalho remoto e cobertura do casal | Afeta elegibilidade, compliance, seguro e risco financeiro | RH/empregador, especialista em trabalho transfronteiriço e fontes oficiais de França/UE | Sem documentos verificados |
| P0 | Cotações completas de hospedagem mobiliada (45–65 dias) | Maior diferença potencial entre Lille, Strasbourg, Mulhouse, Metz, Nancy, Arras, Dijon | Booking mensal, imobiliárias e provedores locais; datas pós-casamento; limpeza, contas, internet, caução | Sem cotações equivalentes de 2027 |
| P0 | Viagem Itália: Salerno × Maiori no período da partida | Transferência de Roma com bagagens, último ônibus/ferry, volta a estação/aeroporto | Trenitalia, SITA Sud, Travelmar; dias exatos; hotéis | Transporte sazonal de 2026, preços incompletos |
| P0 | Todos os custos ainda desconhecidos no orçamento | Risco de parecer que R$72 mil representam o custo final | Passagens, hospedagens, trem normal, ingressos, refeições, seguro, câmbio, contingência | Projeção histórica parcial |
| P1 | Tarifa normal para 2 pessoas (sem Fluo) em cada base × destino | Preço promocional só tem elegibilidade em certas situações | SNCF TER/SBB/DB/CFL/Eurostar para datas; custo cartão e regras acompanhante | Poucas rotas completas |
| P1 | Último trem e volta no fim de semana | Define viabilidade real de bate-voltas | Horário oficial de ida/volta da data real em 2027 | Não confirmado |
| P1 | Tempo porta a porta, bagagens e mudanças de estação | Evita passeios incompatíveis com tempo livre/trabalho | Endereço provável do aluguel, horários locais, caminhada, conexão | Não modelado por completo |
| P1 | Preço/horário dos Alpes, teleféricos e transporte local | Pode custar mais que trem e ser sazonal | Sites oficiais Jungfraujoch/Oeschinensee, SBB e operadores | Não confirmado |
| P1 | Alimentação cotidiana do casal durante trabalho remoto | Não duplicar restaurantes e supermercado | Cesta real 15–20 itens, quantidades casal, refeições fora vs casa | Só pequenas amostras de 2026 |
| P1 | Regras de entrada para ambos e documentação pós-casamento | EU vs non-EU, estadia, seguro e eventuais permissões | Your Europe, autoridades francesas/italianas e consulado | ETIAS era não operacional em 15/11/2026; rever em 2027 |
| P1 | Comparação de bases candidatas Lille/Arras/Dijon/Reims | Ampliam corredores, mas podem elevar moradia/pernoites | Teste com 6–8 passeios fixos, aluguel mobiliado e tempos totais | Somente exploração documental |
| P2 | Pousadas de fim de semana Amsterdam/Bruges/Colônia | Imposto local, noites e alimentação alteram custo total | Booking/operadores, datas exatas e condições de cancelamento | Tarifas mínimas históricas |
| P2 | Padronizar câmbio e arredondamento em todo app | Centavos e versões diferentes de calculadoras | Refatoração com Decimal e testes de invariantes | Score EUR/CHF corrigido; restante em revisão |
| P2 | Teste de import/export de backup contra todo histórico v1 | Evitar perda de dados/migração incompatível | Fixtures anonimizada das versões anteriores e testes offline | Parcialmente coberto |
| P2 | Extração incremental de `app.py` | Reduzir complexidade/coupling | Extrair controllers e modelos com AppTest | Não iniciada nesta fase |

## Pendências específicas — Itália e cinco cidades-base (pesquisa 15/11/2026)

A pesquisa aprofundada de **Offenburg, Trier, Mulhouse, Strasbourg e Lille** está
registrada em `PESQUISA_COMPARATIVA_5_BASES_2027.md`. A coleta é histórica:
há três exemplos de imóvel por base, mas **nenhum total verificável e
elegível de 60 noites em 2027**. Revalidar:

- [ ] **P0 — Hospedagem das cinco bases:** cotar três apartamentos privativos
  para **duas pessoas na mesma janela pós-04/09/2027**, com taxas, limpeza,
  internet, cozinha, duração contratual, depósito e deslocamento até estação.
- [ ] **P1 — Trens das cinco bases:** escolher os passeios de fato desejados,
  verificar **ida e volta no mesmo fim de semana de 2027**, tarifa normal do
  casal, last mile, perda de conexões e pernoites inevitáveis. A matriz
  existente tem 15 destinos comuns, mas não 75 rotas completas.

O prompt de **auditoria da lua de mel italiana** requer investigação de
quatro noites Roma + cinco na Costa Amalfitana, alternativas Salerno,
Maiori, Minori e Amalfi e eventual última noite em Nápoles. Pendências:

- [ ] **P0 — Calendário e voos Itália:** data/hora de chegada FCO,
  saída NAP ou FCO para a próxima base (ainda não decidida), bagagens,
  margem de check-in, e se são 9 ou 10 noites italianas.
- [ ] **P0 — Hotéis e contratos Itália:** cotar quartos para dois nas mesmas
  datas reais, **4 noites em Roma + 5 costa** ou **4+4+1**, com café,
  tributos locais, cancelamento, localização e acesso com malas.
- [ ] **P1 — Itália porta a porta:** Roma FCO→hotel; Roma Termini→Salerno
  (não só duração ferroviária), Salerno→base, base→NAP, táxi/ônibus,
  esperas, horários e custo total do casal.
- [ ] **P1 — Costa sem ferry:** conferir tabela SITA válida para a data de
  setembro–outubro 2027, retorno de Positano/Ravello e alternativa terrestre
  viável se a Travelmar cancelar por vento.
- [ ] **P1 — Capri:** NLG Maiori–Capri teve horários publicados apenas
  até 30/09/2026, enquanto Amalfi–Capri até 03/11/2026.
  Revalidar serviço real em 2027, tempo de conexão, taxa de desembarque,
  volta do dia e alimentação; não pré-aprovar.
- [ ] **P1 — Pompeia:** ingresso oficial publicado para 2026,
  mas transfer ferroviário até o sítio, malas, abertura e volta dependem do
  itinerário; só incluir após escolher entre Pompeia, Capri e descanso.
- [ ] **P1 — Finanças Itália:** não somar a nova amostra de bilhetes a
  `Itália (~10 dias)` (R$12.545 ou R$14.636) e ao bloco separado
  `Passagens e deslocamentos aéreos` sem reconciliação item por item.
  Cotar hospedagem, alimentação, transporte local e imprevistos.
- [ ] **P2 — Reservas Roma:** Coliseu com ingresso por faixa de horário,
  Museus Vaticanos geralmente fechados aos domingos (salvo último domingo
  elegível), Panteão e Basílica com condições para o dia exato de 2027.
- [ ] **P2 — Documentação de evidências:** validar preços publicados contra
  fontes atuais antes de reservar; nenhum resultado da pesquisa
  representa aprovação de roteiro nem disponibilidade para 2027.

O novo painel italiano é **somente leitura e hipóteses manuais**.
Não modifica o documento de decisões oficial no Drive nem o `TripPlan`
canônico. A escolha de uma das três propostas permanece aberta.

## Regras de dados obrigatórias
Toda nova evidência deve ter, quando possível: `source_url`,
`retrieved_at`, `validity_period`, moeda, unidade, número de viajantes,
condição tarifária, qualidade de evidência e data de revisão.

Classificação a usar:
- **Confirmado**: reservado/contratado, comprovante e condições salvas
  sem dados confidenciais no repositório público.
- **Cotado para as datas**: oferta consultada com data específica, não comprada.
- **Referência histórica**: preço/horário anterior à viagem (ex.: 2026).
- **Estimado**: hipótese/extrapolação com método e dados de origem.
- **Desconhecido**: sem referência suficiente; NÃO contabilizar como grátis.

## Próxima reconsulta
SNCF, TER, SBB, DB, CPL/CFL e Eurostar devem ser revisados
quando houver calendário de bilhetes de setembro–novembro de **2027**.
Monitorar também mudanças nas regras oficiais de entrada,
documentos, seguro e autorização de trabalho remoto.

Nenhuma dessas lacunas autoriza escolher silenciosamente cidade-base,
trocar datas ou criar reservas.
