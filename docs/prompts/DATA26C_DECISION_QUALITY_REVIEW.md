# DATA26C — Revisão de qualidade para decisão (28/11/2026)
Complementa DATA26C_PRIORITY_RESEARCH_COMPLETE.md e o contrato DATA26C original. A ordem abaixo prevalece sobre metas de volume. PR #278 único, draft, sem merge até autorização.

## Checklist por domínio
- [ ] Auditar os 42 registros do HEAD 96917f5 (21 oficiais, 21 secundários): direção, identidade/país, mínimo e média da mesma versão, modalidade ferroviária, estação publicada, URL/data/limites. Preservar histórico; reconsulta divergente não é substituição automática. Páginas mistas exigem evidência ferroviária explícita; sem prova de todos os trechos, não promover a itinerário.
- [ ] Isolar a observação DATA26C da proveniência ROUTES7: nomes publicados distintos de IDs reconciliados, sem condições comerciais ou estações herdadas; testes de conflitos e precedência.
- [ ] DATA26B1: moeda, data, direção, unidade e modalidade na revisão; identidade de captura sem preço; duplicidade versus conflito versus captura distinta; separar legado, sobreposição, ganho líquido e progresso do lote. Preservar 60 pares e contratos DATA26B.
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
