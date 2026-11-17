# Mapeamento de lacunas de logística e atrações

Auditoria do estado atual do catálogo (17/11/2026). Não houve consulta nova a operadores.

**30 cidades-base × 46 destinos = 1380 pares.**
**94 atrações distintas; 2820 combinações base × atração.**

| Estado | Quantidade |
|---|---:|
| Tempo histórico de ida cadastrado | 54 |
| Pesquisa parcial sem tempo | 25 |
| Sem pesquisa ferroviária cadastrada | 1271 |
| Deslocamento local, tempo desconhecido | 30 |

A cobertura não significa qualidade logística. Nenhuma atração tem tempo porta a porta verificável desde uma cidade-base. Todos os retornos completos de 2027 continuam pendentes.

## Situação por cidade-base

| Base | Ida histórica | Parcial | Sem pesquisa | Local | Aluguéis históricos | Cotações 2027 |
|---|---:|---:|---:|---:|---:|---:|
| Mulhouse | 8 | 5 | 32 | 1 | 3 | 0 |
| Strasbourg | 15 | 2 | 28 | 1 | 3 | 0 |
| Metz | 5 | 9 | 31 | 1 | 3 | 0 |
| Nancy | 4 | 9 | 32 | 1 | 3 | 0 |
| Colmar | 0 | 0 | 45 | 1 | 0 | 0 |
| Sélestat | 0 | 0 | 45 | 1 | 0 | 0 |
| Saint-Louis | 0 | 0 | 45 | 1 | 0 | 0 |
| Belfort | 0 | 0 | 45 | 1 | 0 | 0 |
| Besançon | 1 | 0 | 44 | 1 | 0 | 0 |
| Thionville | 0 | 0 | 45 | 1 | 0 | 0 |
| Haguenau | 0 | 0 | 45 | 1 | 0 | 0 |
| Saverne | 0 | 0 | 45 | 1 | 0 | 0 |
| Reims | 1 | 0 | 44 | 1 | 0 | 0 |
| Lille | 8 | 0 | 37 | 1 | 2 | 0 |
| Arras | 1 | 0 | 44 | 1 | 0 | 0 |
| Dijon | 3 | 0 | 42 | 1 | 3 | 0 |
| Freiburg im Breisgau | 0 | 0 | 45 | 1 | 3 | 0 |
| Offenburg | 5 | 0 | 40 | 1 | 3 | 0 |
| Kehl | 0 | 0 | 45 | 1 | 0 | 0 |
| Karlsruhe | 1 | 0 | 44 | 1 | 3 | 0 |
| Baden-Baden | 0 | 0 | 45 | 1 | 0 | 0 |
| Saarbrücken | 0 | 0 | 45 | 1 | 0 | 0 |
| Trier | 1 | 0 | 44 | 1 | 3 | 0 |
| Lörrach | 0 | 0 | 45 | 1 | 0 | 0 |
| Aachen | 1 | 0 | 44 | 1 | 3 | 0 |
| Arlon | 0 | 0 | 45 | 1 | 0 | 0 |
| Liège | 0 | 0 | 45 | 1 | 3 | 0 |
| Namur | 0 | 0 | 45 | 1 | 0 | 0 |
| Luxembourg City | 0 | 0 | 45 | 1 | 0 | 0 |
| Esch-sur-Alzette | 0 | 0 | 45 | 1 | 0 | 0 |

## Dados exportados

- city_base_destination_matrix.csv: todos os 1.380 pares; status, duração histórica e fonte, divergência, transferências e lacunas.
- city_base_attraction_matrix.csv: todas as combinações de base e atração; tempo ferroviário só quando documentado, nunca tempo até a porta.
- attraction_access_gaps.csv: todas as atrações, acesso urbano e fontes.
- city_base_summary.csv: todas as 30 bases com indicadores de cobertura.
- summary.json: estatísticas e proveniência da auditoria.

## Limitações

Tempo histórico de trem é estação a estação, não duração até museu ou monumento. Falta de evidência não prova inexistência de conexão. Os dados de 2026 não confirmam serviços, preços, horários, retorno ou aluguel para setembro–novembro de 2027. Nunca somar zero ou duração editorial de visita como deslocamento.

A referência de 15 minutos até o Musée Unterlinden, em Colmar, é um caso isolado fora da lista canônica e não pode ser generalizada para as demais atrações.

## Próxima pesquisa

Priorizar as cidades-base que o usuário está comparando e a cesta de destinos marcados como desejados; procurar operadoras oficiais, serviços de retorno de sábado/domingo, destino ferroviário preciso, transporte urbano e acesso a cada atração. Sem ranking automático.
