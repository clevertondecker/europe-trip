# PROMPT — Planejador interativo de roteiro Europa 2027

## Contexto e fonte oficial
Casamento 04/09/2027, saída depois; casal de dois; Itália primeiro (~10 dias: Roma + Costa Amalfitana); depois base francesa por ~55–65 dias; instalação por 3–5 dias, férias iniciais 20–30 dias, e então home office. França-base ainda não decidida (Mulhouse, Strasbourg, Metz, Nancy); sem carro. Nenhuma reserva confirmada. R$60k e R$70k são tetos da viagem inteira e passeios já têm verba histórica na rubrica França. Manter sincronização com Drive, fonte de decisões e roteiro da aba 04, e status do plano.

## Fontes verificáveis
- Travelmar tarifas 2026 https://www.travelmar.it/_download/tariffe-2026.pdf e cronograma https://www.travelmar.it/_download/orari-travelmar-dal-primo-aprile-2026.pdf
- SNCF TER Grand Est: URLs por rota já registradas em data/city_market_observations_2026.json, com descontos Carte Fluo condicionais.
- Oeschinensee temporada e tarifas https://www.oeschinensee.ch/en/tarife-fahrplan/ (set/2027 - 07/nov/2027 com operação sazonal prevista, tarifas 2026).
- Base e decisões do Google Drive; projetar somente informações efetivamente sustentadas, separar hipótese de serviço comprovado para a data.

## Entrega de produto
1. Criar dataset versionado com destinos (coordenadas para mapa), categorias por etapa, sugestões de duração, transportes observados, preço em EUR/CHF por pessoa e tipo de trajeto, validade, fonte individual e ressalvas.
2. Mapas separados Itália e França, com filtros e marcadores dos destinos, incluindo candidatos não escolhidos; sem traçar falsa rota fechada.
3. Nova página Roteiro com tabs "Visão geral", "Itália", "França & escapadas", "Deslocamentos & custos" e "Cronograma oficial"; manter cronograma do Drive visível, não substituí-lo.
4. França: selecionar cidade-base para explorar destinos e conexões TER. Essa seleção não altera a decisão oficial.
5. Itália: escolher alternativa da Costa Amalfitana (Salerno ou Maiori) para comparar ferries; não pressupor origem da tarifa quando a rota é diferente.
6. Seleção de passeios com preço publicado, total APENAS dos bilhetes conhecidos para duas pessoas, separado por EUR e CHF; não combinar moedas nem inferir custo final de viagem. Itens sem preço aparecem como "a cotar", e descontos Carte Fluo dependem de elegibilidade/compra do cartão.
7. Exibir aviso de sobreposição com orçamento de passeios e conexão aérea não cotada; não adicionar novamente valores automaticamente.
8. Testes para fontes, duplicação, unidade monetária, multiplicador para 2 viajantes, ida/volta, não misturar CHF/EUR, mapas e páginas; publicar no GitHub e confirmar GitHub Actions.

## Aceite
Roteiro navegável, mapas, excursões concretas com duração e fonte, preços condicionais por casal, pendências explícitas e nenhum preço 2027 inventado, preservando Drive e demais páginas.
