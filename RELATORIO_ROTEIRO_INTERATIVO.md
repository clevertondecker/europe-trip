# Relatório de implementação — Roteiro interativo Europa 2027

**Pesquisa/implementação:** 14 de novembro de 2026. **Status:** funcionalidades publicadas para validação visual; não há reservas.

## Contexto oficial preservado
- Casamento: 04/09/2027, início da viagem somente depois.
- Dois viajantes, aproximadamente 65–75 dias de viagem, Itália primeiro (~10 dias), depois residência temporária francesa (~55–65 dias), sem carro.
- Bases candidatas da costa: Salerno ou Maiori; bases francesas Mulhouse/Strasbourg/Metz/Nancy ainda abertas.
- 20–30 dias iniciais de férias, incluindo 3–5 dias de instalação na França; depois trabalho remoto. Logística aérea, contrato de apartamento e autorização de trabalho no exterior não comprovados.
- A aba oficial de cronograma continua acessível, sincronizada com Drive quando possível, sem substituição pelo dataset editorial.

## Páginas implementadas
1. Visão geral: quatro momentos, dois mapas regionais de pontos de interesse.
2. Itália: Roma/Costa Amalfitana, alternativas de base Salerno/Maiori, lista de ferries e preços para casal (2026).
3. França e escapadas: mapa de bases e destinos opcionais, filtros de base, TER Carte Fluo, Luxemburgo, Alpes, Oeschinensee.
4. Transportes e custos: escolha de passeios por base, subtotais separados EUR e CHF dos únicos bilhetes com preços publicados, tarifas condicionadas e ausências identificadas. Não converter automaticamente em orçamento da viagem.
5. Cronograma oficial: permanece conectado à fonte do Drive; fallback snapshot já existente.

## Tarifas Travelmar 2026 verificadas
Fonte primária: https://www.travelmar.it/_download/tariffe-2026.pdf
Cronograma amostral: https://www.travelmar.it/_download/orari-travelmar-dal-primo-aprile-2026.pdf
- Salerno–Amalfi: €12/pessoa/trecho, ~35min de navegação; ida e volta duas pessoas = €48, apenas ferry.
- Salerno–Positano: €17/pessoa/trecho, ~70min; ida e volta casal €68.
- Salerno–Maiori: €10/pessoa/trecho, ~30min; transfer de ida do casal €20.
- Maiori–Amalfi: €5/pessoa/trecho, ~15min; ida e volta casal €20.
- Maiori–Positano: €15/pessoa/trecho, cerca de 15+25 minutos DE NAVEGAÇÃO com troca em Amalfi, exclui espera; ida e volta casal €60.
- Maiori–Minori: €3/pessoa/trecho, ~5min; ida e volta casal €12.
**Excluídos do subtotal:** transporte ao píer, esperas, portos não abrangidos, Capri, hotéis, ingressos e alimentação. Horários de 2027 precisam de confirmação. Mar e clima podem cancelar ferries.

## França / Suíça
- SNCF TER: rotas e exemplos de tarifas reduzidas Carte Fluo com URLs no arquivo estruturado. Ex.: Mulhouse–Colmar 18min e €5,40/pessoa/trecho, casal ida/volta €21,60 SOMENTE se elegível ao desconto. Carte Fluo e deslocamentos porta-a-porta não incluídos.
- Oeschinensee: página oficial https://www.oeschinensee.ch/en/tarife-fahrplan/ registra abertura de outono **20/09–07/11/2027**; tarifa publicada do teleférico no outono **2026**, CHF36/adulto ida+volta, CHF72 casal. Não incluir bilhete ferroviário até Kandersteg nem hotel, e não supor que 2027 custará CHF36.
- Luxemburgo e Interlaken: destinos desejados, mas sem transporte total cotado; o app exibe 'a cotar'. Oeschinensee/Interlaken não são classificados como bate-volta simples desde cidade-base francesa.

## Controles de qualidade
- Arquivo dataset `data/itinerary_options_2027.json` e validador `itinerary_planner.py`.
- Testes `tests/test_itinerary_planner.py`: coordenadas, moedas, bilhete de ida e volta, preço do casal, tarifas desconhecidas e desconto condicional.
- Mapa sem linhas de rota falsas. Selecionar uma base na interface NÃO altera a decisão oficial no Drive.
- Não somar outra vez passagens e passeios ao orçamento financeiro, pois as verbas agregadas já existem.

## Próxima pesquisa prioritária
1. Confirmar sequenciamento dos ~10 dias italianos, ingressos Roma, transporte Roma→Salerno/Maiori e Capri.
2. Cotar o trecho Itália → base francesa e volta ao Brasil para dois com bagagens.
3. Para cada base francesa, selecionar 5 passeios desejados, tarifa padrão (sem Carte Fluo), última volta no domingo e tempo porta-a-porta.
4. Alpes: avaliar 1–3 noites adicionais e deslocamentos até Kandersteg/Interlaken, condições sazonais.
5. Somente depois, criar calendário com datas reserváveis e custo total comprovado sem dupla contagem.
