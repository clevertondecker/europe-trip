# DATA25 — Cobertura ferroviária prioritária: lote 1

## Recorte autorizado
Em 25/11/2026 o responsável autorizou a pesquisa prioritária de Lille, Metz, Mulhouse, Nancy e Strasbourg. Offenburg e Trier continuam no catálogo e na auditoria histórica; D-004 permanece aberta. Não alterar TripPlan, orçamento, Drive ou wishlist.

## Implementação e critério de seleção
A auditoria DATA24 mostrou Annecy sem tempo de ida em todas as cinco bases. Começar por esse destino comum para obter um lote comparável, sem supor que faça parte da wishlist privada. As cinco páginas SNCF foram consultadas em 25/11/2026; mínimos publicados por cidade, sem data de serviço nem retorno verificado. Não converter em bate-volta, preço ou itinerário. Reusar validador e projeção compartilhada, após todos os overlays existentes; manter datasets históricos congelados.

| Base | Mínimo publicado de ida | Fonte |
|---|---:|---|
| lille | 5h42 | [SNCF](https://www.sncf-connect.com/train/trajet/lille/annecy) |
| metz | 6h03 | [SNCF](https://www.sncf-connect.com/train/trajet/metz/annecy) |
| mulhouse | 5h52 | [SNCF](https://www.sncf-connect.com/train/trajet/mulhouse/annecy) |
| nancy | 6h13 | [SNCF](https://www.sncf-connect.com/train/trajet/nancy/annecy) |
| strasbourg | 6h37 | [SNCF](https://www.sncf-connect.com/train/trajet/strasbourg/annecy) |

## Aceite
Cinco pares antes sem tempo passam a indicativo; nenhum outro par alterado, fonte e direção validadas, sem promoção a histórico ou viabilidade, paridade DATA24/comparador/perfil/DQ32; regenerar relatório e executar CI no HEAD. Sem painel novo. Lote parcial, não conclusão de todas as lacunas. As médias publicadas não foram incorporadas neste contrato, e retorno, tarifas, última milha e datas de 2027 continuam desconhecidos.

## Roadmap proposto após este lote
- DATA25: completar os demais pares relevantes, sem preencher matriz indiscriminadamente; comparar datas/retornos quando disponíveis.
- DATA26: moradia mobiliada e custo total de 56–60 noites, duas pessoas, taxas e caução separados; sem confundir anúncio histórico com reserva.
- DATA27: vida cotidiana, cesta homogênea, transporte urbano e serviços.
- DATA28: trabalho remoto, internet residencial e coworking compatível com expediente.
Reutilizar os contratos vigentes e as telas existentes; sem ranking ou nova decisão oficial.
