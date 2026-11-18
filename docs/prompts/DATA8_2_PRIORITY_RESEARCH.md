# DATA 8.2 — Enriquecimento turístico priorizado (18 atrações)

**Papel:** Senior Tourism Research Analyst + Python Data Engineer.
**Base:** PR DATA 8.1. **Repositório:** `clevertondecker/europe-trip`.

## Executar
1. Auditar `build_destination_discovery()`, a matriz canônica e o piloto histórico `tourism_visit_evidence_model.py`.
2. Pesquisar de 15–20 atrações escolhidas no lote público: 18 IDs já conciliados entre Aachen, Baden-Baden, Bruxelas, Strasbourg, Lille, Belfort e Dijon. A wishlist real do usuário não está persistida no repositório; na UI a ordenação deve usar os interesses da sessão, sem fingir saber quais são.
3. Para cada atração: motivo para visita com fonte oficial, faixa editorial de duração com método, ingresso com classificação fiel, janela de abertura somente quando documentada, endereço somente quando documentado, data e URL por campo.
4. Não confundir áreas externas sem bilhete com ingressos interiores gratuitos. Não converter `unknown` em zero.
5. Diante da ausência de atrações canônicas de Colônia/Gand, adicionar apenas propostas documentadas `unreconciled_candidates` com ID `null`. Nunca modificar catálogo principal automaticamente.
6. Entregar JSON versionado, loader puro, testes para 18 IDs, cobertura e invariantes. Manter todas as evidências específicas de 2027 como pendentes.

## Fontes oficiais
Aachener Dom, Aachen Tourist Service, Baden-Baden Tourism, Visit Brussels, Visit Strasbourg, Lille Tourism, Belfort Tourisme, Dijon Tourism. Candidatas: KölnTourismus (Dom) e Visit Gent (Gravensteen). Registro completo por item no JSON.

**Aceite:** 18 itens conciliados, 2 candidatas sem IDs inventados, 18 faixas de duração explicitamente editoriais, só 3 regras de horário documentadas inicialmente, sem falsa promessa sobre 2027. Escopo aditivo; não modificar `TripPlan`, wishlist, `app.py` ou dados históricos.
