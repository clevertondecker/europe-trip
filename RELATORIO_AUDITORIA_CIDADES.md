# Auditoria de confiabilidade — cidades-base | 14/11/2026

## Resultado executivo

**Não existe evidência suficiente para decidir a cidade-base ou reservar o imóvel com os valores atuais.** O ranking 0–5 é reproduzível matematicamente, mas suas notas são *editoriais*, não medidas independentes. As quatro cidades têm 0 orçamentos verificáveis para as datas exatas de setembro–novembro/2027. O modelo NÃO permite que o ranking histórico se apresente como decisão concluída.

## Conferência direta da planilha original

| Cidade | Nota editorial | Aluguel €/mês (aba 11) | Aluguel com contas €/mês (aba 14) | Referência 2 quartos mercado tradicional, abr/2026 |
|---|---:|---:|---:|---:|
| Mulhouse | 4,375 | €980 | €790 | €620 |
| Strasbourg | 4,360 | €1.130 | €1.050 | €901 |
| Metz | 4,190 | €1.000 | €880 | €724 |
| Nancy | 3,935 | €900 | €790 | €603 |

A última coluna provém do barômetro público `123Loger` (mercado residencial convencional, NÃO temporada). Valores divergentes nas abas refletem modelos e premissas distintas; não devem ser fundidos nem tratados como estimativas estatísticas. Os €980/€1.130/€1.000/€900 não são médias de três ofertas comparáveis.

## Descobertas por cidade

### Mulhouse — insuficiente para a decisão
Três referências na aba 15: 40m² €750, 78m² €900 (fora da faixa preferida), 48m² €1.350. A última diz duração de 1–10 meses, mas verificar elegibilidade do contrato e noites de setembro–novembro/2027; o aluguel de €750 tem caução de €1.200 na observação histórica. Boa geografia editorial e orçamento potencialmente favorável, mas qualidade de vida e transporte nas noites após trabalho remoto não foram comparados por bairro. Conferir total de 2 meses, contas, internet, caução e contrato.

### Strasbourg — insuficiente para a decisão
Aba 15 lista 50m² €950 e 38m² €850. A primeira pode ter ajuste de eletricidade; ambos sem disponibilidade válida para as datas específicas do casal. Rede CTS e TER documentadas em fontes oficiais; isso não significa que roteiros desejados tenham preços e horários validados para 2027. Vida urbana bem classificada editorialmente, sem pesquisa reproduzível por bairro/rotina.

### Metz — insuficiente para a decisão
A opção útil observada é Rue du Maître Échevin, 80m² por €1.250, com despesas possivelmente adicionais. A planilha também tem residência estudantil indisponível de €650 (excluída) e imóvel de 15m² de €700 (excluído por inadequação). **Amostra de aptos elegíveis muito limitada.** Acesso ferroviário a Nancy, Thionville/Luxemburgo é promissor, mas faltam deslocamento Itália→base, retorno Brasil e excursões finais.

### Nancy — insuficiente para a decisão
Aba 15 tem 60m² por €850, mas o texto de anúncio também traz €730 + €100 = €830 (divergência), caução histórica de €1.400; outro de 32m² por €660 com ocupação e duração pendentes. Stan publica modalidades de transporte, inclusive regras especiais para fins de semana, mas falta estimativa concreta para os deslocamentos do casal.

## Revisão de fonte externa

- França, fonte oficial: `bail mobilité` requer circunstância elegível; não presumir elegibilidade de empregado remoto brasileiro. Consultar https://www.service-public.gouv.fr/particuliers/vosdroits/F34759?lang=fr
- França, fonte oficial: `meublé de tourisme` é regime diferente; verificar contrato e limite de hospedagem. https://www.service-public.gouv.fr/particuliers/vosdroits/F2045
- Observação de anúncios em HousingAnywhere, 14/11/2026: exemplos ainda apareceram em buscas de Mulhouse, Strasbourg e Metz, alguns com datas início de 2027. Isso **não prova oferta para setembro–novembro/2027**, nem preço total de 55–65 noites.
- Transporte: TER Grand Est descreve linhas Nancy–Metz e Nancy–Strasbourg. CTS Strasbourg e Stan Nancy publicam suas tarifas, mas são dados válidos à época da consulta, não horários e preços de 2027.
- Numbeo e demais índices colaborativos: coberturas diferentes, algumas pequenas; não fazer uma classificação estatística com base em pontuações e amostras desiguais.

## Lacunas globais bloqueantes
1. Pelo menos 3 imóveis realmente elegíveis/confirmados por cidade por 55–65 noites.
2. Custo *all-in* para duas pessoas, distinguindo caução reembolsável de gasto definitivo.
3. Comparação de supermercado, restaurantes, internet, academia, transporte urbano e lazer no mesmo padrão em todas as cidades.
4. Cinco excursões desejadas por base com horário real de retorno, custo casal e trânsito porta-a-porta.
5. Conexão desde a Itália e retorno ao Brasil com mala e deslocamentos.
6. Legalidade/adequação do contrato e política corporativa de trabalho no exterior.

## Normas futuras e execução
- Padrão dos oito gates: `data/city_research_audit_2026.json`.
- Guia de prompt: `PROMPT_AUDITORIA_CIDADES.md`.
- Validação automática: `city_research.py`, `tests/test_city_research.py`.
- O ranking original continua exploratório; nenhuma cidade é aprovada ou reprovada arbitrariamente.
