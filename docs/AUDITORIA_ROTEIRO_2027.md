# Auditoria do roteiro e viabilidade — Europa 2027
Referência: 15/11/2026 · Casamento 04/09/2027 · viagem só depois.

## Escopo e critérios
A viagem é proposta, não uma reserva. A etapa inicial Itália é
modelada como aproximadamente dez dias, seguida de uma base francesa
para trabalho remoto e passeios (cerca de 60 dias no cenário de 70).
As datas exatas de 2027 não foram precificadas.

Viabilidade classificada como:
- **Viável**: logística e calendário confirmados para as datas;
- **Viável com ressalvas**: conexão conhecida, mas faltam preços/
  horários do dia/condições;
- **Não recomendado**: incompatível com duração/rotina;
- **Sem dados suficientes**: impossível verificar retorno, pernoite
  ou rota essencial. Não pressupor custo zero.

## Itália: Roma → Costa Amalfitana → França

**Salerno** é um ponto ferroviário e intermodal mais simples para
chegar de Roma e sair em direção ao norte/França: existe acesso
ferroviário principal à cidade, além de ônibus e ferries para o litoral.
**Maiori** fica mais próximo das praias e vilas da costa, mas exige
transferência adicional até/de estação ou aeroporto, inclusive levando
bagagens. Não há evidência de que a hospedagem em Maiori compense
economicamente sem cotar hotéis reais para as mesmas datas.

O ônibus SITA Sud **linha 5120** conecta Salerno, Vietri, Cetara,
Maiori, Minori, Atrani e Amalfi. A empresa publicou alteração de
horários para **14/09/2026** e outra com vigência em **02/11/2026**,
o que comprova que os horários variam por estação e não se deve
carregar para novembro de 2027 um trajeto de verão.

Fontes oficiais:
- [SITA Sud: horários linha 5120](https://sitasudtrasporti.it/campania/orari/5120-amalfi-maiori-salerno/)
- [SITA: ajuste de setembro 2026](https://sitasudtrasporti.it/campania/avvisi/orario-costiera-sita/)
- [SITA: ajuste de novembro 2026](https://sitasudtrasporti.it/campania/avvisi/orari-costiera-sita-dal-02-11-2026/)

Ferries da Travelmar são sujeitos a temporada, condições marítimas e
alterações de horários. **Não** tratar uma viagem curta de barco
Salerno–Maiori como deslocamento garantido no dia da transferência,
especialmente em fim de temporada.

### Verificação a fazer antes de escolher Salerno ou Maiori
1. Hospedagem com café/ar-condicionado e taxas para período exato.
2. Chegada Roma → Salerno com bagagem e deslocamento ao hotel.
3. Hora de chegada e alternativa de ônibus se ferry for cancelado.
4. Locomoção para Amalfi/Positano/Ravello e último transporte da volta.
5. Saída para a França: aeroporto/estação de saída, conexão e tempo
   porta-a-porta. Sem cotações, não há 'vencedora' financeira.

**Conclusão provisória**: Salerno tende a facilitar a logística
interurbana; Maiori tende a favorecer experiência de praia; custo total
e conforto não verificados para 2027. **Viável com ressalvas** ambas,
não é possível afirmar qual é mais barata.

## França: cidades-base atualmente cadastradas

| Base | Potencial comprovado | Riscos e lacunas | Status |
|---|---|---|---|
| Mulhouse | Colmar ~18 min, Basel ~22 min por trecho ferroviário histórico | Tarifa Fluo condicionada, horários de retorno e aluguel mobiliado desconhecidos | Viável com ressalvas |
| Strasbourg | Colmar ~32 min, Alemanha e Baden-Württemberg relativamente próximos | Conexões transfronteiriças, aluguel e passagens finais não cotados | Viável com ressalvas |
| Metz | Luxemburgo ~42 min publicados; acesso a Nancy | Rotas rumo a Colmar/Alpes incompletas | Viável com ressalvas para Luxemburgo; demais destinos sem dados |
| Nancy | Proximidade regional de Metz; opção urbana a estudar | Muitas combinações ferroviárias base×destino sem tarifa/tempo verificados | Sem dados suficientes para comparativo geral |

Fontes originais preservadas na matriz
`data/base_destination_routes_2027.json` e em
`PESQUISA_BASES_E_DESTINOS_ALTERNATIVOS_2027.md`.

**Nenhuma cidade-base deve ser declarada vencedora** com aluguel mensal
de mercado geral: contratos de 2 meses mobiliados podem exigir outros
depósitos, limpeza, contas, internet adequada ao trabalho e taxas.
A comparação precisa de cotações homogêneas de imóvel **para 2027**.

## França: novas bases exploratórias — não aprovadas
- Lille: corredor Bélgica/Holanda (Amsterdam ~2h49 no mais rápido),
  possível Colônia; melhor para fim de semana a noroeste.
- Arras: cidade menor com conexão ferroviária a Lille, mas depende
  de passagem adicional e possível espera.
- Dijon: Borgonha, Beaune, Lyon e Suíça (Lausanne);
  opções de França central e alpes ocidentais.
- Reims: Champagne e Paris; Amsterdam via Paris pode ser longo.
- Duas bases Lille + Strasbourg/Mulhouse: amplia destinos, mas acrescenta
  mudança e potencial duplicidade de custos de aluguel/caução.

**Status: sem dados suficientes para ranking financeiro.** Mais tempos,
fontes e ressalvas no Markdown de pesquisa exploratória existente.
Ainda não integram `TripPlan.BASES`, para não modificar decisões
ou quebrar backups existentes.

## Passeios e calendário
A versão anterior de `planning_store.add_assignment` permitia
qualquer ISO-date e destino escolhido, inclusive trabalho remoto,
instalação, Itália e após o fim da viagem. Corrigido nas novas
mutações pela validação do calendário. Visitas previamente confirmadas
não são alteradas automaticamente.

Para todos os passeios:
- Tempo publicado de trem é **estação a estação**, não porta-a-porta.
- Tarifas Carte Fluo exigem cartão e elegibilidade do acompanhante.
- Comida e supermercado observados em 2026 são **pequenas amostras**,
  não preços completos 2027.
- Passeios alpinos exigem teleféricos/ônibus, condições climáticas,
  abertura sazonal, alternativas e possivelmente pernoites;
  sem dados completos, manter status **Sem dados suficientes**.
- Cidades a mais de 4–5 horas de deslocamento só ida geralmente exigem
  fim de semana/noites. Não enquadrar como bate-volta realista.

## Entrada, residência e trabalho remoto: checagem necessária
As regras variam com **cada documento e vínculo de trabalho**.

- A UE publica que cidadãos europeus têm liberdade de circulação e
  direitos de trabalho noutros países da UE:
  https://europa.eu/youreurope/citizens/work/work-abroad/index_en.htm
- Para viajantes **não UE**, a regra geral Schengen é **90 dias em
  180** para viagens de curta duração, sujeita a condições específicas:
  https://home-affairs.ec.europa.eu/policies/schengen/visa-policy_en
- ETIAS ainda **não estava operacional em 15/11/2026**. Não presumir
  implementação ou exigência em setembro de 2027 sem rever:
  https://travel-europe.europa.eu/etias/faq
- Documentos de familiares não UE de cidadãos UE podem seguir
  regras especiais; verificar status matrimonial, nacionalidade,
  documentação e os países concretos:
  https://europa.eu/youreurope/citizens/travel/entry-exit/non-eu-family/
- Trabalho remoto para empresa empregadora fora da UE pode envolver
  autorização do empregador, segurança da informação, legislação do
  trabalho, tributação e previdência. A regra de turismo ou livre
  circulação **não substitui** essa análise; não afirmar que
  trabalhar remotamente a partir da França é automaticamente permitido
  para qualquer vínculo.
- Confirmar seguro, condições de cobertura profissional e saúde no
  exterior e requisitos de estadia para ambos, antes de reservas.

**Decisão sugerida, não aprovada:** comparar um roteiro núcleo de
6–8 passeios em Lille, Strasbourg e uma combinação de bases, com
cotações mobiliadas reais, transporte regular do casal, tempo,
segurança do retorno e datas compatíveis com trabalho.

## Pendências maiores
Consultar `docs/PENDENCIAS_DADOS_2027.md`; nenhuma despesa
desconhecida foi transformada em zero ou diária inventada.
