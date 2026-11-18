# UX Sidebar 142.1 — correção visual real (PR corretivo)

## Problema
O PR #142 compactou estrutura e sincronização, mas dependeu do seletor
`[data-testid="stSidebar"] .st-key-ux_area [role="radiogroup"] > label:has(input:checked)`.
Uma pipeline verde não garante que o menu renderizado tenha destaque visual.

## Mudanças propostas
- Substituir apenas o controle de navegação principal (`st.radio`) por quatro
  `st.button` nativos, com ícones Material e largura integral.
- Manter `ux_area`, `set_ux_area` e `_ux_area_changed` como **único** estado/callback de navegação.
- Usar `type="primary"` para a seção selecionada e `type="secondary"` para as outras.
- Usar `st.container(gap="xxsmall")` para reduzir espaçamento de botões.
- Remover o CSS frágil específico da seleção de `st.radio` e o divisor extra.
- Preservar o painel de sincronização recolhido, ferramentas legadas e TripPlan.

## Validação técnica
- AppTest: quatro botões existem, os cliques atualizam `ux_area` e
  o plano oficial permanece intacto.
- Testes de navegação existentes deixam de depender de `app.radio(key="ux_area")`.
- Não há novo estado de navegação nem dependências adicionadas.
- Rodar `python -m unittest discover -s tests -v` e `python -m compileall -q .`.

## Aceite **visual** obrigatório — pendente até captura real
1. Publicar a branch de teste sem substituir produção, ou validar localmente.
2. Executar `python scripts/capture_sidebar_visuals.py --url https://APP-TESTE.streamlit.app`
   em máquina com Playwright e Chromium.
3. Comparar as imagens `sidebar-desktop.png` (1440×900) e
   `sidebar-mobile.png` (390×844) com o esboço da sidebar:
   - logo compacto sem espaço vazio excessivo;
   - quatro itens com ícones, área clicável integral e espaçamento consistente;
   - seleção claramente visível por cor de fundo;
   - estado de foco perceptível ao navegar por teclado;
   - bloco de sincronização secundário e recolhido;
   - sem cortes/rolagem horizontal indevida no mobile.
4. Clicar nas quatro áreas e fotografar ao menos o estado ativo de cada uma.
5. Inspecionar acessibilidade de foco e contraste. Screenshots sozinhas
   não validam comportamento de teclado.
6. Registrar evidência visual ou ressalva explícita antes do merge.

**Status:** screenshot real e comparação ainda não executados nesta sessão.
O PR deve permanecer draft até essa revisão; não declarar "UX concluída" por CI verde.
