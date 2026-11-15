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
