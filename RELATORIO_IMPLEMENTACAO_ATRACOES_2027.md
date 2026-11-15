# Relatório de implementação — Explorar atrações | Nossa Europa 2027

Data da coleta e implementação: **14/11/2026**. Branch: `main`.
Especificação original: [PROMPT_CATALOGO_ATRACOES_ROTEIRO_ADAPTATIVO_2027.md](PROMPT_CATALOGO_ATRACOES_ROTEIRO_ADAPTATIVO_2027.md).

## Entrega no front-end

**Menu:** `Roteiro → Explorar atrações`, ao lado das seções de Itália, França, Transportes, Calendário.

- Selecionar uma das quatro cidades-base da França; escolha é apenas simulação, **não altera D-004**.
- Visualizar **11 destinos** (quatro cidades-base, Colmar, Freiburg, Basel, Luxemburgo e três regiões alpinas) e **50 atrações catalogadas**; fontes oficiais associadas a cada atração.
- Filtrar país, categoria, interesse pessoal, status do ingresso, tempo de trem pesquisado e destinos com transporte documentado/pernoite.
- Cards com fotos de destinos licenciadas Wikimedia Commons, créditos/links, destaques, tempo de trem quando publicado, tarifa histórica condicionada para duas pessoas, distância geodésica explicitamente rotulada **linha reta**, viabilidade em estudo e aviso de custos faltantes.
- Ver detalhes: descrição, tempo de visita **estimado editorialmente**, fonte oficial, preço observado ou "a verificar" e link para pesquisa no Google Maps. O mapa principal mostra **pinos dos destinos**, não coordenadas precisas para todas as atrações.
- Escolher de 1 a 5 atrações por cidade e salvar um pacote por destino durante a sessão. O custo do trem entre base e destino é somado **uma vez por destino**, mesmo com cinco atrações.
- Marcar "Quero visitar", "Opcional" ou "Descartar", filtrar preferências, exportar JSON. Essas alterações são **temporárias na sessão**, não gravadas no Drive/GitHub.
- Adicionar um pacote a um dia francês livre nas férias ou no fim de semana; impedir colisões entre dois passeios no mesmo dia, bloqueio de instalação, dias italianos e trabalho remoto em dias úteis. O calendário da página Roteiro mostra essas escolhas provisórias.
- Integrar ao Orçamento usando somente **excedente positivo** dos custos conhecidos acima da verba de passeios já prevista. Se os bilhetes conhecidos ficarem abaixo do teto da rubrica, NÃO registrar economia fictícia. EUR e CHF convertidos separadamente com câmbio hipotético selecionado.
- Na página Mapa & destinos, incluir novos destinos pesquisados no catálogo comum e link de navegação à nova seção.

## Pesquisa coberta

| Destino | Atrações | Fonte base |
|---|---:|---|
| Mulhouse | 6 | https://www.tourisme-mulhouse.com/en/what-to-do-in-mulhouse/getting-around-mulhouse-by-public-transport/ |
| Strasbourg | 6 | https://www.visitstrasbourg.fr/en/discover/must-see-attractions/ |
| Metz | 6 | https://www.tourisme-metz.com/en/discover-metz-metropole/top-15-tourist-spots-in-metz-metropole |
| Nancy | 6 | https://www.destination-nancy.com/en/tourisme/decouvrir-nancy/les-incontournables/ |
| Colmar | 5 | https://tourisme-colmar.com/en/visit/presentation/discover |
| Freiburg | 4 | https://visit.freiburg.de/en/discover/sightseeing/top-10-sightseeing |
| Basel | 4 | https://www.basel.com/en/places-of-interest |
| Luxemburgo | 4 | https://www.visitluxembourg.com/place/bock-casemates-luxembourg |
| Interlaken | 3 | https://www.interlaken.ch/en/ |
| Oeschinensee/Kandersteg | 3 | https://www.oeschinensee.ch/en/tarife-fahrplan/ |
| Lauterbrunnen | 3 | https://lauterbrunnen.swiss/en/destination/discover-the-lauterbrunnen-valley.html |

Valores de ingresso que foram vistos em páginas oficiais **na coleta de novembro/2026**:
- Cité du Train: **€16/adulto**, https://www.tourisme-mulhouse.com/en/experiences/railway-museum-cite-du-train/;
- Casamatas do Bock: **€11/adulto**, https://www.luxembourg-city.com/en/tours-activities/underground/bock-casemates;
- Trümmelbachfälle: **a partir de CHF18/adulto**, https://lauterbrunnen.swiss/en/map/detail/trummelbach-waterfalls-52c355bf-8544-4c9b-9885-427fc77657fb.html;
- Oeschinensee: **CHF36/adulto, ida e volta do teleférico, tarifa de outono 2026**, https://www.oeschinensee.ch/en/tarife-fahrplan/.
Todos os outros museus com preço não verificado permanecem com `ticket.status=unknown`. Visitas externas a praças/ruas/parques têm `ticket.status=not_applicable` e não incluem acessos internos/visitas especiais.

## Matriz base × destino

**44 combinações** em `data/base_destination_routes_2027.json`: uma para cada uma das quatro cidades-base × onze destinos. Linhas sem tempo/tarifa comprovados ficam com `null`, nunca zero.

Exemplos com **Carte Fluo** publicada (tarifa € por pessoa/trecho, não inclui custo cartão nem trânsito local):
| Origem | Destino | Trem/trecho | Casal ida/volta condicional |
|---|---|---:|---:|
| Mulhouse | Colmar | 18 min | €21,60 |
| Strasbourg | Colmar | 32 min | €31,60 |
| Mulhouse | Basel | 22 min | €18,80, sujeita à regra transfronteiriça |
| Metz | Nancy | 38 min | €28,00 |
| Nancy | Metz | 38 min | €28,00 |
| Strasbourg | Metz | 96 min | €67,60 |
| Metz | Strasbourg | 96 min | €67,60 |

Fontes ferroviárias: https://www.ter.sncf.com/grand-est/trajet-mulhouse-colmar , https://www.ter.sncf.com/grand-est/trajet-strasbourg-colmar , https://www.ter.sncf.com/grand-est/trajet-nancy-metz , https://www.ter.sncf.com/grand-est/trajet-strasbourg-metz .

**Atenção:** Isso não valida retorno dominical, desconto para casal, disponibilidade 2027 ou tempo porta a porta. Preços normais de trem, custo do cartão, hotel alpino e trajetos completos permanecem em aberto.

## Integridade de dinheiro e tempo

- `attractions_model.py`: validação de dados, linha reta explicitamente separada de percurso, tarifas por moeda e visitante, agregação sem repetição de trem, elegibilidade de calendário e excedente financeiro conservador.
- `attractions_ui.py`: UI Streamlit isolada da aplicação principal para facilitar manutenção.
- `tests/test_attractions_model.py`: teste dos quatro cenários de base, Colmar 18/32 minutos, cartões Fluo, custos EUR/CHF, tickets desconhecidos e conflitos de datas.
- `tests/test_attractions_ui_smoke.py`: navegação Streamlit real das quatro bases, salvar Colmar, inserir no calendário, abrir o orçamento.
- `assets/styles.css`: fotos com mesma altura e responsividade.
- `app.py`: nova aba, ligação às páginas do mapa/calendário/orçamento.
- `.github/workflows/validate.yml`: compilar módulos novos e rodar testes junto com o legado.

## Limitações honestas / próximas pesquisas
1. **Pinos de atrações**: hoje há pinos de cidades/destinos, mas não geocodificação individual validada de todas as 50 atrações; o detalhe oferece link para abrir o lugar no Google Maps.
2. **Fotos**: retratos ilustrativos de vários destinos no Wikimedia Commons, licenciados e atribuídos por fonte. Ainda não há uma fotografia individual com licença verificada para cada atração.
3. **Transporte completo**: faltam tarifa normal (sem Fluo), cartão Fluo, conexões, caminhada, fim de semana, último trem e ônibus final para a maioria das 44 combinações.
4. **Orçamento completo por passeio**: subtotal contém apenas itens efetivamente publicados. Comida, ingresso a cotar, hotel, margem de câmbio e taxas permanecem fora. O modelo conservador não reduz a verba original com base em subtotal incompleto.
5. **Calendário**: alocação de um destino por dia na sessão, sem geolocalização do hotel e sem intervalo de horas; não confirma abertura naquele dia, disponibilidade ou reserva. Exportar JSON antes de fechar sessão.
6. **Cidade-base**: não muda a decisão D-004 no Drive.
7. **2027**: datas de saída não definitivas e preços 2027 ainda não contratáveis. Confirmar tudo antes da viagem.
8. **Fase italiana**: o modelo poderá receber atrações italianas, mas este primeiro catálogo detalha a França e países próximos, preservando a seção Itália existente.

## Segurança
Nenhuma credencial foi inserida nem modificada. Recomenda-se rotacionar a chave do GCP compartilhada em conversa passada e atualizar Streamlit Secrets.
