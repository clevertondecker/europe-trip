# ROUTES 6 — comparador com prontidão turística, logística e de moradia

Implementação independente da especificação #115. Na UX 5.0.5, a matriz de tempos históricos segue intacta; antes dela, o usuário agora vê **quantos atrativos têm dados de ingresso/horários**, e em um painel recolhido **as lacunas de hospedagem de cada cidade-base**. Há sempre a mesma cesta de destinos selecionada manualmente, sem recalcular prioridade nem escolher uma base.

`ux506_decision_readiness_projection.py` usa os contratos já existentes de `load_attractions()`, `load_research()` e `build_destination_discovery()`. Rejeita matrizes parciais/destinos fora do catálogo, diferencia editorial de dados publicados e nunca apresenta `null` como zero.

**Contratos de associação:** `compatible_evidence_association()` compara **estação de chegada**, **estação do retorno**, **direção**, **data** e **fonte** de trem/retorno/última milha. Uma associação com componentes compatíveis ainda **não calcula porta a porta**, porque falta hospedagem→estação, janelas completas da atração e garantia de 2027. Múltiplos modos e divergências devem ser avaliados nas camadas de pesquisa, não automaticamente somados na tela.

**P1:** soma de partes não compatíveis ou tempo até a porta fictício; duração total permanece `None`. **P1:** cidade que tem mais fontes virar vencedora; `winner_id=None` e `ranking_available=False`. **P2:** confundir foto/ingresso histórico com disponibilidade em 2027; UI rotula lacunas explicitamente. A ausência de informação nunca significa custo zero.

**Dependências:** estudo de #108; integração opcional futura com os novos módulos dos PRs #116, #119 e #120, após revisão conjunta. **Aceite:** 2–5 bases, cesta idêntica, seleção apenas em sessão, matriz ferroviária legada preservada, testes de associação com estação/direção/data e checks da UX; sem alteração de TripPlan, wishlist, dados históricos, nem escolhas.
