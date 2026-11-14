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
