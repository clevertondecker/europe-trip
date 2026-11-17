# Prompt executado — Fotografias locais para todos os destinos restantes

## Papel e objetivo

Atue como Senior Python/Streamlit Engineer, UX Designer e Curador de Imagens com conhecimento de licenças Creative Commons. Corrigir a falta de fotos reais nos destinos do **Nossa Europa 2027**: todos os destinos de `build_destination_discovery()` devem ter imagens locais licenciadas ou imagens editoriais já existentes.

A experiência de descoberta precisa funcionar mesmo quando Wikipédia, Commons e redes externas estão indisponíveis no **runtime** do Streamlit.

## Auditoria obrigatória

1. Ler `AGENTS_COORDINATION.md` e os contratos da UX 5.0.
2. Gerar a lista canônica de IDs e nomes via `ux501_destination_discovery_model.build_destination_discovery()`.
3. Distinguir `photo` editorial, imagem local em `data/destination_photo_assets.json`, e realmente ausentes.
4. Nunca inferir destino por proximidade geográfica ou pelo nome aproximado de uma imagem.
5. Não alterar `TripPlan`, interesse, prioridade, orçamento, navegação, catálogo de atrações ou persistência.

## Curadoria

- Usar o artigo enciclopédico inequivocamente correspondente ao destino para localizar candidatos, **somente durante a preparação do PR**, não na aplicação publicada.
- Resolver cada candidato ao arquivo original do Wikimedia Commons e obter URL de fonte, autor, licença, e, se disponível, o link do texto da licença.
- Aceitar somente fotos reais de destino, não mapas, brasões, diagrams, ilustrações ou fotos de outra cidade. Evitar imagens com resoluções insuficientes.
- Permitir somente licenças verificáveis que autorizem redistribuição e edição (CC BY, CC BY-SA, CC0, domínio público), com atribuição e indicação de recorte. Preservar os requisitos de compartilhamento pela mesma licença quando aplicável.
- Criar arquivos binários WebP reais em `assets/destinations/<id>.webp`, dimensão 800×450, idealmente 5–250 KB, com bytes válidos.
- Adicionar as fontes e o alt-text ao manifesto existente, preservando todas as entradas antigas e os nomes canônicos.
- Para exceções (p.ex. Saint-Louis com foto pequena, Amsterdam com imagem cartográfica), escolher manualmente outro arquivo específico do mesmo lugar, validando novamente a licença.

## Integração

Ordem: foto editorial histórica → foto WebP local → foto externa licenciada → placeholder. Nunca acionar Commons/Wikipedia em runtime para destinos já cobertos. Usar o adaptador `destination_photo_assets.local_destination_photo()` e manter `st.image()` para servir os arquivos locais.

## Testes obrigatórios

- Cobertura igual a 100% dos destinos atuais.
- Identidade do ID, existência e formato WebP de todos os assets, dimensões 800×450, hashes distintos, origem/copyright/autor e `alt`.
- Rejeição de paths inseguros, arquivos não encontrados e direitos de uso inválidos.
- AppTest de todas as páginas, com lookup online mockado para falhar se chamado.
- Ausência de mudanças em `TripPlan`, persistência, interesses, ranking ou navegação.
- CI GitHub Actions verde. **Não afirmar verificação visual em desktop/mobile sem navegador real.**
- Não fazer merge ou deploy sem aprovação explícita.

## Diagnóstico e resultado da execução

Auditoria factual realizada na branch sobre a `main` (17/11/2026):
- **46 destinos** no catálogo;
- **10** já tinham foto editorial;
- **5** já tinham foto local fixa;
- **31** estavam sem imagem fixa.

Foram preparadas 30 imagens automaticamente com validação de licença, e as duas exceções foram curadas manualmente: Amsterdam recebeu fotografia de canais no lugar de diagrama e Saint-Louis recebeu fotografia da antiga prefeitura, licenciada em resolução suficiente.

**Cobertura final: 46 de 46** (10 fotos editoriais e 36 fotos locais). Relatório detalhado em `docs/UX_ALL_DESTINATION_PHOTOS_COVERAGE.json`.

## Limitações e manutenção

Fotos editadas são redistribuídas sob suas licenças próprias, separadamente do código. Revalidar com o Commons quando for atualizar imagens: autor, licenças e origem não podem ser inferidos. Registros históricos de rota e custos não são deduzidos de fotografias. A publicação exige reinício/redeploy da aplicação Streamlit quando novos binários são adicionados e ainda requer inspeção real no navegador.
