# Nossa Europa 2027 — Streamlit + Drive

App de lua de mel Itália → França, com mapa, orçamento, cronograma e pesquisas. Repositório de código: `clevertondecker/europe-trip`. Os arquivos oficiais da viagem continuam no **Google Drive**.

## O que sincroniza

| Tela | Fonte | Tipo |
|---|---|---|
| Decisões | 01_ESTADO_ATUAL (Google Doc) | Leitura Drive, até 5 min de cache |
| Pendências | 03_PENDENCIAS (Google Doc) | Leitura Drive, até 5 min de cache |
| Orçamento e cenários | 03 PREMISSAS do XLSM, validando 02 ORÇAMENTO | Recalcula a partir das premissas, até 5 min |
| Roteiro | 04 ROTEIRO E TRABALHO do XLSM | Leitura Drive, até 5 min |
| Mapa | Catálogo geográfico local; status da cidade-base D-004 do Doc | Híbrido; cidades não são reservas |

Em cada seção aparece a origem, data da fonte e/ou aviso de fallback. Simulações **não são cotações reais para 2027**. O fluxo é *somente leitura*, preservando os documentos originais.

## Ativar no Streamlit Community Cloud (uma vez)

1. Acesse seu app no [Streamlit Cloud](https://share.streamlit.io/), abra **Settings → Secrets** (ou **App settings → Secrets**).
2. Crie uma conta de serviço em [Google Cloud Console](https://console.cloud.google.com/), ative a **Google Drive API** no projeto e crie uma chave JSON dessa conta de serviço, se esse for o método de credenciais que você escolher. Proteja essa chave e **não a envie ao chat nem ao GitHub**.
3. No Drive, compartilhe como **Leitor** com o e-mail `client_email` da conta de serviço **somente** estes arquivos:
   - [Estado atual](https://docs.google.com/document/d/12O55HyOZsyv68qntsZbbVAeiw4tQnKrpG61i2_kZJBo/edit)
   - [Pendências](https://docs.google.com/document/d/1kFvDkGO8tGXoVGcBMisntyoVGZNTDHwUT7Me7vVH1pY/edit)
   - [Modelo financeiro XLSM](https://drive.google.com/file/d/1LeTrUWLLzIe_mZS26gMt_KMnnX4jelZ4/view)
4. No painel de Secrets do Streamlit, crie a seção TOML `[gcp_service_account]` com os campos do JSON (`type`, `project_id`, `private_key_id`, `private_key`, `client_email`, `client_id`, `auth_uri`, `token_uri`, etc.). O campo `private_key` deve preservar os caracteres de quebra de linha `\n` conforme TOML. **Nunca cole Secrets em arquivos versionados.**
5. Salve, reinicie/reimplante o app, abra **Nossa Europa 2027** e use **Atualizar dados do Drive**. Confira os indicadores de origem (Drive versus snapshot) na barra lateral.

Para revogar acesso, remova a permissão da conta de serviço nos três arquivos e revogue a chave no Google Cloud. Configurar a integração da conta do Google com ChatGPT **não** dá automaticamente acesso à aplicação Streamlit.

## Falhas seguras

- Se não houver credenciais, exibe snapshot de 14/11/2026.
- Se uma fonte falhar, preserva somente aquela parte no snapshot e exibe aviso específico.
- Se o cache do Excel divergir do cálculo reproduzido a partir das premissas, exibe alerta de divergência; não usa a cópia antiga como verdade.
- Se mudar a estrutura da planilha ou as datas fixas, bloqueia a atualização financeira até revisão.
- Alterações em layout e código ainda exigem commit no GitHub; mudanças nos documentos oficiais refletirão automaticamente após o cache de leitura.

**Segurança:** verifique tanto a visibilidade do repositório GitHub quanto a do app Streamlit; mesmo em repositórios privados, apps podem ser compartilhados separadamente.

## Testar

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py data_model.py drive_sync.py
streamlit run app.py
```

O script usa apenas Python padrão para inspecionar o ZIP/OOXML do XLSM e o Google Drive API para buscar os arquivos. Ele nunca grava no XLSM.

## Evolução 1 — Comparador de cidades francesas

Nova página **Comparar cidades**: Mulhouse, Strasbourg, Metz e Nancy com notas históricas 0–5 (arquivo `data/cities_france_2026.json`), calculadora de ranking com pesos ajustáveis e três perfis originais do modelo financeiro. Exibe comparação lado a lado, envelopes históricos de aluguel e links de pesquisas de 2026.

**Fontes e governança:** abas 11, 12, 13 e 15 de `Europa_2027_COMPLETO_ORGANIZADO.xlsm`, com cópia editorial de referência versionada no GitHub. Essas abas históricas NÃO fazem parte da sincronização automática atualmente estabelecida (que lê decisões, pendências e as abas operacionais 02–04 do Excel). Para atualizar as notas editoriais ou anúncios históricos, é necessário revisar a fonte e este arquivo JSON no repositório. Se D-004 do documento de decisões continuar "Não decidida", a página jamais deve declarar uma vencedora oficial.

O ranking não prevê disponibilidade, aluguel por 55–65 dias, internet, elegibilidade para contratos ou preços finais para 2027. Alterar sliders não edita o Drive e não muda o orçamento oficial.

Para validar: `python -m unittest discover -s tests -v`; a rotina GitHub Actions executa os testes e a compilação.


## Auditoria da confiabilidade das cidades (14/11/2026)
As notas de Mulhouse, Strasbourg, Metz e Nancy são *históricas/editoriais*, não medições objetivas. Os valores de aluguel não são cotações para 55–65 noites após o casamento. Em 14/11/2026 nenhuma cidade possui 3 ofertas confirmadas para a janela 2027; o aplicativo exibe essa limitação separada do ranking de preferências.
- [Prompt mestre de auditoria](PROMPT_AUDITORIA_CIDADES.md)
- [Relatório detalhado e divergências da planilha](RELATORIO_AUDITORIA_CIDADES.md)
- [Modelo obrigatório para nova cidade](TEMPLATE_NOVA_CIDADE.md)
- [Critérios de auditoria e dados estruturados](data/city_research_audit_2026.json)
- [Validação automática](city_research.py) e [testes](tests/test_city_research.py)

A matriz histórica continua versionada e separada do Drive live; revisar manualmente quando novas fontes estiverem verificadas. O arquivo `city_research_audit_2026.json` não significa sincronização de anúncios em tempo real. Nunca transformar status de pesquisa em decisão oficial sem registrar aprovação no documento de decisões.

## Primeira comparação factual de mercado — novembro de 2026

A página **Comparar cidades** apresenta, além do ranking editorial, uma amostra padronizada de três anúncios por cidade no mesmo catálogo, passes urbanos nominais e exemplos de trens TER com tarifa Carte Fluo. Os números **não são preços integrais de 55–65 noites**, não garantem imóvel para dois adultos nem inclusão de contas, internet e contrato. A cesta de €137,06/semana é hipótese compartilhada do Drive, não pesquisa local. A separação é intencional para evitar falsa precisão.

- [Prompt executado](PROMPT_PRIMEIRA_COMPARACAO_REAL.md)
- [Pesquisa com URLs, datas e ressalvas](RELATORIO_PRIMEIRA_COMPARACAO_REAL.md)
- [Dados estruturados](data/city_market_observations_2026.json)
- [Validador](city_market.py) e [testes](tests/test_city_market.py)

A inclusão futura de uma cidade deve seguir o template de auditoria e coletar o mesmo tipo de evidência. Nenhuma observação desta pesquisa altera a planilha oficial ou a decisão D-004 no Drive.


## Evolução integral — consolidação das cinco fases

**Implementação:** 14/11/2026 · Prompt mestre: [PROMPT_MESTRE_EVOLUCAO_INTEGRAL_2027.md](PROMPT_MESTRE_EVOLUCAO_INTEGRAL_2027.md).

### Fase 1 · Integridade
- `catalog.py` combina as referências de destino do snapshot com os pontos detalhados de `data/itinerary_options_2027.json` usando IDs canônicos (Roma/rome, Nápoles/naples, Luxemburgo/luxembourg). Mantém as notas da fonte oficial quando disponíveis e não inventa preços.
- O filtro do mapa agora considera a seleção vazia como **zero resultados**, e não como "mostrar todos".
- `unified_budget.py` obtém as cinco subverbas francesas do cenário **atualmente sincronizado** quando os dados do Drive estão live; em snapshot usa os valores históricos explicitamente sinalizados. Fonte Drive continua somente leitura.
- O CSS passou para `assets/styles.css`, facilitando consistência visual e manutenção.

### Fase 2 · Orçamento unificado
- Página **Orçamento** substitui simuladores desconectados por uma única projeção: teto do casal, duração na França, frequência e preço de saídas, cidade-base opcional, aluguel hipotético, câmbio e deltas de voos, passeios, transporte e taxas de moradia.
- Aluguel indicado **substitui**, e não adiciona, a verba original de aluguel. O mesmo vale para saídas/restaurantes. Variações adicionais só entram uma vez.
- Reserva de emergência já está dentro do total da planilha, nunca reaproveitada como verba de consumo.
- Três perfis de comportamento são **hipóteses ilustrativas**, não preços reais: Econômico, Equilibrado, Mais ativo.
- Custos de mercado de 2026 **não** significam disponibilidade ou taxa contratada para 2027.
- Atenção: ajustar duração escala linearmente compras/transporte/passeios e aluguel como hipótese. Isso não é necessariamente o preço praticado para contratos de locação, feriados, descontos ou pernoites.

### Fase 3 · Roteiro e mapas
- Página **Roteiro → Calendário** calcula a distribuição ilustrativa dos dias a partir de partida posterior ao casamento: Itália, instalação francesa, férias/escapadas, dias úteis de trabalho remoto e fins de semana.
- Permite mudar a data candidata, duração, férias, dias italianos e instalação, sem gravar no Drive.
- **Transportes e custos** pode exibir dois pinos de origem/destino quando o arquivo de pesquisa contém ambas as coordenadas. **Não** gera trajeto geográfico real nem tempo porta a porta; usa apenas tempo ferroviário/marítimo publicado e referências de preço catalogadas.
- EUR e CHF continuam separados; descontos Carte Fluo são condicionais; valores "a cotar" continuam desconhecidos. Passeios não são somados novamente à verba já reservada no orçamento.

### Fase 4 · Comparação de cidade-base
- Página **Comparar cidades → Visão rápida** apresenta simulações financeiras equivalentes para as quatro cidades, usando o mesmo padrão de consumo e alugueis **editoriais de 2026**, apenas para sensibilidade do teto de R$70 mil.
- Em **Comparar e ajustar**, "Simular ... no orçamento" carrega a cidade selecionada para o simulador unificado. Não altera a decisão D-004 sobre a cidade-base.
- Auditoria dos oito gates e ausências de cotação ainda bloqueia status "pronto para reserva". O aluguel exibido nunca é convertido silenciosamente em oferta de 2027.

### Fase 5 · Acompanhamento e UX
- **Visão geral** agora indica número de pesquisas concluídas, decisões abertas, fontes Drive sincronizadas e ausência de reservas confirmadas, com atalhos para o orçamento e prioridades.
- **Pesquisas & decisões** passou a ter visão por prioridade P0–P3, decisões oficiais e documentos/fontes. A origem registra somente "pendente/concluído"; status intermediário **não é inventado**.
- Fontes Drive (decisões, pendências, orçamento/cronograma) sincronizam com cache; pesquisas de mercado e preços de passeios são arquivos versionados do GitHub, que **não são atualizados automaticamente** pelo Drive.

### Validação e limitações
- `tests/test_catalog.py`, `tests/test_unified_budget.py`, `tests/test_calendar_model.py`, `tests/test_route_preview.py` protegem os contratos novos.
- `tests/test_app_smoke.py` usa Streamlit AppTest para executar as seis páginas sem Secrets reais. Essa prova não é um teste visual de navegador.
- O CI compila todos os módulos e roda os testes, incluindo o legado.
- **Não resolvido por código**: três ofertas imobiliárias elegíveis para 55–65 noites nas datas reais por cidade; transporte público porta a porta e últimos trens de fim de semana; tarifas de 2027; autorização de trabalho remoto e contratos; passagens multidestino para duas pessoas. Esses itens precisam de pesquisa/contato real antes de qualquer reserva.
- **Segurança**: uma chave de conta de serviço do Google Cloud já foi inserida em conversa anterior. Recomenda-se **revogar/rotacionar** essa chave no GCP e atualizar os Streamlit Secrets. Nenhuma chave foi publicada nestes arquivos.

### Workflow operacional
1. Editar decisões, pendências e premissas financeiras no Drive; depois clicar **Atualizar dados do Drive** no aplicativo.
2. Registrar novas pesquisas verificadas com fonte, URL, validade, moeda e distinção entre preço observado/cotação em arquivos versionados no GitHub.
3. Explorar cenários no Streamlit sem aprovar reservas automaticamente; quando tiver orçamento comparável e cotação real, registrar a decisão oficial D-004 no documento do Drive.


## Roteiro → Explorar atrações (implementação 14/11/2026)

A nova experiência de turismo usa a cidade-base francesa hipotética para **recalcular tarifas e tempos ferroviários publicados** dos destinos em estudo e permitir a escolha de atrações. O usuário não altera a decisão D-004 nem compra bilhetes pelo painel.

- [Prompt de especificação](PROMPT_CATALOGO_ATRACOES_ROTEIRO_ADAPTATIVO_2027.md) e [relatório de implementação e fontes](RELATORIO_IMPLEMENTACAO_ATRACOES_2027.md).
- [50 atrações catalogadas em 11 destinos](data/attractions_2027.json), agrupadas em países, com fontes oficiais, fotos licenciadas de vários destinos e ingressos apenas quando documentados.
- [44 combinações de rotas base × destino](data/base_destination_routes_2027.json), incluindo tempos e tarifas históricas com desconto quando comprovados, e valores ausentes como `null`.
- [Validação, cálculo e calendário](attractions_model.py), [UI separada](attractions_ui.py), [testes de domínio](tests/test_attractions_model.py) e [testes interativos](tests/test_attractions_ui_smoke.py).
- **Roteiro → Explorar atrações:** filtros por base, país, categoria, tipo de preço, preferência pessoal e tipo de acesso; cards, mapas de destinos, detalhes, interesse, pacotes de até cinco atrações, custo parcial por casal, calendário provisório e exportação JSON.
- **Mapa & destinos:** destinos do catálogo partilhado e atalho para Explorar atrações.
- **Roteiro → Calendário:** mostra escolhas provisórias da sessão, sem bloqueio real de agenda/reservas.
- **Orçamento:** o subconjunto de valores conhecidos só acrescenta o excedente **sobre** a verba de excursões prevista, evitando dupla contagem ou economias fictícias.
- **Ressalvas:** distâncias exibidas são geodésicas em linha reta, não quilômetros de trem. Os tempos oficiais são de estação a estação, não porta a porta. Carte Fluo requer regras de elegibilidade e eventual custo do cartão. Mapas não traçam trilhos verdadeiros; passeios alpinos podem exigir pernoite. Fotografias individuais das 50 atrações, tarifas normais e rotas específicas de 2027 continuam em pesquisa.

A lista pessoal permanece em `st.session_state`; exporte-a antes de fechar a sessão. Nenhuma pesquisa de atrações sincroniza automaticamente do Drive.


## Consultor inteligente determinístico (15/11/2026)

**Onde:** Roteiro → Consultor inteligente.

A partir do catálogo de 50 atrações e da matriz de 44 rotas pesquisadas, o consultor identifica lacunas de preço e retorno, tempo de viagem longo, tarifas Fluo condicionais e pernoites possíveis. Em Python, sem LLM, propõe até três redistribuições conservadoras de passeios nos fins de semana e dias livres. O ranking é relativo aos candidatos e **não** é uma previsão de custo, horários ou trajetos porta a porta.

A interface contém perfis Econômico, Equilibrado (padrão) e Aproveitar ao máximo, alertas rastreáveis, custo conhecido para duas pessoas, comparação de alternativas, botão de aprovação/rejeição, exportação e importação JSON. Nenhum plano proposto muda calendário sem aprovação explícita. A escrita versionada no GitHub é desabilitada por padrão; pode ser configurada pelo proprietário nos Streamlit Secrets, com token e autenticação separados. É necessário evitar armazenamento de roteiros pessoais em repositórios públicos.

**Arquivos:** `trip_plan_model.py`, `trip_plan_repository.py`, `travel_advisor.py`, `travel_optimizer.py`, `travel_advisor_ui.py`, `tests/test_travel_advisor.py`, `tests/test_travel_advisor_ui_smoke.py`, `tests/test_travel_advisor_approval_smoke.py`.

**Documentação completa, limitações e configuração segura:** [RELATORIO_CONSULTOR_DETERMINISTICO_2027.md](RELATORIO_CONSULTOR_DETERMINISTICO_2027.md).

**Segurança da gravação (atualizado):** o fluxo utiliza login Google OIDC, verifica o e-mail do proprietário e sessão válida, e só grava com token restrito guardado nos Streamlit Secrets. O hash de senha usado anteriormente não é mais aceito. Consulte o [guia de ativação segura](GUIA_ATIVAR_SALVAMENTO_GITHUB_SEGURO.md).

O repositório foi confirmado **público** em 15/11/2026; roteiros gravados em JSON ficarão públicos. As credenciais ainda **não foram configuradas**; até que o proprietário complete o setup Google Cloud/GitHub/Streamlit, a exportação e importação JSON continuam disponíveis. O Drive e a decisão D-004 permanecem somente leitura.


### Recuperação após atualizar a página (corrigido em 15/11/2026)

Quando o proprietário autenticado abre **Roteiro → Consultor inteligente** numa sessão nova, o aplicativo procura os planos já gravados em `data/user_plans/` e carrega o mais recentemente salvo. O comportamento antigo criava um ID aleatório a cada atualização e fazia o botão **Carregar** tentar abrir um arquivo inexistente.

A seção **Outros planos e histórico de revisões** agora permite selecionar outros roteiros versionados, ordenados pela última gravação registrada no GitHub. Carregar um plano restaura também a seleção de atrações e o calendário na sessão. Alterações que ainda não foram salvas não são sobrescritas automaticamente.

Os arquivos existentes não são modificados pela recuperação; a escrita continua exigindo aprovação explícita e autenticação Google.


## Nossa Europa UX 2.0 — Planejamento simples e consultor integrado

A nova página **Minha viagem** mostra o status de salvamento, quantas atrações foram selecionadas e quantos dias do roteiro estão organizados. Use as ações **Escolher atrações**, **Melhorar meu roteiro** e **Ver orçamento** para continuar.

**O plano é único:** `advisor_plan` é a fonte de verdade versionada; as páginas de atrações, calendário, consultor e orçamento lêem o mesmo conjunto de escolhas. O antigo processo de importar manualmente atrações no consultor foi eliminado. O orçamento usa bilhetes conhecidos como custos **parciais**, com proteção contra dupla contagem da rubrica de excursões.

**Consultor:** apresenta recomendações prioritárias em cards, explica sua origem e compara as mudanças de data antes de permitir a aprovação. As alternativas são heurísticas Python, sem LLM e sem horários de transporte em tempo real.

**Salvamento:** o botão **Salvar planejamento** usa a conta Google autorizada e a API GitHub server-side. Exportação/importação JSON e histórico ficam em opções avançadas. O plano não é alterado por simplesmente navegar ou visualizar recomendações. Salvamento automático é opcional, desativado por padrão e exige reconhecimento explícito da publicidade do repositório; recomenda-se não incluir dados pessoais no GitHub público.

**Migração:** planos JSON antigos seguem válidos; seleção de atrações, datas e preferências são preservadas. O Drive continua fonte documental somente leitura.

Documentação de arquitetura e UX: [UX_REDESIGN_2027.md](UX_REDESIGN_2027.md) · [Relatório completo dos 11 steps](RELATORIO_UX_NOSSA_EUROPA_2_0.md).
