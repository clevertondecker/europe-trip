# UX124 — Ficha única de cidade-base

Atue como Staff Software Engineer, Principal Product Designer e especialista Streamlit/Python no repositório Nossa Europa 2027.

## Objetivo
Consolidar Conhecer cidade e os detalhes individuais do explorador legado em um único renderer, com seis assuntos: Visão geral, Moradia, Logística, Vida cotidiana (inclui clima), Trabalho remoto, Atrações. Preservar foto, favoritos, mapa, simulação e retorno contextual. Não criar uma segunda wishlist, TripPlan, persistência ou comparador.

## Contratos
- Usar o catálogo dinâmico de bases (34 hoje), inclusive candidatas sem suporte oficial. Nenhum score editorial.
- Para logística, usar build_wishlist_matrix + decorate_comparison, os mesmos contratos de UX87/97. Projetar o catálogo inteiro apenas em memória e separar os desejos reais da navegação da ficha. Excluir local do denominador de trens; distinguir histórico, indicativo, local e sem tempo. Não inferir ida/volta, tarifas, acessibilidade ou horários de 2027. Preservar referências regionais fora do catálogo separadamente.
- Consolidar moradia com observed_housing; manter amostras de outras fontes separadas, não misturar medianas. Preservar bairros, anúncios e links, auditoria histórica e restrições contratuais.
- Preservar população municipal/ano/fonte, vida cotidiana, refeições, clima, coworking, modalidade e compatibilidade noturna, passes urbanos, fontes de logística e atrações. Tratar ausência como não pesquisado, nunca zero monetário.
- Manter evidências de acesso local e atrações DATA23 com fotos e créditos existentes. Usar IDs canônicos; não simular fotos de imóveis ou atrações sem imagem.
- Não coletar novos dados, alterar o orçamento, apagar dados, alterar identidade/estudos privados ou iniciar DATA24.
- Retirar código de renderização e ponderação substituído. Preservar modelos/validadores usados por outros fluxos. Entrada temporária UX123 deve usar o mesmo componente da ficha.
- Testar paridade ferroviária, todas as cidades, dados escassos, navegação por assuntos, ausência de mutação, retorno e integração existente. Atualizar testes que verificavam UI obsoleta sem enfraquecer contratos. CI verde antes do merge. QA visual real e produção devem ser explicitamente identificados como não realizados se indisponíveis.

## Aceite
Uma ficha única com abas nativas, sem ranking e sem cesta fixa de 15 como indicador atual. Nenhum dado de origem alterado. A auditoria técnica global e a retirada definitiva das entradas temporárias permanecem DATA24/UX125.
