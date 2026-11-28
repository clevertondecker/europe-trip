# DATA26C — Revisão de qualidade para decisão (28/11/2026)
Complementa DATA26C_PRIORITY_RESEARCH_COMPLETE.md e o contrato DATA26C original. A ordem abaixo prevalece sobre metas de volume. PR #278 único, draft, sem merge até autorização.

## Checklist por domínio
- [x] Auditar os 42 registros do HEAD 96917f5 (21 oficiais, 21 secundários): direção, identidade/país, mínimo e média da mesma versão, modalidade ferroviária, estação publicada, URL/data/limites. Preservar histórico; reconsulta divergente não é substituição automática. Páginas mistas exigem evidência ferroviária explícita; sem prova de todos os trechos, não promover a itinerário.
- [x] Isolar a observação DATA26C da proveniência ROUTES7: nomes publicados distintos de IDs reconciliados, sem condições comerciais ou estações herdadas; testes de conflitos e precedência.
- [x] DATA26B1: moeda, data, direção, unidade e modalidade na revisão; identidade de captura sem preço; duplicidade versus conflito versus captura distinta; separar legado, sobreposição, ganho líquido e progresso do lote. Preservar 60 pares e contratos DATA26B.
- [ ] Piloto Paris: mesmo sábado/domingo e antecedência, duas pessoas adultas, segunda classe sem descontos presumidos, segmentos ferroviários de ida e volta identificados, taxas/reservas, condições, tempo útil entre chegada e partida. Usar DATA26B existente; não combinar mínimos nem multiplicar tarifas publicitárias em cotação. Se motor inacessível, registrar lacuna por base. Depois Colmar e Luxemburgo se aplicável.
- [ ] Passes regionais/transfronteiriços: preço e moeda, elegibilidade, validade, trechos, restrições e reservas; distinguir produto de tarifa indicativa ou cotação.
- [ ] DATA26A/UX132C2: ofertas mobiliadas 56–60 noites, duas pessoas, total, taxas, caução, mobiliário, serviços, cancelamento e internet residencial documentada; sem disponibilidade 2027 inventada. Separar referência mensal de oferta efetiva.
- [ ] Cesta de custo de vida comparável e condições de trabalho remoto.
- [ ] Atrações, ingressos, última milha e demais lacunas do catálogo; metas documentais subordinadas à confiabilidade.
- [ ] Relatório antes/depois por base, destino e domínio; cobertura versus tentativa, confiança e disponibilidade. DATA24 histórico intacto, universo global e denominador 270 preservados, tarifas 60 pares, precedência antiga.
- [ ] Suite completa no HEAD final, integração main/UX133, REC02, TripPlan, wishlist, DRAFT/SCOPE/CHOICE, orçamento, persistência e handoffs; QA desktop/mobile se disponível, explicitar limitações.

Sem novo motor, página, ranking, estimativa financeira ou sistema paralelo. Cada incremento: lacunas, fontes efetivamente consultadas, evidências, atualização, testes e resultado. Amostras de 2026 não comprovam 2027. Não computar média agregada entre domínios.

## Baseline de revisão
HEAD 96917f59a6d9036dda73cda1ed013a883f8d5b49: 42 registros, 21 oficiais e 21 secundários; 248/270 tempos de ida projetados (91,9%), pendentes de CI nesse HEAD. Não equivalem a horários de retorno, preços, nem cobertura dos outros domínios.

## Lotes de auditoria
Manter resultados incrementais aqui ou nas observações dos registros, distinguindo reproduzido, divergente, inconclusivo e não consultado. Não considerar todos os 42 revalidados até evidência individual.

### Incremento de 28/11/2026 — qualidade, não expansão de cobertura
- Revisão direta de quatro dos 42 registros: Lille→Saumur, Metz→Saumur, Metz→Interlaken Ost e Strasbourg→Dinan. Duas observações selecionadas foram reproduzidas em versões consultadas; duas divergem. As versões mais recentes também podem divergir das reproduzidas. As quatro consultas são registradas em quality_review (mesma versão para mínimo/média); nenhum valor selecionado foi substituído. Restam 38 revisões individuais neste checklist, mesmo quando há uma revalidação anterior.
- A projeção DATA26C agora constrói uma observação isolada, conserva estações publicadas e IDs não reconciliados, não herda dados comerciais, datas ou médias de ROUTES7. Testes específicos enviados; CI final pendente.
- DATA26B1: 19 das 21 revisões históricas têm observação de calendário correspondente para documentar moeda/unidade/direção; as duas restantes (ônibus e sem preço) não recebem unidade presumida. Comparação de valores exige rótulo ferroviário e termos equivalentes; duplicidade e conflito são rejeitados separadamente; uma captura distinta pode ter outro preço. Métricas acumuladas e ganho líquido separados na UI. Testes enviados; CI final pendente.

### Piloto Paris — fase de calendário (não cotação)
Consulta 28/11/2026; ida 05/12/2026 (sábado), retorno 06/12/2026 (domingo), amostra comum de 7–8 dias de antecedência. Calendário SNCF Connect, valor anunciado em EUR por pessoa, trecho único, segunda classe, sujeito a disponibilidade; marca comercial indica ferrovia, não valida cada segmento. Valores em duas direções são **observações independentes**; não somar ou multiplicar para produzir cotação de dois adultos. Mínimos e médias abaixo são resumos não datados das respectivas páginas, não duração do serviço do fim de semana. Não inferir tempo útil ou disponibilidade de 2027.

| Base | Ida anunciada (marca) | Retorno anunciado (marca) | Resumo ida mínimo/média (min) | Resumo retorno mínimo/média (min) |
|---|---:|---:|---:|---:|
| Lille | €19 OUIGO | €16 OUIGO | 56/80 | 55/82 |
| Metz | €25 OUIGO | €40 TGV INOUI | 82/125 | 83/125 |
| Nancy | €31 Fluo | €43 TGV INOUI | 90/128 | 88/120 |
| Mulhouse | €38 LYRIA | €65 TGV INOUI | 162/185 | 155/187 |
| Strasbourg | €29 OUIGO | €47 TGV INOUI | 104/132 | 104/129 |

Fontes consultadas, 28/11/2026: páginas SNCF Connect para cada direção:
- lille: https://www.sncf-connect.com/train/trajet/lille/paris ; https://www.sncf-connect.com/train/trajet/paris/lille
- metz: https://www.sncf-connect.com/train/trajet/metz/paris ; https://www.sncf-connect.com/train/trajet/paris/metz
- nancy: https://www.sncf-connect.com/train/trajet/nancy/paris ; https://www.sncf-connect.com/train/trajet/paris/nancy
- mulhouse: https://www.sncf-connect.com/train/trajet/mulhouse/paris ; https://www.sncf-connect.com/train/trajet/paris/mulhouse
- strasbourg: https://www.sncf-connect.com/train/trajet/strasbourg/paris ; https://www.sncf-connect.com/train/trajet/paris/strasbourg

As cinco observações de ida foram adicionadas ao contrato DATA26B1 existente, sem alterar o universo de 60 pares e sem ganho líquido de pares (já documentados). Retornos registrados aqui como evidência de calendário fora da direção histórica desse contrato; não inseridos como cotações DATA26B. As tentativas de acessar páginas de horários com data na URL para Lille→Paris e Paris→Lille falharam. O calendário não fornece o serviço associado ao menor preço, disponibilidade simultânea, perfil de dois adultos, condições completas e taxas. Logo: 0/5 cotações completas obtidas neste piloto, 0/5 tempos úteis comprovados. Pesquisar horários datados e cotações completas antes de concluir a comparação.

### Produtos regionais — documentação inicial
- Pass Groupe Week-End (TER Fluo Grand Est): €40 por grupo de 2–5, segunda classe, um sábado, domingo ou feriado escolhido; viagens ilimitadas em trens e ônibus elegíveis Fluo. Inclui Paris Est fora do TGV, Basel e Luxemburgo conforme FAQ. Para trens de/para Paris é obrigatória reserva a €0, com disponibilidade limitada; a oferta não acumula descontos e é reembolsável até a véspera. Reservas TER de Paris–Strasbourg e Paris–Troyes–Mulhouse têm regras específicas de alteração/reembolso. Não implica elegibilidade de qualquer trem, nem de Lille (fora da região), nem disponibilidade em 2027. Fonte consultada em 28/11/2026: https://www.ter.sncf.com/grand-est/tarifs-cartes/tarifs-regionaux/pass-groupe-week-end
- Ticket Saar-Lorraine-Luxembourg: produto de um dia, ida e volta, sábados/domingos/feriados aplicáveis; individual ou grupo até cinco; acesso às redes elegíveis além da fronteira, sem troca nem reembolso. A página consultada não exibe valor numérico nem comprova classe ou reservas; não estimar. Fonte 28/11/2026: https://www.ter.sncf.com/grand-est/tarifs-cartes/tarifs-transfrontaliers/tickets-saar-lorraine-luxembourg
- Produtos são referências documentais, não cotações nem evidência de disponibilidade. Não ampliar denominadores nem inserir preço do passe em observações de tarifa individual. Verificar integração com contratos de mobilidade já existentes antes de projetar.

### Pendências do incremento
38 revisões de qualidade restantes; confirmar CI após todos os commits, fontes de horários e retorno datado, tempo útil e cotação completa Paris; aprofundar passes, Colmar/Luxemburgo, moradia/internet, custo de vida e atrações. QA visual e comparação histórica final não executados.


### Auditoria individual completa — 28/11/2026
- 42/42 registros originais revisados no campo `quality_review` (URL exata, direção, país, pares mínimo/média na mesma versão, recência, ressalvas e rótulos de estação quando observados). 21 oficiais, 21 secundários. Fonte consultada via páginas públicas indexadas; não há captura permanente ou verificação de todos os trechos. Os 42 valores selecionados e sua confiança permanecem intactos.
- Reprodução numérica de ambos os valores: 20/42 (11 oficiais, 9 secundários). Divergências: 22/42 (10 oficiais, 12 secundários). A revisão distingue reprodução numérica de validação do serviço. Nenhuma revisão comprova itinerário em 2027.
- Exemplo: Nancy→Saumur 275/308 selecionados versus 276/316 na nova página; Lille→Dinan 313/385 versus 298/375; Nancy→Arlon 153/189 versus 130/159. Não combinar mínimo e média de versões diferentes.
- Caso de modalidade inconclusiva: Strasbourg→Arlon reproduz 135/200 na FAQ ferroviária, mas a lista de operadores da página só cita Flixbus. Uma consulta independente indica rota ferroviária via Luxemburgo (Rome2Rio, https://www.rome2rio.com/s/Strasbourg/Arlon); não confirma a média nem todos os trechos da referência selecionada. Manter a referência histórica de baixa confiança explicitamente ressalvada; não utilizar para afirmar viabilidade, itinerário integralmente ferroviário ou cotação. 19 reproduções numéricas sem essa inconsistência específica, 1 com ressalva. As outras fontes secundárias têm texto especificamente ferroviário, mesmo quando a lista comercial inclui ônibus; nenhum tempo identificado como rodoviário foi importado.
- Estações indicadas pela fonte não equivalem a IDs reconciliados. Campos vazios significam que a revisão não identificou rótulos específicos no extrato inspecionado, não que a cidade não tenha estação.
- CI anterior ao lote: HEAD e0147ca, 1522 testes, 2 ignorados, zero falhas. Lote atual aguarda CI. Cobertura documental histórica de tempos não equivale a confirmação das 42 referências nem foi artificialmente ampliada.

### Paris — amostra suplementar de domingo, 29/11/2026
Consulta em 28/11/2026, um dia de antecedência. A amostra originalmente definida (05–06/12/2026, 7–8 dias) permanece separada: não foi possível obter os serviços datados daquele fim de semana. Para comparar a logística de um dia, foram escolhidos serviços diretos publicados nas duas direções no mesmo domingo, partindo da estação da base a partir de 07:30 e retornando à mesma estação antes da meia-noite; chegada/partida na mesma estação parisiense. Todos são horários locais CET. A duração entre chegada e partida é janela bruta na cidade, não tempo líquido de visita (não desconta deslocamentos urbanos, alimentação ou antecedência de embarque). Não implica lugares disponíveis, serviço efetivamente operado ou viagem 2027.

| Base | Ida (TGV INOUI) | Retorno (TGV INOUI) | Estações base / Paris | Janela bruta |
|---|---|---|---|---:|
| Lille | 08:12–09:25, 7014 | 22:44–23:50, 7093 | Lille Flandres / Paris Nord | 13h19 |
| Metz | 08:49–10:13, 2860 | 21:35–23:04, 2647 | Metz / Paris Est | 11h22 |
| Nancy | 08:11–09:48, 2534 | 21:12–22:49, 2527 | Nancy / Paris Est | 11h24 |
| Mulhouse | 07:46–10:42, 6702 | 20:22–23:20, 6715 | Mulhouse / Paris Gare de Lyon | 9h40 |
| Strasbourg | 08:20–10:05, 2352 / 9534 (números publicados no mesmo serviço direto) | 22:05–23:51, 2471 | Strasbourg / Paris Est | 12h00 |

Fontes oficiais dos horários, consultadas em 28/11/2026 (tabelas explicitamente datadas de 29/11):
- Lille: https://www.sncf-connect.com/train/horaires/lille/paris ; https://www.sncf-connect.com/train/horaires/paris/lille
- Metz: https://www.sncf-connect.com/train/horaires/metz/paris ; https://www.sncf-connect.com/train/horaires/paris/metz
- Nancy: https://www.sncf-connect.com/train/trajet/nancy/paris ; https://www.sncf-connect.com/en-en/train/timetables/paris/nancy (a página francesa /train/horaires/nancy/paris estava datada de 28/11, portanto não foi usada na ida).
- Mulhouse: https://www.sncf-connect.com/train/horaires/mulhouse/paris ; https://www.sncf-connect.com/train/horaires/paris/mulhouse
- Strasbourg: https://www.sncf-connect.com/train/horaires/strasbourg/paris ; https://www.sncf-connect.com/train/horaires/paris/strasbourg

**Cotações completas (dois adultos): bloqueio de acesso.** Tentativas de abrir horários específicos de 05–06/12 para Lille (https://www.sncf-connect.com/train/horaires/lille/paris/2026-12-05 e https://www.sncf-connect.com/train/horaires/paris/lille/2026-12-06) e os resultados dinâmicos SNCF (https://www.sncf-connect.com/app/home/shop/results) e Trainline (https://www.thetrainline.com/book/results) não retornaram conteúdo acessível pela ferramenta de pesquisa. A fonte pública mostra serviços e valores indicativos independentes, mas não associa preço e disponibilidade simultânea de ida/volta, dois adultos, classe e condições completas. Para Lille, Metz, Nancy, Mulhouse e Strasbourg, registrar 0/5 cotações completas obtidas, não 0/5 ofertas disponíveis no mercado. O contrato DATA26B continua com zero cotações; nenhum preço foi inventado, multiplicado ou combinado com horários de outra data. Próximo passo quando houver acesso ao formulário interativo de reserva: selecionar as mesmas datas, perfil, classe, serviços e capturar valor total, condições, taxas e reservas para cada base. Não dar a tarefa tarifária como concluída enquanto faltar evidência.

A comparação de horários de domingo está documentada para 5/5 bases; a comparação de sábado/domingo de 05–06/12 e as cotações DATA26B permanecem incompletas. Este relatório não cria um motor ou fonte de verdade paralela nem altera o orçamento ou TripPlan.

### Complemento de produtos regionais — 28/11/2026
- **Lille–Paris, TER Hauts-de-France Krono 12**: oferta oficial a partir de €10 por adulto por trecho; sábados, domingos e feriados, limitada aos lugares disponíveis, não acumulável e reembolsável até a véspera. A página publica dois serviços em cada sentido. A combinação publicada Lille Flandres 09:14 → Paris Nord 11:26 e Paris Nord 18:28 → Lille Flandres 20:49 deixa 7h02 de janela bruta na cidade. É um horário padrão do produto, sem data de serviço específica; não constitui cotação nem comprova disponibilidade do casal. Classe e taxas não explicitadas na página. Não multiplicar a tarifa mínima como cotação. Consulta 28/11/2026, página indexada hoje: https://www.ter.sncf.com/hauts-de-france/bons-plans/lille-paris-des-10-euros
- **Saar-Lor-Lux-Ticket**: a CFL corrobora viagens regionais ilimitadas em segunda classe por um dia, na área elegível de Lorraine, Saarland e Luxemburgo; exclui TGV e ônibus Luxembourg–Saarbrücken Express. Preço não publicado na página consultada; a compra indicada é por telefone ou bilheteria. Não presumir validade em toda a França/Alemanha. Consulta 28/11/2026, índice do mês anterior: https://www.cfl.lu/en-gb/ticket/international/europe/weekend-en-gr
- **TER Hauts-de-France**: bilhetes promocionais regionais entre €3 e €22 conforme distância, inclusive Paris, e tarifas negociadas para a Bélgica; descontos coletivos de 5–9 pessoas e de 10+ não são aplicáveis ao casal. A página não comprova preço específico para os trajetos desejados. Consulta 28/11/2026: https://www.ter.sncf.com/hauts-de-france/tarifs-cartes/billets
- Ganho: uma alternativa regional documentada para Lille–Paris, uma fonte oficial adicional para o passe transfronteiriço e exclusão de descontos incompatíveis com dois adultos. Cobertura histórica de 60 pares, cobertura ferroviária 248/270 e cotações completas 0/5 inalteradas. Não criar observação tarifária datada nem serviço específico a partir de oferta geral.


### Moradia e trabalho remoto — triagem de 15 estabelecimentos (28/11/2026)
Janela de comparação **hipotética**, não gravada no TripPlan: 29/09–27/11/2027, 59 noites, dois adultos. A janela permite pesquisar uma estadia após as férias iniciais; não é uma decisão de datas do usuário. As fontes abaixo são páginas dos próprios estabelecimentos, não ofertas de reserva para o período. Não contam como cotações DATA26A nem como amostra independente adicional à amostra histórica D-004 (eventuais estabelecimentos repetidos precisam ser reconciliados).

| Base | Estabelecimento | Características anunciadas verificadas na fonte | Fonte |
|---|---|---|---|
| Lille | Appart'City Euralille (La Madeleine, área metropolitana) | Wi-Fi fibra gratuito e espaço de trabalho; tram Romarin, duas paradas até Flandres/uma até Europe | https://www.appartcity.com/en/destinations/france/hauts-de-france/lille/lille-euralille |
| Lille | Appart'City Grand Palais | Estúdio para 2, mobiliado, cozinha, Wi-Fi gratuito | https://www.appartcity.com/fr/destinations/france/hauts-de-france/lille/lille-grand-palais |
| Lille | Adagio Centre Grand Place | Estúdio 26 m² para 2, cozinha, Wi-Fi gratuito, Flandres a 10 min a pé segundo o operador | https://www.adagio-city.com/fr/hotel-a0w9-aparthotel-adagio-lille-centre-grand-place.shtml |
| Metz | Residhome Metz Lorraine | Cozinha, mesa de trabalho, Wi-Fi e limpeza semanal incluídos; lavanderia extra; estação próxima. Fonte indica €90 para uma noite de 27/11/2026, até 2 pessoas, **não** tarifa de 59 noites | https://www.residhome.com/residence-hoteliere-aparthotel-metz-154.html |
| Metz | Student Factory Trèves | Estúdio com cama dupla, cozinha, mesa de trabalho, Wi-Fi de alta velocidade, coworking; anúncio a partir de €45/noite sem período aplicável | https://www.student-factory.com/fr/appart-hotel/metz-treves |
| Metz | Le Colibri | Apartamento até 4, cozinha, Wi-Fi fibra gratuito, varanda | https://lecolibrimetz.com/ |
| Nancy | Adagio Access Nancy Centre | Estúdio para 2, cozinha, banheiro privativo, acesso à lavanderia; Wi-Fi anunciado na página regional | https://www.adagio-city.com/fr/hotel-8988-aparthotel-adagio-access-nancy-centre/index.shtml ; https://www.adagio-city.com/fr/apparthotel-nancy.shtml |
| Nancy | KOSY Cœur de Ville | Unidade mobiliada com cama simples/dupla, mesa, kitchenette, tomadas de internet; duração flexível anunciada, sem medição de conexão | https://www.kosy-apparthotels.com/nancy-coeur-de-ville/ ; https://en.kosy-apparthotels.com/nancy-coeur-de-ville/ |
| Nancy | Nemea Home Suite Nancy Centre | Estúdio para 2, mobiliado, kitchenette, Wi-Fi e lavanderia listados como serviços incluídos; confirmar custo efetivo do uso | https://www.nemea-appart-hotel.com/france/lorraine/meurthe-et-moselle/nancy/home-suite-nancy-centre-10 |
| Mulhouse | Appart'City Centre | Estúdio para 2, cozinha, mesa, Wi-Fi gratuito ligado à fibra; lavanderia à parte; estação ~2 km e acesso por tram T2 Lefebvre | https://www.appartcity.com/fr/destinations/france/grand-est/mulhouse/mulhouse-centre |
| Mulhouse | Residhotel Centre | Estúdios 18–29 m² para 2, cozinha, banheiro privativo, Wi-Fi gratuito; motor de reservas carrega tarifas separadamente | https://www.residhotel.com/en/mulhouse-centre/apartments |
| Mulhouse | Quality Aparthotel Zenitude | Cozinha, Wi-Fi, limpeza semanal em estadias acima de sete noites; página indica abertura próxima. **Candidato preliminar, operação e capacidade para 2 não confirmadas** | https://www.zenitude-hotel-residences.com/residences/mulhouse/ |
| Strasbourg | Appart'City Centre | Estúdio para 2, mesa de trabalho, cozinha, Wi-Fi fibra gratuito; lavanderia opcional, estação anunciada a 700 m | https://www.appartcity.com/fr/destinations/france/grand-est/strasbourg/strasbourg-centre |
| Strasbourg | Adagio Place Kléber | Estúdio 25 m² para 2, cozinha, Wi-Fi gratuito, estação anunciada a 700 m / 10 min a pé | https://www.adagio-city.com/fr/hotel-7123-aparthotel-adagio-strasbourg-place-kleber/index.shtml |
| Strasbourg | Adagio Access Petite France | Estúdio 20 m² para 2, cozinha, Wi-Fi gratuito e lavanderia; página anuncia 5 e 10 min até estação em trechos distintos, não selecionar um valor como verificado | https://www.adagio-city.com/fr/hotel-8446-aparthotel-adagio-access-strasbourg-petite-france/index.shtml |

Tentativas de acesso com 29/09–27/11/2027 e dois adultos em Appart'City Euralille, Mulhouse Centre e Strasbourg Centre retornaram erro de acesso à URL parametrizada (parâmetros de pesquisa de data e ocupação); não prova indisponibilidade comercial nem que o provedor aceitou esses parâmetros. MyResidhome retornou apenas uma página de reserva sem oferta datada legível. Adagio, Nemea, Residhotel e demais páginas consultadas apresentam características, não o preço total para a janela. O programa de longa permanência Appart'City oferece consulta separada: https://www.appartcity.com/fr/concept-experiences/offre-long-sejour . Não multiplicar preço diário ou presumir que serviços, impostos, caução ou cancelamento estão incluídos. Nenhuma confirmação de velocidade efetiva, upload, VPN ou estabilidade residencial.

Resultado: cinco bases triadas, 15 estabelecimentos distintos (14 páginas de estabelecimentos apresentados como operantes e um anunciado como abertura próxima); **0/15 cotações completas da janela**, 0/5 bases com três cotações completas, 0/5 internet residencial confirmada para 2027. Não inserir registros no DATA26A apenas com datas pretendidas e características genéricas. A consulta individual com valor total, condições e disponibilidade continua pendente; não alteramos o histórico D-004 nem o orçamento.

### Custo de vida — transporte urbano comparável, referência de 2026
Consulta 28/11/2026. Selecionar produto mensal avulso de adulto em tarifa cheia, sem subsídio social, anual, patronal ou de residência presumido. Valores por pessoa por mês, não preço para casal nem previsão de 2027. Condições de início/fim de validade podem variar; não multiplicar automaticamente por dois meses.

| Base | Produto | EUR/mês | Observações e fonte |
|---|---|---:|---|
| Lille | ilévia 26–64 / tout public | 67,00 | Formulário oficial edição 01/08/2026, página 2; guia antigo de €63 não deve prevalecer. https://media.ilevia.fr/prod-cms/docs-utiles/guides%2Babo/abonnement-26-64-ans.pdf |
| Metz | LE MET' Liberté Mensuel 27–64 | 45,90 | Página de assinaturas consultada indica tabela de 01/07/2025 e valor publicado de €45,90; não usar tarifa permanente com compromisso anual. https://www.lemet.fr/abonnements/ ; https://www.lemet.fr/abonnement-27-64-ans/ |
| Nancy | Stan mensal 26–64 | 47,00 | Tabela 01/08/2026, mês calendário, cartão SimpliCités. Fins de semana e feriados gratuitos para todos. Não confundir com MixCités ou plano renovável. https://www.reseau-stan.com/titres-tarifs/tous-les-titres |
| Mulhouse | Soléa mensal 26–64 | 47,00 | Página oficial de títulos, passe válido necessário. https://www.solea.info/en/titres-tarifs/abonnement-tickets/tickets ; https://e-boutique.solea.info/products/pass-mensuel-26-64 |
| Strasbourg | CTS tarifa cheia 26–64 | 56,00 | Acesso a TER urbano condicionado à residência e contramarca; não presumir elegibilidade. https://www.cts-strasbourg.eu/fr/acheter/nos-titres/titres-reguliers/abonnement-tarif-plein/ |

Resultado: **5/5 preços mensais urbanos documentados como referências contemporâneas**, não disponibilidade/tarifas 2027. Cesta local completa ainda não comprovada; faltam preços locais comparáveis de supermercado, restaurante, lavanderia e alternativas de internet. Não atualizar snapshot histórico, não somar componentes incompatíveis. As novas referências permanecem documentadas neste relatório até haver contrato de projeção existente apropriado sem adulterar o histórico.


### Mobilidade regional e última milha — consulta 28/11/2026
- Alsa+ Groupe Journée, fonte oficial TER Grand Est: €45 Alsácia, €28 por departamento (Bas-Rhin ou Haut-Rhin), €7,20 por zona urbana de Strasbourg, Colmar ou Mulhouse. Preços por grupo de 2–5, segunda classe, um sábado/domingo/feriado escolhido; rede coletiva da zona adquirida, incluindo TER elegíveis. Não assumir cobertura TGV, reserva ou validade em 2027. Útil para comparar Colmar a partir de Mulhouse e Strasbourg; o passe departamental Haut-Rhin não cobre Strasbourg. Fonte: https://www.ter.sncf.com/grand-est/tarifs-cartes/tarifs-regionaux/alsa%2B-groupe-journee
- Luxemburgo: autoridade nacional confirma gratuidade doméstica em segunda classe, inclusive as exceções ferroviárias Athus, Audun-le-Tiche e Volmerange-les-Mines. Não extrapolar para Metz/Nancy. Fonte: https://www.mobiliteit.lu/en/tickets-page/fares/
- RegioZone €3 por duas horas ou €5 por dia (até 04:00 seguinte), exclusivamente ônibus transfronteiriços elegíveis; não vale para trens internacionais. Não inserir como tarifa ferroviária. Fonte: https://www.cfl.lu/en-gb/ticket/international/grande-region/regiozone-1-ou-2-%282%29
- Pass Groupe Week-End: reconfirmado preço de €40 por grupo/dia e reserva gratuita limitada para TER Paris. FAQ atual da operadora inclui Basel e Luxemburgo, enquanto a página turística Explore Grand Est ainda contém exclusão transfronteiriça de lançamento; prevalece a regra da operadora, sujeita à verificação do serviço específico. Fontes: https://www.ter.sncf.com/grand-est/tarifs-cartes/tarifs-regionaux/pass-groupe-week-end ; https://www.explore-grandest.com/en/offerings/activities/city-adventures/weekend-group-pass-for-group-travel-in-the-grand-est-region/
- Referências de produto e transporte local, não cotações datadas; nenhum ganho nos denominadores de cobertura ferroviária/tarifária. Ainda faltam serviços de ida/retorno datados para Colmar/Luxemburgo e acesso efetivo às atrações.
