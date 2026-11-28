# DATA26C — Lacunas internacionais e cotações do casal

## Objetivo
Atuar como Staff Software Engineer e Data Quality Engineer. Evoluir incrementalmente a pesquisa do PR #277 (merge 629c590) usando o contrato de cotações do #276. Não criar nova página, ranking, estimativa financeira ou arquitetura paralela.

## Baseline e escopo
Preservar as cinco bases (Lille, Metz, Nancy, Mulhouse, Strasbourg) e os 12 destinos do DATA26B1–B4, denominador fixo de 60 pares dirigidos. Recalcular a união com legado elegível a partir dos dados reais antes da coleta: referência anterior estimada 19/60, 20 pendentes, 21 lacunas consultadas, zero cotações completas. Reportar eventual diferença, não fixar os números nos testes.

## Incrementos
1. Fechar pendências de qualidade do #277: validar IDs contra catálogo efetivo, países e aliases, metadados de review, distinção de observação de calendário e itinerário exclusivamente ferroviário. Preservar histórico sem promovê-lo a confirmação independente. Revisar classificação das lacunas e cobertura legada. Confirmar DATA24 inalterado.
2. Priorizar Metz/Nancy–Luxembourg (CFL/TER); Mulhouse/Strasbourg–Freiburg (DB/TER); Basel/Bern/Interlaken (SBB/DB/Lyria); Lille–Bruges/Brussels/Amsterdam (SNCB/Eurostar/NS International). Depois consultar demais pares pendentes. Registrar fonte oficial, direção, cidade/país, data de viagem e consulta, preço, moeda, modalidade e motivo de exclusão. Não extrapolar produto reverso, trecho parcial, ônibus, preço promocional sem condições ou calendário misto. Consultas falhas não equivalem a ausência de serviço.
3. Amostra piloto de ida e volta: tentar uma rota relevante por base (Lille–Brussels, Metz–Luxembourg, Nancy–Luxembourg, Mulhouse–Basel, Strasbourg–Freiburg). Usar mesmo fim de semana futuro disponível e antecedência equivalente, dois adultos sem descontos, classe equivalente quando comprovada. Pesquisar ambos os sentidos ou bilhete integrado. Registrar serviços, estações, horários com offset, conexões, preço total para dois adultos, taxas, reservas, elegibilidade, classe, reembolso e alteração. Não multiplicar preço individual ou ida para inferir total. Se não houver prova suficiente, documentar a lacuna e manter cotação desconhecida; só inserir no contrato #276 quando os campos tiverem evidência válida.
4. Reutilizar painel e projeções existentes; separar cobertura indicativa, modalidade comprovada, cotações completas e lacunas. Não alterar orçamento oficial, REC02, TripPlan, wishlist, DRAFT/SCOPE/CHOICE, persistência ou handoffs.

## Aceite
- Comparativo antes/depois por base e destino: denominadores, pares novos únicos, sobreposição, motivos de lacunas e cotações completas.
- Testes de contrato e fonte, alias/homônimo, proveniência de review, deduplicação, ausência de preço, separação de classes de evidência, AppTest não vazio, filtros e paridade DATA24.
- Registrar resultados reais de CI do HEAD final e QA visual (ou explicitar impedimento).
- Nenhum preço inventado; não confundir referência 2026/2027 com disponibilidade confirmada para a viagem de setembro/outubro de 2027.
- Manter draft durante pesquisa/implementação. Merge somente após autorização e validação.
