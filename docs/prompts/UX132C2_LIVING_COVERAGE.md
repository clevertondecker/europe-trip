# UX132C2 — Cobertura documental de moradia, vida cotidiana, clima e trabalho remoto

Atue como Staff Software Engineer e Principal Product Designer especializado em Python, Streamlit, qualidade de dados e UX no Nossa Europa 2027.

## Contexto e dependência
UX132A #269 e UX132B #270 integrados. UX132C1 #271 introduz a composição independente ux132_coverage_page.py com Visão geral, Transporte ferroviário e Atrações turísticas. Este PR parte do HEAD 28b904c de #271; aguardar sua integração e sincronizar eventuais correções, retarget para main e validar diff exclusivo antes da implementação definitiva/merge.

## Objetivo
Acrescentar o domínio "Morar e trabalhar" à cobertura existente para identificar lacunas que dificultam a escolha de uma base de longa estadia, sem transformar a aplicação em plataforma de auditoria. Não pesquisar novos preços, não modificar dados oficiais, orçamento ou decisão D-004.

## Dados e recorte
- Reutilizar data24_d004_audit_model.py: project_d004, research_gaps e contagens. A auditoria atual cobre sete bases descritivas (união do snapshot histórico D-004 e estudo histórico de cinco bases), distinta das cinco bases prioritárias autorizadas em RESEARCH_BASE_IDS (Lille, Metz, Mulhouse, Nancy, Strasbourg). O recorte atual inclui também Offenburg e Trier. Nenhum é lista de finalistas oficiais.
- Apresentar cinco prioritárias por padrão, com opção "Todas as bases auditadas (7)" derivada do modelo, não fixar números. Denominadores correspondem ao recorte; não extrapolar resultados às 34 bases globais. Não classificar cidades fora do recorte como sem dados.
- Extrair, se necessário, somente a projeção não ferroviária compartilhada de D-004 (incluindo contagens), preservando exatamente contratos e resultados do relatório. O domínio especializado não deve executar rail_coverage, build_audit inteiro ou dependências de UI. Não preencher rail_by_base com dados inventados. Manter auditoria e aplicação na mesma fonte de verdade. Separar gaps ferroviários de gaps de moradia/vida cotidiana/trabalho; não alterar sua semântica original no relatório.

## Indicadores documentais
1. Moradia: bases com amostra histórica; número de ofertas únicas no conjunto canônico; bases com três cotações verificadas e comparáveis para 56–60 noites em 2027 (2 adultos); requisitos de imóvel privativo, mobiliado, taxas, caução, contrato, internet. Amostras EUR/mês não são cotações totais; mercado e pacotes podem repetir anúncios, não somar; ausência de cotação não prova indisponibilidade. Não assumir disponibilidade, preço, caução ou contrato.
2. Vida cotidiana/custo de vida: restaurante EUR/2 pessoas, passe urbano nominal EUR/pessoa/mês e cesta local completa comparável. Distinguir dados históricos, cesta parcial e premissas compartilhadas do orçamento. Não atribuir cesta compartilhada a uma cidade. Academia, lavanderia e demais serviços só recebem indicador próprio se existir contrato consistente de evidência; caso contrário marcar não medido ou apresentar lacuna já catalogada. Não inventar valores.
3. Clima: normais documentadas de setembro a novembro, com local, período/unidades e fonte. Não tratar normais como previsão para 2027.
4. Trabalho remoto: coworking pesquisado, modalidade/tarifas/horário quando documentados, compatibilidade histórica em três estados (compatível/incompatível/indeterminado) e confirmação para 2027 separada. Internet residencial verificada no imóvel para a estadia é distinta de infraestrutura geral, conexão anunciada ou coworking. Não inferir fuso, acesso contratual ou confirmação futura.
- Numerador e denominador para cada indicador; manter desconhecido, indeterminado, não aplicável e não medido semanticamente distintos. Não confundir 0 registros com 0 euros. Sem média geral, ranking ou nota por cidade.
- Valores, data e URL permanecem ligados ao registro que sustenta a evidência. Não atribuir fonte genérica ou data do dataset a um campo específico sem evidência. Links, detalhes e ressalvas sob divulgação progressiva.

## UX
- Na composição de Cobertura dos dados, acrescentar apenas um cartão compacto na Visão geral e uma opção "Morar e trabalhar" ao lado de Transporte e Atrações. Não criar nova página, hierarquia de abas ou nova ficha de cidade. Não mover navegação principal neste PR.
- Resumo com indicadores essenciais e acesso direto ao domínio. No domínio, recorte de bases, tabela compacta por cidade com indicadores de moradia/vida cotidiana/clima/trabalho remoto e um seletor por ID estável. Reutilizar helpers de busca/estado; somente adicionar filtro se ajudar a encontrar lacunas reais. Mostrar denominadores e recorte.
- Detalhe da cidade: distinguir requisitos ainda necessários para decisão, pesquisas complementares e referências suficientes apenas para contexto, seguindo research_gaps sem reclassificar arbitrariamente. Organizar quatro blocos compactos com campos, unidades e fontes específicas. Não repetir toda a tela Conhecer cidade, nem as lacunas ferroviárias já tratadas. Evitar quatro novos conjuntos de filtros.
- Preservar seleção e recorte entre domínios e ao retornar à área; recuperar seleção inválida. Estado de apresentação somente na sessão, independente de TripPlan. Preservar DRAFT, SCOPE, CHOICE, wishlist, orçamento, persistência e handoffs.

## Performance e manutenção
Visão geral carrega apenas resumo de cada domínio; detalhes somente a projeção correspondente. Medir projeção e detalhe no catálogo real; não introduzir cache ou framework preventivo. Evitar dependências bidirecionais e manter helpers pequenos. UX132C3 (reavaliação de navegação e consolidação) e DATA26 (novas pesquisas) ficam fora do escopo.

## Aceite
Testes de paridade com D-004 por campo e recorte, cinco vs sete, ausência de falsa lacuna em base não auditada, anúncios não duplicados, cotações/contrato não inferidos, contexto compartilhado não localizado, coworking três estados, internet residencial, normais climáticas, fonte/unidade/data e zero/None. Teste de atualização via fixture sem alterar dados oficiais. AppTest: acesso sem wishlist, troca de domínios, recorte e seleção inválida, preservação de estado e navegação real, isolamento de projeções e preservação do plano/escopo/handoffs. Manter regressões existentes. Medir tempos reais sem limiar frágil, verificar auditoria versionada, CI no HEAD final e QA visual quando disponível. Documentar limitações; manter draft, sem merge sem autorização específica.
