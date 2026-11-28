# DATA26C — Cobertura documental das cinco bases prioritárias (PR único)

## Papel e objetivo
Atue como Staff Software Engineer, Data Quality Engineer e Principal Product Designer. Consolidar neste PR o escopo original DATA26C e os incrementos antes planejados DATA27–31/UX134. Aprofundar Lille, Metz, Mulhouse, Nancy e Strasbourg com fontes rastreáveis; nenhuma nova hierarquia, motor de ranking ou estimativa financeira automática.

## 1. Baseline e denominadores
- Registrar HEAD/base, data e catálogo efetivo. Usar DATA24/UX132 e RESEARCH_BASE_IDS; inventariar todos os pares dirigidos não locais das cinco bases, inclusive destinos difíceis e lacunas. Congelar a lista de IDs do baseline para comparação antes/depois; se catálogo mudar, relatar o efeito separadamente. Não retirar destinos para melhorar percentuais.
- Manter o universo global DATA24; os 32,1% da interface são cobertura de tempos de ida global, não cobertura total do projeto.
- Preservar o universo tarifário histórico DATA26B/C de 60 pares (inclui Bern como endpoint ferroviário fora do catálogo turístico); se expandir tarifas para todos os destinos, registrar universo adicional, sem redefinir a métrica antiga.
- Atrações, última milha e custo de vida têm denominadores próprios. Destinos únicos são contados uma vez; comparar escopo igual entre bases. Não calcular nota média entre domínios.
- Gerar inventário de lacunas por par, por base e por campo, com classificação pendente, consultada sem evidência, não aplicável justificada, documentada. Consulta sem resultado não é cobertura.

## 2. Transporte ferroviário (prioridade)
- Completar tempos de ida: meta >=95% por base, buscar 100% quando fonte confiável existir. Reusar a cadeia de projeção DATA24/REC02 e modelos de evidência existentes; acrescentar dados, não alterar critérios do motor ou prioridades.
- Pesquisar direção, país, estações, mínimo, tempo típico definido metodologicamente, conexões e modalidade de todos os trechos. Não duplicar ida como retorno, usar distância como tempo, inferir estação por slug ou aceitar ônibus como trem.
- Para ida/volta, usar amostra comum de sábado/domingo com antecedência comparável; consultar horários, identificadores, estações, conexões e preço total para dois adultos sem descontos presumidos. Registrar condições, taxas e reservas. Não atribuir disponibilidade 2027 às amostras de outra data.
- Completar DATA26C original: validar e reconsultar alegações históricas, registrar evidência real e lacunas. Meta indicativa 85–95% de preços no escopo de 60 pares; tentar ampliar depois, sem confundir calendário com cotação completa. Meta de horários documentados 85–95% no universo prioritário; publicar o denominador. Cotações completas: tentar cinco pilotos, uma por base, preencher contrato DATA26B somente se todos os campos suportados. Não fabricar valores quando o motor de reservas não expuser a resposta.
- Fontes oficiais SNCF/TER/OUIGO, DB, SBB, CFL, SNCB, Eurostar, NS International e operadoras aplicáveis. Verificar páginas efetivamente consultadas, data, modalidade, direção e extrato de evidência; links dinâmicos sem captura não são prova permanente.

## 3. Atrações e última milha
- Reusar catálogo e inventário UX132C1. Priorizar destinos do universo das cinco bases; listar lacunas por atração e campo. Documentar atrações com fonte oficial, endereço, ingresso, moeda, condições e data; distinguir gratuito comprovado, pago, desconhecido e não aplicável. Meta >=95% dos destinos com inventário e >=90% dos campos aplicáveis de preço/última milha, sem inventar duração de visita.
- Documentar estação até atração, modo e percurso de transporte público/a pé com fonte; separar distância e duração. Não confundir tempos ferroviários e porta a porta.

## 4. Morar e trabalhar
- Reusar UX132C2 e pesquisa de moradia vigente. Para as cinco bases, pesquisar anúncios mobiliados para duas pessoas, estadia de 56–60 noites, custo total/taxas/caução, disponibilidade, política de cancelamento, acesso a internet e serviços. Referência de aluguel mensal não é cotação da estadia.
- Comparar mesma cesta de supermercado, transporte urbano, internet, lavanderia e despesas de trabalho remoto. Meta >=95% de campos documentados ou lacunas explicitamente identificadas; não contar lacunas como dados. Três ofertas reais para cada base quando calendário permitir; se indisponível, conservar zero ofertas elegíveis 2027.

## 5. UX e auditoria
- Na visão geral e transporte, dar destaque à cobertura das cinco bases e manter a global com rótulo inequívoco. Exibir numerador/denominador e lacunas reais; sem ranking ou porcentagens ilustrativas na produção. Reutilizar detalhamento por cidade e domínios existentes.
- Preservar UX133 #279, SCOPE, DRAFT, CHOICE, TripPlan, wishlist, orçamento oficial, handoffs e persistência. Não introduzir fontes de verdade paralelas.
- Cada lote deve ter commit rastreável no mesmo PR, fontes verificadas e relatório antes/depois. Registrar lacunas e limitações técnicas em vez de forçar metas. Separar cobertura, pesquisa tentada e disponibilidade efetiva de setembro/outubro de 2027.
- Testar integridade, aliases, proveniência, direção, deduplicação, ausência de dados, paridade de projeção e AppTest. Confirmar CI no HEAD final e QA desktop/mobile quando disponível. Sem merge até aprovação explícita; manter draft enquanto os critérios de aceite não estiverem atendidos.

As metas são objetivos de coleta, não declarações de completude. Priorizar qualidade e comparabilidade antes de percentual.
