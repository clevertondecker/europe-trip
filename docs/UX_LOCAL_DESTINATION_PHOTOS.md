# Fotografias locais dos destinos — UX 5.0

## Problema comprovado
A página Explorar → Descobrir lugares continuava mostrando placeholders para Aachen, Baden-Baden, Colônia, Karlsruhe e Kehl, mesmo após o fallback de Wikimedia Commons. As consultas à Action API e os redirects Special:FilePath não asseguravam que o navegador recebesse a imagem.

## Entrega efetiva
As cinco imagens foram **baixadas e versionadas como arquivos binários WebP** no repositório, sob `assets/destinations/`. Cada arquivo tem 800×450 pixels, com corte 16:9, e é servido localmente pelo Streamlit via `st.image`. O aplicativo não faz requisição HTTP em runtime para esses cinco destinos. A busca dinâmica antiga continua apenas para outros destinos sem mídia local.

O arquivo `data/destination_photo_assets.json` identifica o destino, título de origem, caminho local, autoria, licença, link para a licença, descrição alternativa e página da imagem no Commons.

| Destino | Arquivo | Autor | Licença | Original |
| --- | --- | --- | --- | --- |
| Aachen | `aachen.webp` | Vitold Muratov | CC BY-SA 4.0 | [Cathedral in Aachen](https://commons.wikimedia.org/wiki/File:Cathedral_in_Aachen.jpg) |
| Baden-Baden | `baden_baden.webp` | Txllxt TxllxT | CC BY-SA 4.0 | [Lichtentaler Allee](https://commons.wikimedia.org/wiki/File:Baden_Baden_-_Lichtentaler_Allee_-_View_SE.jpg) |
| Colônia | `cologne.webp` | AtmikaPaul | CC BY-SA 4.0 | [Köln Cathedral](https://commons.wikimedia.org/wiki/File:K%C3%B6ln_Cathedral,_Germany.jpg) |
| Karlsruhe | `karlsruhe.webp` | Martin Kraft | CC BY-SA 3.0 | [Schloss Karlsruhe](https://commons.wikimedia.org/wiki/File:MKa_0553_Schloss_Karlsruhe.jpg) |
| Kehl | `kehl.webp` | H.Helmlechner | CC BY-SA 4.0 | [Passerelle des Deux Rives](https://commons.wikimedia.org/wiki/File:Passerelle_des_Deux_Rives_Kehl.jpg) |

As imagens foram reduzidas e recortadas; os cartões assinalam essa transformação e mantêm atribuição/links e licenças share-alike. A redistribuição dos arquivos modificados está sujeita às condições das respectivas licenças, independentes da licença do código.

## Arquitetura e ordem de preferência
1. Foto editorial catalogada existente, quando disponível.
2. WebP local versionado com autoria/licença.
3. Foto remota com evidência de licença, quando disponível.
4. Placeholder informativo.

`destination_photo_assets.local_destination_photo()` é uma projeção pura, sem rede e sem persistência. `ux501_destination_discovery_ui.py` elimina as cinco cidades do lote de consulta Wikimedia da página. A geração é reprodutível por `python scripts/curate_destination_photos.py` em um ambiente com internet e Pillow/requests. Uma workflow efêmera de preparação gerou/commitou os binários na branch do PR e foi removida ao final.

Nenhuma alteração de TripPlan, pesquisa, preferências, prioridades, agenda ou persistência.

## Verificação
- Testes verificam presença, tamanho, formato, dimensões, hashes distintos, créditos/licença e escolha de mídia.
- AppTest verifica ausência de consultas dinâmicas para as cinco cidades e preservação do plano ao abrir descoberta.
- A inspeção final em navegador desktop/mobile e a confirmação de publicação Streamlit Cloud permanecem independentes da validação automatizada.
