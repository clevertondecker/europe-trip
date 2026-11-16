# Data Quality 2.1 B — rotina real e horário de trabalho

A pesquisa atual mantém os seis critérios da DQ 2.0; nenhuma nota 0–100. Novo `dq21_living_model.py` não reescreve `city_research_packs_2026_11.json`.

## Freiburg: dado meteorológico preliminar
Estação Freiburg **DWD 01443**, normais 1991–2020 republicadas em https://wetteratlas.de/stationen/freiburg : temperatura média setembro **15,9°C**, outubro **11,4°C**, novembro **6,6°C**. Um segundo site DWD-rótulo mostra 15,4/10,9/6,1°C e 77,4/78,5/66,2 mm: https://freiburgtravelguide.com/ . Há divergência de ~0,5°C. **Não misturar séries nem declarar precipitação comparável sem extrair a fonte DWD primária**, indexada em https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/multi_annual/mean_91-20/ . Preserva `null` para precipitação até reconciliar.

## Horário brasileiro corretamente localizado
`brazil_to_europe_hours("2027-10-30", start_hour=9,end_hour=18)` converte 09h–18h São Paulo para **14h–23h** na Alemanha/França; em **31/10/2027** (fim do horário de verão europeu) passa a **13h–22h**. O modelo usa `zoneinfo`, não soma manual de horas. Referência mudança DST: https://time.is/DST_2027 e https://savvytime.com/converter/cet-to-cest-brazil-sao-paulo . É cenário opcional; não fixa rotina no TripPlan.

## Dados urbanos e limitações
Redes públicas Soléa/CTS/VAG já pesquisadas no DQ 2.0 permanecem fonte primária das políticas de serviço noturno. Sem endereço do apartamento, é impossível comprovar acesso no fim do expediente, farmácia/mercado/academia em caminhada, velocidade da conexão interna e segurança por rua. Dados oficiais criminais de fronteiras administrativas diferentes não foram tornados comparáveis artificialmente.

## Contratos / testes
`compare_living_depth(study_dates=("2027-09-15","2027-11-15"), brazil_hours=(9,18))` retorna dados das 3 cidades; fora desse cenário não há horário definido. Testes verificam mudança do DST, internet desconhecida e divergência climática.

**Sem publicação/merge automático.**
