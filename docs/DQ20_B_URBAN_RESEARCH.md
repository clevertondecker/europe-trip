# Data Quality 2.0 · PR B — Rotina e qualidade de vida sem notas

## Contratos / dados reaproveitados
\`dq20_urban_life_model.py\` consome \`city_research_packs_model.load_city_packs()\` — não duplica os 12 pacotes (moradia, bairros, coworking e normais climáticas). \`data/dq20_urban_evidence_delta_2026_11.json\` registra **somente referências de mobilidade e trabalho** complementares para Mulhouse, Strasbourg e Freiburg.

As seis dimensões seguem o mesmo contrato: mobilidade sem carro, serviços/rotina, trabalho remoto, segurança com evidência, clima set–nov e lazer/cultura. Não há pontuação, classificação de segurança, equivalência entre bairros nem afirmação de internet no apartamento.

## Achados verificados (16/11/2026)
- **Mulhouse:** Soléa identifica linhas de tram 1/2 a cada 20 minutos no período noturno e última saída da Gare Centrale às 23h33 para tram 1, sujeita a alterações de serviço. Fontes: https://www.solea.info/les-lignes-tram-1-et-2-evoluent-en-soiree-pour-mieux-vous-accompagner e https://www.solea.info/se-deplacer/plans/plans-des-lignes
- **Strasbourg:** CTS publica tram até 00h30, e Hibus noturno em linhas específicas de quinta a sábado. Fonte: https://www.cts-strasbourg.eu/fr/nous-connaitre/notre-reseau/lignes-de-nuit-et-soirees/
- **Freiburg:** VAG informa ônibus e tram 05h30–00h30 normalmente e transporte noturno aos fins de semana selecionados; fonte: https://www.vag-freiburg.de/fahrplan / https://www.vag-freiburg.de/fahrplan/nachtverkehr/mit-bus-und-bahn
- **Freiburg, trabalho remoto:** turismo municipal lista coworkings, mas atendimento noturno e elegibilidade devem ser confirmados antes de concluir adequação ao expediente brasileiro. Fonte: https://visit.freiburg.de/en/info/coworking-and-workation
- Normais set–nov existentes em \`city_research_packs\`: Mulhouse e Strasbourg estão documentadas com período 1991–2020. Freiburg ainda não tem série municipal de mesma metodologia validada. Ausência permanece \`null\`.

## Cenário de horário (nunca uma decisão)
Somente quando o usuário informar um horário no Brasil, \`compare_urban_life(brazil_work_window=(9,18))\` calcula faixas locais ilustrativas: 14–23 na Europa em horário de verão e 13–22 no inverno. O fim de horário de verão pode ocorrer durante a viagem. Horários de coworking e retorno noturno precisam ser avaliados por endereço e data.

## Pesquisa ainda necessária
- Serviços a pé dos endereços **reais** de moradia, acesso noturno à rua/estação, velocidade de internet dentro do apartamento.
- Estatísticas públicas criminais com mesmas definições e território (não substituir por "percepção de segurança").
- Normais de Freiburg com estação e período equivalentes.
- Qualquer avaliação qualitativa é interpretação separada dos fatos verificáveis.

## Testes e limite
\`python -m unittest tests.test_dq20_urban_life -v\`; suíte CI completa. **Sem nova pontuação**, alterações no \`TripPlan\`, ou nova página.
