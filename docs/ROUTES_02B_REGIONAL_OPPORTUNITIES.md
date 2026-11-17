# ROUTES 2B — quatro descobertas regionais, sem afetar a comparação

**Implementação vinculada à especificação #111.** Piloto de **quatro propostas** em **dois corredores**, usando fontes turísticas oficiais consultadas em 17/11/2026. Não equivale a quatro passeios viáveis nem a quatro destinos adicionados ao catálogo.

| Corredor | Proposta | Fonte |
|---|---|---|
| Bélgica/Países Baixos | Maastricht (Basílica de São Servácio) | [Visit Maastricht](https://www.visitmaastricht.com/en/locations/2059606782/sint-servaasbasiliek-1) |
| Bélgica/Países Baixos | Leuven (Biblioteca Universitária) | [Visit Leuven](https://www.visitleuven.be/en/university-library) |
| Alsácia | Eguisheim | [Visit Alsace](https://www.visit.alsace/253000781-eguisheim/) |
| Alsácia | Riquewihr | [Visit Alsace](https://www.visit.alsace/en/sit/229000837-office-de-tourisme-du-pays-de-ribeauville-et-riquewihr/) |

**Risco P1:** local existe, mas serviço de trem, retorno e última milha permanecem desconhecidos. Nenhuma proposta pode contaminar a cesta fixa, influenciar ranking ou ser considerada selecionada. **P2:** propostas de nomes/aliases já presentes no catálogo falham na validação em vez de criar duplicação.

Código novo `regional_opportunity_research_model.py`, dados isolados em `data/regional_opportunities_pilot_2026_11.json`, testes de tamanho, fonte, deduplicação e flags de promessa. Reutiliza `build_destination_discovery()`, `load_research()` e `canonical_place()`; não modifica `ux502_destination_interests_model.py`, wishlist, `TripPlan`, bases ou orçamento.

**Aceite:** quatro fontes explícitas; 0 roteiros/tempos/retornos de 2027 alegados; nenhuma mudança no comparador ou dados existentes. Inclusão futura exige aceite manual + reconciliação e PR separado.
