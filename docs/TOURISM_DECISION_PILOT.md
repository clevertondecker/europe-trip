# Piloto de decisão turística — três atrações já cadastradas

Pesquisa documental observada em **17/11/2026**, em **overlay isolado**; não cria catálogo duplicado e não altera qualquer item histórico original. É uma primeira amostra de como o fluxo Descobrir → Escolher → Comparar precisa evoluir.

| Atração | Informação concreta da fonte | Limite para 2027 |
|---|---|---|
| Catedral de Aachen | Visitas normais de seg–sex a partir de 11h, sáb 13h, dom 13h–17h45; entrada geral gratuita; visitas guiadas de adulto anunciadas a € 8,50 | Não confirma feriados, celebrações ou preço/horário de 2027 |
| Lichtentaler Allee | Parque externo gratuito e aberto 24h; endereço publicado | Não comprova tempo da estação nem condições de eventos de 2027 |
| Catedral de Strasbourg | Horários publicados em duas janelas seg–sáb e visita dominical; restrição durante ofícios e endereço do monumento | Não comprova visita em data concreta de 2027 nem ingresso de experiências separadas |

**Fontes primárias:** [Aachener Dom](https://www.aachenerdom.de/en/a-place-to-visit/faqs/), [Baden-Baden Turismo](https://www.baden-baden.com/en/nature/lichtentaler-allee), [Turismo Strasbourg](https://www.visitstrasbourg.fr/en/things-to-see-and-do/visiting/places-to-visit/historical-sites-and-monuments/f223007269_the-cathedral-of-notre-dame-strasbourg/).

**Escopo de dados:** `data/tourism_visit_evidence_pilot_2026_11.json`, `tourism_visit_evidence_model.py`, testes. IDs canônicos preexistentes: `dq32_aachen_07`, `dq32_baden_baden_27`, `strasbourg_cathedral`.

**P1:** entrada principal gratuita não torna visitas guiadas gratuitas; gratuidade e preço de atividade adicional são campos distintos. **P1:** horário genérico não é garantia para 2027, especialmente durante missas; `valid_for_2027=false`. **P2:** endereço publicado não implica caminhada/tempo desde estação; `station_to_attraction_min=null`. Não inventa duração de visita.

**Aceite:** 3 entradas oficiais válidas; campos de interesse e horário com fonte; nenhum preço/horário futuro confirmado; zero mutação de catálogo, wishlist e TripPlan. Segunda onda só com atrações selecionadas explicitamente.
