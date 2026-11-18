# UX Sidebar — navegação clara e sincronização sob demanda

## Papel e objetivo
Atue como Senior Product Engineer, UX Designer e Senior Python/Streamlit Engineer. Simplifique a sidebar do Nossa Europa 2027 sem alterar o backend, o TripPlan ou o comportamento das áreas.

## Contexto
A sidebar anterior combinava quatro destinos de navegação, radio legado, três indicadores de fontes, duas ações do Drive e um aviso extenso, dando peso excessivo a informações secundárias.

## Escopo
1. Compactar o branding "Nossa Europa 2027" sem eliminar o contexto da viagem.
2. Preservar exatamente quatro entradas de navegação: Minha viagem, Explorar destinos, Meu roteiro e Orçamento. Mostrar seleção visível com fundo, borda e foco; evitar segundo estado de navegação.
3. Remover os textos redundantes "ONDE VOCÊ QUER IR?" e "Escolha uma tarefa dentro de cada área".
4. Exibir resumo de fontes sincronizadas e colocar datas por fonte, data da operação, atualização manual, acesso à pasta e diagnóstico no painel "Google Drive · detalhes", fechado inicialmente.
5. Preservar distinção entre consulta ao Drive, modified_at de cada fonte e snapshot local. Não afirmar que o arquivo foi modificado só porque a sincronização rodou.
6. Mover acesso legado para "Fontes e ferramentas", recolhido por padrão, mantendo callbacks e chaves atuais.
7. Substituir aviso extenso de desenvolvimento por indicação discreta; preservar aviso completo de não-reserva na área "Minha viagem".
8. Preferir componentes Streamlit; limitar estilos ao widget de navegação atual com foco acessível.

## Restrições de arquitetura
- Nunca duplicar ux_area, main_navigation, ou introduzir estado paralelo.
- Não modificar planejamento oficial, autenticacão, ações de salvamento, orçamentos, dados ou cadastros.
- Não eliminar funcionalidades legadas nem renomear suas chaves.
- Os dados da sincronização podem estar indisponíveis ou parcialmente disponíveis; a UI deve ser verdadeira em cada cenário.
- Não adicionar dependências.

## Critérios de aceite / validação
- As quatro áreas e atalhos de transição continuam operando com mesmo estado.
- Item ativo permanece evidente; navegação por teclado tem foco identificável.
- Detalhes do Drive e ferramentas legadas começam recolhidos.
- Mensagem-resumo correta para live (3/3), partial (N/3) e snapshot (0/3).
- Data de consulta não se confunde com data modified_at das fontes; erros de sincronização continuam acessíveis.
- Botões Atualizar e Abrir Drive permanecem funcionais.
- Informações de ausência de reservas permanecem na tela Minha viagem.
- Testar em telas desktop e mobile, além de executar compileall e suíte existente.

## Fora do escopo
Redesenhar páginas internas, substituir o roteador Streamlit por st.navigation, editar dados turísticos, modificar o TripPlan, alterar serviços do Drive ou fazer merge do DATA 10.

## Verificações recomendadas
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```
Registrar limitações e resultado de CI antes do merge.
