# Nossa Europa 2027 — Pesquisa ampliada de 30 cidades-base
Data: **15/11/2026** · Público: casal, viagem após casamento em 04/09/2027.

> **Estado real deste estudo:** triagem de 30 candidatas e 12 finalistas,
> com 35 referências de anúncios e seis amostras ferroviárias oficiais.
> A fase de ranking definitivo está **incompleta**: nenhum anúncio foi
> cotado/aceito para o mesmo intervalo de **56 a 60 noites em 2027**.
> Sem essa comparabilidade, publicar "melhor cidade" ou "total para 2 meses"
> seria criar uma precisão falsa. Não mudar `TripPlan` com esse estudo.

## 1. Escopo e conflitos de datas

- Data fixa do casamento: **04/09/2027**; viagem começa depois.
- Lua de mel na Itália, seguida de uma residência temporária na Europa.
- Modelo atual padrão: `total_days=70`, `italy_days=10` → **60 dias
  de França/segunda etapa**, coerente com a pesquisa de até 60 noites.
- O snapshot `data/trip.json` ainda permite cenários de **65 a 75 dias**
  de viagem total e descreve a segunda etapa como **55–65 dias**.
  Durações maiores que 60 noites de uma única base não foram aprovadas
  por esta pesquisa. Antes de cotar, fixar a entrada e saída real do imóvel.
- França historicamente preferida; comparar outros países em grupo separado,
  pois contratos, seguro, trabalho remoto, impostos e documentação mudam.

## 2. Trinta candidatas pesquisadas em triagem

**França (16):** Mulhouse, Strasbourg, Metz, Nancy, Colmar, Sélestat,
Saint-Louis, Belfort, Besançon, Thionville, Haguenau, Saverne, Reims,
Lille, Arras e Dijon.

**Alemanha (9):** Freiburg im Breisgau, Offenburg, Kehl, Karlsruhe,
Baden-Baden, Saarbrücken, Trier, Lörrach e Aachen.

**Bélgica (3):** Arlon, Liège e Namur.

**Luxemburgo (2):** Luxembourg City e Esch-sur-Alzette.

Triagem geográfica baseada em acesso potencial a países vizinhos,
estações e cidades turísticas. **Não são 30 cidades aprovadas nem 30
comparações completas de aluguel/ferrovias.**

### Doze finalistas para a próxima validação

| Cidade | País | 3 anúncios de 2026? | Menor / mediana / maior observados por mês | Qualidade da amostra |
|---|---|---|---|---|
| Mulhouse | FR | Sim | €980 / €1.350 / €1.360 | Heterogênea |
| Strasbourg | FR | Sim | €850 / €950 / €1.100 | Heterogênea |
| Metz | FR | Sim | €650 / €700 / €1.250 | Dois apartamentos muito pequenos; €650 é estudante/fiador |
| Nancy | FR | Sim | €660 / €850 / €1.140 | Taxas excluídas |
| Lille | FR | **Não: 2** | €840 / €875 / €910 (duas observações) | Não completar com Roubaix/Croix |
| Dijon | FR | Sim | €800 / €850 / €1.350 | Heterogênea |
| Offenburg | DE | Sim | €1.200 / €2.500 / €2.800 | Apartamentos grandes; forte dispersão |
| Freiburg | DE | Sim | €1.400 / €1.650 / €2.250 | Quartos/área muito distintos |
| Karlsruhe | DE | Sim | €1.290 / €1.550 / €1.790 | Wunderflats, 2 adultos nos exemplos |
| Trier | DE | Sim | €800 / €1.000 / €1.380 | Wunderflats, 2 adultos nos exemplos |
| Aachen | DE | Sim | €1.200 / €1.350 / €1.500 | Vários anúncios exigem **3 meses mínimos** |
| Liège | BE | Sim | €840 / €880 / €980 | Condições para 60 noites não verificadas |

**ATENÇÃO:** mediana é dos *anúncios escolhidos*, não renda mediana do
mercado e não preço mensal comparável por m²/serviços. Valores baixos de
Metz vêm de imóveis pequenos e contratos possivelmente inadequados;
valores altos de Offenburg são imóveis grandes. Não ordenar as cidades
como "mais baratas" por esta tabela.

Fonte estruturada com título, área, preço, tipo de despesas, indicação de
ocupação e URL: `data/base_city_research_expanded_2026_11.json`.

**Fontes do catálogo pesquisadas em novembro/2026**:
- [HousingAnywhere Mulhouse](https://housinganywhere.com/s/Mulhouse--France/furnished-apartments)
- [HousingAnywhere Strasbourg](https://housinganywhere.com/s/Strasbourg--France/furnished-apartments)
- [HousingAnywhere Metz](https://housinganywhere.com/s/Metz--France/furnished-apartments)
- [HousingAnywhere Nancy](https://housinganywhere.com/s/Nancy--France/furnished-apartments)
- [HousingAnywhere Lille](https://housinganywhere.com/s/Lille--France/furnished-apartments)
- [HousingAnywhere Dijon](https://housinganywhere.com/s/Dijon--France/furnished-apartments)
- [Offenburg temporário, ImmoScout24](https://www.immobilienscout24.de/Suche/de/baden-wuerttemberg/ortenaukreis/offenburg/wohnen-auf-zeit)
- [Wunderflats Freiburg](https://wunderflats.com/en/furnished-apartments/freiburg)
- [Wunderflats Karlsruhe](https://wunderflats.com/en/furnished-apartments/karlsruhe)
- [Wunderflats Trier](https://wunderflats.com/en/furnished-apartments/trier)
- [Wunderflats Aachen](https://wunderflats.com/en/furnished-apartments/aachen)
- [HousingAnywhere Liège](https://housinganywhere.com/s/Li%C3%A8ge--Belgium/furnished-apartments)

Alguns links individuais verificados mostram cláusulas relevantes:
- [Metz, Rue de Vercly](https://housinganywhere.com/room/ut1598487/fr/Metz/rue-de-vercly):
  preço mais recente €650/mês sem contas, visto em página individual;
  estudante e fiador, anúncio **indisponível** ao abrir detalhe.
  Essa observação histórica não serve como imóvel elegível.
- [Metz, Rue du Maître Échevin](https://housinganywhere.com/room/ut1639224/fr/Metz/rue-du-ma-tre-chevin):
  €1.250/mês sem contas, fibra mas contratação separada,
  aproximadamente 1,3 km até a estação; caução €1.200 e exigência
  de documentação. **Não cotado para 60 noites.**
- [Offenburg, Weidenstrasse](https://www.immobilienscout24.de/en/expose/170758812):
  €1.200/mês, mínimo de um mês, depósito apresentado; unidade grande,
  disponibilidade de 2027 precisa de nova verificação.
- [Offenburg, Händelstraße](https://www.immobilienscout24.de/expose/172439262):
  €2.500/mês, mínimo um mês, depósito €2.000. Não comparar com estúdio pequeno.
- [Wunderflats FAQ](https://wunderflats.com/en/help/post/75000062964):
  mínimo geralmente um mês, podendo ser maior por cidade, contrato ou imóvel.
  **Em Aachen, muitos anúncios da plataforma são para >=3 meses**.

**Nenhum desses casos foi reservado, e nenhum preço total 56–60 noites,
taxas, limpeza, câmbio, utilidades, cauções ou cancelamento foram aprovados.**

## 3. Ferrovias — estudo do operador para segunda 16/11/2026

| Origem → destino | Menor tempo publicado | TER/regional de referência | Média operador | Serviços na segunda |
|---|---:|---:|---:|---:|
| Offenburg → Strasbourg | 25 min (TGV) | ~29 min | 34 min | 27 |
| Strasbourg → Colmar | 25 min (TGV) | ~30 min | 31 min | 42 |
| Mulhouse → Basel | 20 min (TGV) | ~22 min | 27 min | 49 |
| Metz → Luxemburgo | 42 min | ~54 min | 54 min | 54 |
| Lille → Bruxelas | 34 min | não comparável | 35 min | 17 |
| Besançon → Dijon | 46 min (TGV) | ~55 min | 58 min | 29 |

**Não** utilizar isso como frequência aos domingos, chegada porta
a porta, último trem de volta, bilhetes 2027 ou preço final do casal.
Detalhe e origem de cada linha no arquivo
`data/base_city_rail_evidence_expanded_2026_11.json`.

Fontes oficiais:
[SNCF Offenburg–Strasbourg](https://www.sncf-connect.com/en-en/train/timetables/offenburg/strasbourg),
[SNCF Strasbourg–Colmar](https://www.sncf-connect.com/en-en/train/timetables/strasbourg/colmar),
[SNCF Mulhouse–Basel](https://www.sncf-connect.com/en-en/train/timetables/mulhouse/basel),
[SNCF Metz–Luxembourg](https://www.sncf-connect.com/en-en/train/timetables/metz/luxembourg),
[SNCF Lille–Brussels](https://www.sncf-connect.com/en-en/train/timetables/lille/brussels),
[SNCF Besançon–Dijon](https://www.sncf-connect.com/en-en/train/timetables/besancon/dijon).

### Transporte urbano/transfronteiriço que pesa na decisão

- [Deutsche Bahn Deutschland-Ticket](https://www.bahn.de/angebot/regio/deutschland-ticket)
  anuncia **€66,80/pessoa por mês a partir de 01/01/2027**, para o
  transporte regional/local elegível, como assinatura. Para duas
  pessoas e dois meses, **€267,20** *se* ambas assinassem e
  permanecessem durante dois meses tarifários completos. **Não**
  cobre automaticamente ICE/IC nem trechos transfronteiriços.
- [Luxemburgo](https://www.vdl.lu/en/getting-around/bus/routes-and-maps/free-public-transport-and-exceptions)
  mantém transporte público nacional de segunda classe gratuito.
  **Trens/ônibus internacionais até a França, Alemanha ou Bélgica
  não se tornam gratuitos por esse benefício.**

## 4. Ranking: pesos e impossibilidade atual de classificar

Modelo reproduzível: cada critério recebe uma nota **documentada de 0
a 100**, multiplicada por seu peso. Se um critério não puder ser medido,
a nota **não é imputada como 0** nem redistribuída a outras categorias.
O modelo informa `score_0_100=null`, cobertura em porcentagem e limites
teóricos (soma dos pontos conhecidos; soma dos conhecidos + pesos faltantes).

| Critério | Geral | Econômico | Explorador |
|---|---:|---:|---:|
| Habitação mobiliada de curta temporada | 30% | 40% | 20% |
| Trem/mobilidade | 25% | 20% | 30% |
| Destinos efetivamente viáveis | 20% | 15% | 25% |
| Custo do conjunto de passeios | 10% | 15% | 8% |
| Moradia e trabalho remoto | 10% | 7% | 7% |
| Países com acesso prático | 5% | 3% | 10% |
| **Total** | **100%** | **100%** | **100%** |

**Neste momento os 3 rankings definitivos continuam sem classificações.**
Isso não é falha no código: dados faltantes impossibilitam notar
objetivamente aluguel 2027, 15 destinos com volta real, custo padrão
para dois, e condições de morar e trabalhar. Atribuir "90/100" a uma
cidade seria **inventar** o resultado.

O modelo `base_research_expanded_model.normalized_score` já recebe
futuras métricas validadas e calcula os três pesos sem viés por dados
ausentes.

## 5. Comparações práticas preliminares (hipóteses de pesquisa)

**Offenburg × Mulhouse** — Strasbourg fica em ~29 min por TER
desde Offenburg. Mulhouse tem Colmar/Basel muito acessíveis.
Offenburg exige validar custos de apartamento realmente privativo;
Mulhouse tem anúncios menores/mais baratos, porém com elegibilidade
e condições variáveis. **Sem vencedor por custo total.**

**Strasbourg × Freiburg** — Strasbourg liga diretamente o corredor
Alsácia/TER; Freiburg serve de base alemã na Floresta Negra.
Exemplos Wunderflats em Freiburg tendem a custar mais que algumas
opções observadas em Strasbourg, mas o contrato final 60 noites não foi
comparado. **Sem vencedor.**

**Trier × Metz** — Trier tem apartamentos apresentados explicitamente
para 2 adultos a €800/€1.000/€1.380 nos anúncios escolhidos;
Metz tem amostras até €650 com perfil estudantil e imóveis pequenos,
não equivalentes. Luxemburgo é corredor relevante; horários,
tarifas de ida/volta e frequência de fins de semana precisam ser
levantados. **Sem vencedor.**

**Lille × Aachen** — Lille favorece Bélgica, Bruxelas e Amsterdam,
Aachen oferece proximidade à Bélgica/Países Baixos e passe regional
alemão. Em Aachen **a duração mínima de 3 meses é risco prático**;
em Lille a amostra é de apenas dois anúncios no município, não
podendo ser inflada com Roubaix. **Sem vencedor.**

**Dijon × Karlsruhe** — Dijon é candidata para Beaune/Lyon/Suíça;
Karlsruhe oferece conectividade alemã e passe regional,
mas há diferenças de operação e custo total ferroviário. Comparação
só terá resultado após mesmo conjunto de passeios e hospedagem
privativa cotada. **Sem vencedor.**

## 6. Mobilidade, imóveis e legislação

- A regra francesa `bail mobilité` não é simplesmente "aluguel por
  dois meses para qualquer turista". [Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F34759)
  exige situação específica, como missão profissional temporária,
  estudos ou formação, com documentação.
- Muitos anúncios nas plataformas pedem fiador, contrato profissional
  ou mínimo de três meses, incompatíveis com 56–60 noites.
- [Your Europe, familiares não UE](https://europa.eu/youreurope/citizens/travel/entry-exit/non-eu-family/index_en.htm)
  indica regras próprias para familiares de cidadãos europeus.
  Verificar documentos/estado civil concreto do casal após 04/09/2027;
  turismo e livre circulação não resolvem automaticamente autorização
  de trabalho remoto pelo empregador, tributação, seguro ou previdência.
- Segurança, internet dedicada, ergonomia, barulho, lavanderia, estação
  acessível e custo de mercado **ainda são critérios de pesquisa**, e
  não notas atribuídas sem evidência.

## 7. O que falta para concluir o pedido integral

1. Fixar noites exatas **até 60** e endereço aproximado preferido.
2. Validar **pelo menos 3 apartamentos privados para 2 adultos em cada
   uma das 12 finalistas**, nas MESMAS datas de 2027, incluindo
   cozinha, internet, trabalho, lavanderia, taxas e política do imóvel.
3. Verificar tamanho/ocupação e duração mínima: anúncios de 2026 não
   comprovam elegibilidade em 2027.
4. Para cada finalista, estudar **>=15 destinos potenciais**, validar
   ida e volta em fim de semana de 2027, custo regular de trem
   para dois, acesso até atração e horários de retorno. Contar
   cidades uma vez e separar atrações dentro delas.
5. Calcular consumo médio de supermercado/transportes urbanos e
   refeições em base homogênea.
6. Produzir três projeções de 60 noites (econômico/equilibrado/explorador)
   por base, reconciliadas sem duplicar as verbas do orçamento oficial.
7. Somente então publicar `score_0_100` geral, econômico, explorador
   com a qualidade da evidência; comparar cinco finalistas.
8. Se não aparecerem 3 ofertas elegíveis, marcar **inviável
   documentalmente** em vez de declarar melhor cidade.

## 8. Integração com o projeto

- Arquivos novos: `data/base_city_research_expanded_2026_11.json`,
  `data/base_city_rail_evidence_expanded_2026_11.json`,
  `base_research_expanded_model.py`, `base_research_expanded_ui.py`,
  `tests/test_expanded_base_research.py`.
- `base_explorer_ui.py` recebe o modo **Pesquisa ampliada**, usando
  a mesma aba **Roteiro → Explorar bases** já implantada.
- `TripPlan` e as quatro cidades-base oficiais permanecem iguais.
  Não entram novas tarifas/hospedagens no orçamento como se fossem
  contratos. Não sobrescrever dados, fontes, notas históricas ou
  modelo já existente.
