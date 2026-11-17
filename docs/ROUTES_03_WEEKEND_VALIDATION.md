# ROUTES 3 — ida/volta documentada não é passeio viável

Implementação do pacote descrito em #112. `weekend_return_validation_model.py` examina **direção, estações, datas de serviço, horários locais com fuso, transferências documentadas, última milha e janelas de abertura**.

O conjunto de dados existente contém amostras e horários históricos de 2026; este PR **não cria** um retorno 2027 nem preenche lacunas com zero. Um caso com duas viagens documentadas e acesso compatível recebe no máximo `historical_schedule_coherent_only`, nunca `outing_feasible=true`. A validação estrutural também não garante a autenticidade de um horário fornecido; fontes e amostras continuam exigindo pesquisa e verificação independentes.

**P1:** serviço de dia útil usado como fim de semana, direções ou estações incompatíveis, visita fechada ou retorno antes da visita. Contrato: a lista `calendar_dates_verified` deve conter a data concreta do trecho; horários são ISO com fuso e transferências têm ordem temporal. **P2:** incompatibilidade de última milha e tarifa/serviço sem garantia futura. Contrato de acesso exige mesma estação e tempos positivos com fontes.

Reutiliza `canonical_place()` e mantém o adaptador ferroviário legível e inalterado. Não modifica `TripPlan`, dados históricos, preferências ou interface.

**Aceite:** testes de calendário, ordem, transferência, falta de acesso, horário de atração, identidade e recusa expressa de viabilidade automática.
