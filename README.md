# Nossa Europa 2027 🌍

Painel Streamlit privado para lua de mel Itália → França (setembro–novembro de 2027).

## Publicação

1. Entre em https://share.streamlit.io/ e selecione **Create app** a partir do GitHub.
2. Repositório: `clevertondecker/europe-trip`; branch: `main`; arquivo principal: `app.py`.
3. Publique sem Secrets inicialmente. O app exibirá o snapshot local de novembro/2026.
4. Para sincronizar **decisões e pendências**, configure uma conta de serviço no Google Cloud com API Google Drive habilitada; conceda acesso **Leitor** somente aos Docs [Estado atual](https://docs.google.com/document/d/12O55HyOZsyv68qntsZbbVAeiw4tQnKrpG61i2_kZJBo/edit) e [Pendências](https://docs.google.com/document/d/1kFvDkGO8tGXoVGcBMisntyoVGZNTDHwUT7Me7vVH1pY/edit).
5. Armazene a chave da conta **apenas** no painel **App secrets** do Streamlit, usando o grupo TOML `[gcp_service_account]`. Nunca publique a chave no GitHub.

**Escopo:** decisões e pendências são consultadas via Drive somente leitura (cache de 5 minutos). Mapa, roteiro e orçamento permanecem como dados históricos de snapshot. Os totais R$ 59.975 e R$ 69.683 são estimativas, não preços confirmados para 2027.

Para testar em ambiente autorizado: `pip install -r requirements.txt`, `python -m unittest discover -s tests -v`, `streamlit run app.py`.

Fonte de referência: https://drive.google.com/drive/folders/1FCQAHuU1W3wnxDFeXbxsywZC96W5ta1r
