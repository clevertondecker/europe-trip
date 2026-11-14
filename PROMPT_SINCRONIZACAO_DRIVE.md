# Prompt executado — Sincronização Drive → Nossa Europa 2027

**Projeto:** `clevertondecker/europe-trip` · Streamlit Community Cloud.

## Objetivo

Evoluir o painel de viagem somente leitura, sem descaracterizar o visual existente, para atualizar automaticamente a partir da pasta oficial Europa 2027 no Google Drive, sem download, Git local ou edição manual do `trip.json`.

## Fonte de verdade e prioridades

1. Decisões aprovadas: Google Doc `01_ESTADO_ATUAL` (`12O55HyOZsyv68qntsZbbVAeiw4tQnKrpG61i2_kZJBo`).
2. Pendências: Google Doc `03_PENDENCIAS` (`1kFvDkGO8tGXoVGcBMisntyoVGZNTDHwUT7Me7vVH1pY`).
3. Orçamento, premissas e cronograma: arquivo XLSM `Europa_2027_COMPLETO_ORGANIZADO.xlsm` (`1LeTrUWLLzIe_mZS26gMt_KMnnX4jelZ4`), abas `02 ORÇAMENTO`, `03 PREMISSAS` e `04 ROTEIRO E TRABALHO`.
4. O `data/trip.json` é somente fallback histórico, nunca substituir uma decisão vigente válida por ele.
5. Catálogo geográfico de cidades pode continuar como referência estática; não confundi-lo com reservas ou roteamento calculado.

## Regras obrigatórias

- Autenticação pelo Google Drive API em **modo somente leitura** usando credenciais de conta de serviço guardadas exclusivamente nos Secrets do Streamlit.
- Compartilhar com a conta de serviço somente os dois Docs e a planilha XLSM, como leitor.
- Exibir data de atualização e proveniência por seção, com cache máximo de 5 minutos e botão para atualizar.
- Falhar de forma isolada por seção: preservar snapshot quando a fonte não puder ser validada, sinalizando visualmente, sem inventar nem apagar dados.
- Recalcular financeiramente a partir das premissas `03 PREMISSAS`, reproduzindo as fórmulas da aba `02 ORÇAMENTO`, sem aceitar silenciosamente caches desatualizados do Excel.
- Preservar escopo total para dois viajantes, ida/volta já incluídas, reserva já incluída e restrição de partida posterior a 04/09/2027.
- Sincronizar o roteiro planejado da aba `04 ROTEIRO E TRABALHO`, diferenciando hipóteses de reservas.
- Só destacar uma cidade-base como definida no mapa quando a decisão D-004 registrar explicitamente uma opção aprovada; nunca inferir uma escolha apenas por ranking histórico.
- Não alterar os arquivos oficiais do Drive pelo aplicativo, não publicar credenciais, não criar preços, reservas ou disponibilidade fictícios.
- Não fazer push local no Mac corporativo. Publicar usando a conexão autorizada do GitHub.

## Critérios de aceite

- [x] Ler e validar Docs de decisões e pendências.
- [x] Ler XLSM e sincronizar premissas, orçamento por categoria e cronograma.
- [x] Recalcular e comparar com os valores históricos de cache.
- [x] Indicar se cada origem é `Drive` ou `snapshot`.
- [x] Não escrever nem no Drive nem no Excel.
- [x] Passar testes unitários e validação sintática.
- [ ] Adicionar credenciais da conta de serviço no Streamlit (ação do proprietário).
- [ ] Confirmar teste fim a fim no aplicativo publicado (requer autenticação configurada).

> **Nota:** conclusão do código não equivale a autenticação ou sincronização ativa no serviço publicado. O aplicativo só fará leituras reais após os Secrets e as permissões serem configurados.