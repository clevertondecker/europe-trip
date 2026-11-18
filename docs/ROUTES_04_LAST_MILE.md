# ROUTES 4 — última milha por estação, atração, entrada e modo

Implementação separada do prompt #113.

O piloto documenta as duas referências de transporte/atração já pesquisadas como contexto e o foco em Aachen/Baden-Baden, **sem inventar minutos**. As três observações canônicas deste piloto têm duração `null` porque faltam estação precisa, rota, entrada e tempo verificado. Observações múltiplas de caminhada, bonde, ônibus ou outros modos são preservadas; `station_to_attraction_duration` só devolve número quando existe **uma** observação compatível e verificada. Se há rotas alternativas ou estação diferente, devolve desconhecido/conflito.

**Identidade em aberto:** a Catedral de Colônia não foi localizada nas atrações reconciliadas atuais e o Musée Unterlinden consta apenas como referência externa; ambas permanecem em `unreconciled_manual_notes`, sem ID canônico fabricado. O PR não duplica nem promove o catálogo.

- **P1:** falsa precisão por duração inferida, mistura de entradas/estações; exige origem documental, modo, entrada, estação e fonte.
- **P2:** deduplicação que perde alternativas, ausência tratada como zero; mantém coleção de observações, conflito explícito, nulos.
- **Contratos:** `build_destination_discovery()`, identidade canônica da atração, dados DQ30 existentes.
- **Aceite:** 3 referências parciais, 0 tempos inventados, testes de estação/entrada/modo, fontes, conflitos e dados não canônicos. Sem alteração dos 94 registros de atração, TripPlan, wishlist ou UI.
