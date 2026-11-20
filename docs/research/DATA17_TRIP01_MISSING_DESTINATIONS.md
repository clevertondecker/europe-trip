# DATA17 — lacunas de destinos dos três roteiros (20/11/2026)

## Escopo
Auditoria de cidades e passeios **citados na apresentação visual** para as três bases francesas (Strasbourg, Metz, Mulhouse), comparada ao registro usado por `Explorar → Passeios`: `_registry()` combina `data/attractions_2027.json`, `data/exploration_bases_2027.json` e `data/base_city_research_expanded_2026_11.json`. A lista não depende apenas de `data/attractions_2027.json` e a busca é um agrupamento por cidade, não uma lista de bilhetes.

## Resultado
- **Lacunas confirmadas entre os passeios franceses citados:** `obernai` e `lucerne`.
- **Já representados:** Strasbourg, Colmar, Freiburg, Baden-Baden, Basel, Paris, Metz, Luxembourg City (alias canônico `luxembourg_city`), Nancy, Trier, Saarbrücken, Reims, Mulhouse, Interlaken e Oeschinensee/Kandersteg.
- **Itália:** Roma, Nápoles, Salerno, Maiori, Minori, Amalfi, Positano e Capri aparecem em `data/itinerary_options_2027.json` ou na experiência italiana; **não** são automaticamente parte do explorador independente das cidades francesas. Pompeia, Herculano, Sorrento e Ravello estão citados no guia, mas é preciso auditoria funcional separada de suas representações na experiência Itália para determinar quais podem ser selecionados como passeio. Não duplicar seus IDs no catálogo francês por suposição.

## Correção aditiva com snapshot preservado

A primeira tentativa de adicionar os dois destinos aos arquivos históricos globais alterou o inventário 30×46 e causou regressões amplas em testes e relatórios ferroviários. A mudança foi **revertida** antes do merge.

A solução revisada preserva integralmente o snapshot original (30 bases, 46 destinos, 1.380 pares):
1. `data/trip01_supplemental_destinations_2027.json`: dois destinos candidatos, com seis atrações e URLs oficiais.
2. `trip01_supplemental_discovery.py`: projeção somente leitura que combina as novas entradas com o inventário existente; valida IDs, fontes e coordenadas.
3. `ux501_destination_discovery_ui.py`: a busca e os cartões usam essa projeção, sem alterar o `TripPlan` ou os dados ferroviários históricos.
4. Fotos verificadas de Obernai (Morio60/Patrick Monchicourt, CC BY-SA 2.0) e Lucerna (Yair Haklai, CC BY-SA 4.0) foram vinculadas por URLs diretas oficiais do Wikimedia e páginas Commons de autoria/licença. O fallback visual é preservado para falhas de rede. Nenhuma imagem gerada ou sem fonte foi usada.
5. **Limitação:** as entradas complementares aparecem em **Explorar → Passeios**, inclusive para adicionar à lista de interesses, mas ainda não são automaticamente selecionáveis na matriz de passeios do **Meu planejamento**. Isso precisará de uma integração posterior com contratos canônicos e auditoria de regressões. Nenhum custo ou retorno é declarado confirmado.

## Obernai — referências
- [Turismo Grand Est](https://visitgrandest.fr/en/lieux/obernai/)
- [Place du Marché, cidade de Obernai](https://www.obernai.fr/Fr/Divertir/Histoire-Patrimoine/Patrimoine-historique-Obernai/Place-Marche.html)
- [Muralhas, Turismo Obernai](https://www.tourisme-obernai.fr/En/Things-to-see-and-do/Obernai/Monuments-and-buildings.html?fiche=220000754)
- [Percurso histórico, cidade de Obernai](https://www.obernai.fr/Fr/Divertir/Histoire-Patrimoine/Parcours-historique-Obernai.html)

## Lucerna — referências
- [Turismo da Suíça: Kapellbrücke](https://www.myswitzerland.com/en-ch/experiences/chapel-bridge-and-water-tower/)
- [Turismo de Lucerna: centro histórico](https://www.luzern.com/en/highlights/hopping/small-town/luzern)
- [Turismo de Lucerna: atrações](https://www.luzern.com/en/the-city/sights/top-sights/All/offset%253A12)

## Limites
Esta auditoria cobre **nomes de destinos recomendados nos três roteiros**, não todos os lugares turísticos possíveis na Europa. Cobertura do catálogo não equivale a horário de trem confirmado; viagens devem validar volta e última milha. No cadastro manual, selecionar destinos no explorador francês e consultar a seção italiana separadamente.
