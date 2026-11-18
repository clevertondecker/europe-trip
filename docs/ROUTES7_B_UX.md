# ROUTES 7B — comparador UX 5.0.5 com estimativas condicionadas

**Depende do PR #126.** Este PR não altera `compare_wishlist_bases()`, histórico, `TripPlan`, wishlist ou cidade-base oficial.

## Interface consolidada

A primeira distribuição da tela reflete **exatamente uma** destas categorias por combinação:
1. **Histórico de trem:** duração selecionada pelo adaptador legada, com divergências internas identificadas.
2. **Mínimo indicativo:** referência reconsultada de tempo mínimo por cidade, sem serviço nem estação comprovada, exibida com `~` e ressalva.
3. **Sem tempo:** sem histórico e sem nova referência reproduzida; não é inexistência de transporte.
4. **Local:** a mesma cidade nos dois lados; acesso urbano a pesquisar.

A matriz usa as mesmas quatro categorias. Os detalhes **já existentes** por destino agora distinguem fonte histórica, fonte da referência publicada, média de fonte atual e média do snapshot. O expander duplicado de 15 pares foi removido e títulos não presumem tamanho da seleção.

Uma diferença numérica entre o tempo histórico e o mínimo de página-resumo aparece como `outra referência indicativa`, **não** como conflito. Conflitos só podem ser concluídos entre fatos do mesmo serviço, estações, data e condições.

## Valores e limitações

- Exemplo com 3 bases × 5 destinos: 5 células históricas, 9 referências indicativas reconsultadas, 1 local, 0 sem tempo. São referências **por cidade**; 9 não significa 9 itinerários documentados.
- Média do snapshot Strasbourg → Belfort de 116 min foi preservada, mas a média reconsultada na SNCF é 106 min; as duas são mostradas no detalhe, com rótulos separados.
- Mínimo histórico Lille → Gand de 75 min permanece, referência Trainline de 68 min aparece como alternativa, sem classificação automática de conflito.
- Nenhum retorno, frequência de fim de semana, tarifa de casal, tempo porta a porta ou certeza de 2027 é inferido.

## CI e aceite

PR #127 começou empilhado sobre #126, que é o responsável por `data/routes7_priority_reference_2026_11.json` e `routes7_reference_model.py`. Sem alterar o workflow permanente, CI completo deve rodar **depois da integração da base #126 e do retarget para `main`**. Os testes cobrem 2–5 bases, 3 × 5, destinos fora do overlay, local, dados não reproduzidos, fonte/histórico simultâneos, diferenças numéricas que não são conflito, prioridades, wishlist e TripPlan.

**Aceite visual:** a tela explica a referência sem conhecimento de arquitetura, não mostra dois resumos contraditórios e mantém os detalhes em um único expander. Inspeção real desktop/mobile ainda será necessária se não houver navegador disponível.
