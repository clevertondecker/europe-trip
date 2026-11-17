# Auditoria estratégica de prontidão para decisões — Nossa Europa 2027

**Escopo:** revisão documental, em 17/11/2026, das fontes atuais da `main` no commit `cdffbd898d4ff904c3fce0771494497532f44f83`, mais a auditoria histórica do PR #108. **Não** confirma preços, serviços nem disponibilidade para setembro–novembro de 2027; **não** altera código de produção, o `TripPlan`, a wishlist, a shortlist nem a cidade-base oficial.

## A pergunta de produto
Para duas pessoas, após 04/09/2027, com lua de mel na Itália, 56–60 noites europeias, trabalho remoto durante parte da estadia, fins de semana para passeios, transporte público e cenário global de R$ 60–70 mil:
1. **Quais lugares queremos visitar?** Conhecer custo, horário, duração, sazonalidade, natureza da experiência e restrições.
2. **Quais passeios são realmente possíveis?** Ida, retorno, última milha, abertura e tempo útil compatíveis para datas concretas.
3. **Qual cidade-base é viável para morar?** Moradia por 56–60 noites, infraestrutura de trabalho remoto, mobilidade cotidiana e custo integral para o casal.
4. **Cabe no orçamento global?** Não contar custos faltantes como zero, evitar somar passagens/passeios já provisionados e distinguir caução recuperável de despesa.

A UX segue **Descobrir → Interesses → Comparar bases → Montar roteiro → Revisar orçamento**. A cesta comum deve ser fixa por cenário e não pode ser expandida automaticamente por descobertas regionais.

## Baseline recalculado do snapshot consultado

| Métrica | Resultado | Interpretação |
|---|---:|---|
| Cidades-base em `base_city_research_expanded_2026_11.json` | 30 | 12 na shortlist de pesquisa; não são escolhas oficiais de moradia |
| Destinos na projeção `build_destination_discovery()` e PR #108 | 46 | Projeção de catálogos, não 46 viagens viáveis |
| Atrações no catálogo `attractions_2027.json` | 65 | Cada uma tem título, resumo, fonte e duração editorial |
| Observações DQ3.2 | 30 | Uma alias explícita, `dq32_luxembourg_city_22 → lux_bock` |
| Atrações distintas reconciliadas | 94 | 65 originais + 29 adicionais; nunca 95 itens distintos |
| Ingressos do catálogo principal com valor publicado | 4 | Referências históricas em EUR/CHF; **não** preço cotado para datas de 2027 |
| Durações editoriais de visita no catálogo principal | 65 | Nenhuma duração foi validada como observação real de visita |
| Horários de funcionamento no catálogo principal | 0 | Critério bloqueante para planejamento de janelas |
| Coordenadas específicas de atrações no catálogo principal | 0 | Há coordenadas de **destinos**, não equivalentes a portas de atrações |
| Fotografias específicas de atração no catálogo principal | 0 | Fotografia de destino/cidade não demonstra a mesma atração |
| Durações e preços novos na DQ3.2 | 0 | 30 observações apenas com identificação/categoria/fonte |
| Referências históricas de moradia no registro das 30 bases | 35 | Apenas 6 têm link direto de anúncio; outras usam índices de catálogo |
| Moradias com 56–60 noites e disponibilidade 2027 verificadas | 0 | 0 taxas totais confirmadas; 0 internet verificadas; 0 proximidades de estação verificadas |
| Pares base × destino (PR #108) | 1.380 | 54 tempos históricos; 25 parciais; 1.271 sem pesquisa; 30 locais sem tempo |
| Pares base × atração (PR #108) | 2.820 | 0 durações completas porta a porta |
| Referências de acesso canônico DQ3.0 | 2 | Endereço/ponto urbano, **sem** duração ferroviária→porta |
| Exemplo de nove pares do PR #108 | 9 | Exemplo **manual/curado**, validado contra as respectivas linhas da matriz exportada |

**Nota de qualidade:** `ticket.status=not_applicable` (27 atrações principais) se refere ao ingresso da visita ao espaço externo; não garante atividades internas gratuitas. Outros 34 ingressos seguem desconhecidos; 4 possuem montante publicado. Em 4 atrações há informação parcial de sazonalidade. `reservation_required` não está preenchido para as 65 atrações principais.

## Matriz de decisões: artefatos anexados neste PR

- `tourism_decision_readiness_94.csv`: uma linha por **atração reconciliada**, com identidade, cidade/país, tipo de fonte, data, estados de descrição, motivo de visita, fotos de atração versus destino, endereço, coordenadas, horários, fechamentos, sazonalidade, duração editorial, preço/unidade, reserva, estação, última milha e prioridade condicional à seleção. Valores desconhecidos são **unknown**, e não zero. O arquivo é uma **projeção estática feita para esta revisão** dos datasets acima, não foi adicionado ao gerador original.
- `housing_decision_readiness_30.csv`: uma linha por **base cadastrada**, informando volume de observações históricas, links diretos, casal, 56–60 noites, disponibilidade 2027, taxas, internet, estação, trabalho remoto e total da estadia. Também é **projeção estática desta revisão**, não dado primário.
- Os arquivos anteriores `city_base_destination_matrix.csv`, `city_base_attraction_matrix.csv`, `attraction_access_gaps.csv`, `city_base_summary.csv` e `summary.json` permanecem intactos.

**Privacidade:** o audit não acessou nem publicou a wishlist individual, que é um documento versionado separado. A relevância da atração para os desejos do casal aparece como `unknown_private_not_accessed`; converter esse campo em prioridade real requer escolha explícita ou uso privado autorizado dos interesses.

## Frente A — qualificar o que desejamos visitar (primeiro piloto)
Começar por **2–3 destinos já cadastrados** e atrações escolhidas explicitamente, antes de propor dezenas de destinos novos. Para cada atração incluir:
- Identidade canônica e aliases; motivo real de visita, descrição objetiva, fonte e data; contexto/foto específica com atribuição; endereço, entrada e referência de coordenadas com precisão.
- Horário por dia da semana, dia de fechamento, feriados, sazonalidade set.–nov., duração e natureza da estimativa, necessidade/prazo de reserva, restrições.
- Preço **por pessoa** e **por casal**, moeda, categoria (adulto, concessão, pacote, ida/volta etc.), condições, validade e custos adicionais.
- Acesso pesquisado por estação e modo, incluindo horários de transporte urbano; duas atrações próximas não significam a mesma visita sem confirmação de ligação.
- Cada campo usa estado independente `verified | historical | editorial_estimate | partial | unknown | not_applicable`, `source_url`, `checked_at` e validade. `verified` não equivale a “válido para 2027” sem período específico.

**Gatilho de aceite:** ficha suficiente para decidir “quero visitar?” sem exigir ainda bate-volta; registrar fontes ausentes e incógnitas sem inventar dados. Não criar segundo catálogo nem alterar a wishlist.

## Frente B — moradia e cotidiano antes de eleger uma base
Para cada cidade **já cadastrada** na comparação priorizada, pesquisa de apartamento mobiliado para **dois adultos, 56–60 noites**, com datas explícitas **após 04/09/2027**: link direto, disponibilidade, aluguel total, taxas obrigatórias, limpeza, depósito (exposição de caixa separada), política de cancelamento, cozinha equipada, lavanderia, internet comprovada e área de trabalho. Estimar **porta do imóvel→estação/mercado/transporte**, nunca apenas proximidade nominal ou distância em linha reta. Incluir vida cotidiana, serviços, transporte urbano, segurança contextual, legislação oficial de residência/trabalho remoto e cobertura adequada para orçamento. Há 22 notas `research_updates`, mas todas têm `score_eligible=false`; **não** constituem score comparável.

**Gatilho de aceite:** dados suficientes para comparar custo total e condições práticas nas mesmas datas para o casal. Sem três opções comparáveis por base ou critério material de trabalho remoto, sinalizar decisão pendente; não declarar vencedora. Não somar as 15 observações de outro dataset às 35 sem deduplicar IDs/links e períodos.

## Frente C — fins de semana e custo real do passeio
A primeira cesta sintética atual é Mulhouse, Strasbourg, Lille × Aachen, Baden-Baden, Colônia (9 pares). Uma vez explicitada e, se desejado, substituída por interesses consentidos:
- Pesquisar origem no imóvel, estação, serviço de ida, transferências, destino, modo urbano, horário de atração, duração de visita, tempo útil, última viagem de volta e chegada à base.
- Não classificar “bate-volta viável” somente por encontrar uma ida e uma volta; horários, datas, direções, estações, serviços e funcionamento da atração devem coincidir.
- Calcular custos somente com segmentos compatíveis e tarifas verificadas. Bilhete “desde” e passe promocional não são tarifa ordinária garantida. Alocação de despesas **por visita**, evitando duplicar trem para várias atrações no mesmo destino.

## Governança, rastreabilidade e reprodutibilidade

**Versões de fonte (Git blob SHA, snapshot de 17/11/2026):**
- `data/attractions_2027.json`: `6354e3c837bd0bf181e3fca7537b58509707bd43`
- `data/dq32_macro_tourism_2026_11.json`: `6ed2fe387901374e608937d701140bd6442b1e01`
- `data/base_city_research_expanded_2026_11.json`: `9c5a8bdf3343a64eeb3188c6ec4fbea8e1101ddf`
- `data/five_base_comparison_evidence_2026_11.json`: `ad2cf963feb4efca67d356a7df6317d2336388f6`
- `data/dq30_mobility_pilot_2026_11.json`: `33b36c7b6b6c98235ae00a30a24d0349f6cab01c`
- `data/exploration_bases_2027.json`: `142a34e8482f7bff5684f161c8242785aa9d20da`

**Validação efetivamente realizada:** leitura das quatro matrizes CSV originais; 1.380 chaves `base_id+destination_id` distintas, 2.820 chaves `base_id+attraction_id` distintas e 94 `attraction_id` distintos; contagens `historical_time=54`, `partial=25`, `not_researched=1271`, `local=30`; todas as nove linhas do exemplo curado correspondem à matriz completa em estado e duração histórica.

**Validação ainda pendente:** não foi possível executar o gerador Python em checkout local neste ambiente, portanto **não está comprovada a reprodução byte a byte** dos artefatos via regeneração. O script atual ainda fixa `assert len(bases)==30`, `len(destinations)==46`, `len(rail_rows)==1380`; um PR futuro de **manutenção da auditoria**, separado da aplicação, deve substituir esses invariantes por verificações derivadas dos inputs, preservar IDs únicos e comparar hashes após regeneração.

Procedimento de verificação para o revisor no checkout do PR #108:
```bash
python scripts/audit_rail_and_attraction_gaps.py
git diff --exit-code -- docs/audits/2026-11-17-rail-attraction-gaps/README.md \
  docs/audits/2026-11-17-rail-attraction-gaps/city_base_destination_matrix.csv \
  docs/audits/2026-11-17-rail-attraction-gaps/city_base_attraction_matrix.csv \
  docs/audits/2026-11-17-rail-attraction-gaps/attraction_access_gaps.csv \
  docs/audits/2026-11-17-rail-attraction-gaps/city_base_summary.csv \
  docs/audits/2026-11-17-rail-attraction-gaps/summary.json
```
Os dois CSVs de decisão **não** são escritos por esse script e devem continuar declarados como projeções manuais do snapshot de fonte, até existir gerador determinístico aprovado.

## Matriz de riscos e ordem incremental proposta
| Fase | Artefato | Risco principal P1/P2 | Aceite mínimo |
|---|---|---|---|
| 0 | #108 auditoria | P1 falso senso de completude; P2 snapshot sem versão | Contagens, identidade, fontes, limites e reprodução documentados |
| 1 | #109 contratos | P1 confusão entre existência, prova e validade | Estados independentes; conflitos e compatibilidade preservados |
| 2 | Novo PR **futuro**, ainda não aberto: enriquecer atrações desejadas | P1 passeio “atraente” sem horário/custo | Fichas verificadas em pequena cesta, sem duplicar catálogo |
| 3 | #114 piloto ferroviário nas bases já cadastradas; #112 retorno; #113 última milha | P1 falso bate-volta | Ida/retorno/acesso com identidade e calendário coerentes |
| 4 | Novo PR **futuro**, ainda não aberto: moradia/trabalho remoto | P1 base escolhida sem aluguel viável | Cotações datas do casal e infra real; lacunas explícitas |
| 5 | #115 projeção de comparação | P1 estimativa completa falsa | Campos de decisão e bloqueios visíveis; sem vencedor automático |
| 6 | #110 alternativas regionais, depois #111 propostas novas | P2 expansão antes de fechar o primeiro caso | Separar cadastradas/exploratórias e shortlist congelada |

**Condição de produto:** nenhuma cidade-base pode parecer superior apenas porque acumulou mais registros históricos. Antes de expandir significativamente bases/destinos, testar se a jornada atual responde corretamente às decisões reais no piloto.
