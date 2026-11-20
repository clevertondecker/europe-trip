# DATA17 — lacunas de destinos dos três roteiros (20/11/2026)

## Escopo
Auditoria de cidades e passeios **citados na apresentação visual** para as três bases francesas (Strasbourg, Metz, Mulhouse), comparada ao registro usado por `Explorar → Passeios`: `_registry()` combina `data/attractions_2027.json`, `data/exploration_bases_2027.json` e `data/base_city_research_expanded_2026_11.json`. A lista não depende apenas de `data/attractions_2027.json` e a busca é um agrupamento por cidade, não uma lista de bilhetes.

## Resultado
- **Lacunas confirmadas entre os passeios franceses citados:** `obernai` e `lucerne`.
- **Já representados:** Strasbourg, Colmar, Freiburg, Baden-Baden, Basel, Paris, Metz, Luxembourg City (alias canônico `luxembourg_city`), Nancy, Trier, Saarbrücken, Reims, Mulhouse, Interlaken e Oeschinensee/Kandersteg.
- **Itália:** Roma, Nápoles, Salerno, Maiori, Minori, Amalfi, Positano e Capri aparecem em `data/itinerary_options_2027.json` ou na experiência italiana; **não** são automaticamente parte do explorador independente das cidades francesas. Pompeia, Herculano, Sorrento e Ravello estão citados no guia, mas é preciso auditoria funcional separada de suas representações na experiência Itália para determinar quais podem ser selecionados como passeio. Não duplicar seus IDs no catálogo francês por suposição.

## Fix mínimo
1. Adicionar **Obernai** (48.4627, 7.4816), França, e **Lucerna/Luzern** (47.0502, 8.3093), Suíça, como destinos na coleção exploratória já consumida pelo registro.
2. Adicionar três atrações documentadas por destino a `data/dq32_macro_tourism_2026_11.json` (fontes oficiais abaixo).
3. Não fabricar trechos de trem, horário de retorno, duração de visita, preço ou disponibilidade para 2027: todos permanecem desconhecidos e precisam de pesquisa específica.
4. Preservar o mecanismo de fotos atual: nenhuma foto sem licença foi anexada. Os novos destinos usarão busca de imagem sob demanda e fallback visual já implementado, podendo exibir placeholder enquanto não existir mídia validada.

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
