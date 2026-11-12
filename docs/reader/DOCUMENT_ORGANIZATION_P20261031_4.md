# Polaris P20261031.4 — inclusão seletiva e organização

O candidato anterior já permitia selecionar um arquivo do celular. Esta revisão acrescenta a organização antes da inclusão. O Polaris não pesquisa nem inclui todos os PDFs do aparelho.

## Fluxo

1. Abra **Mais → Documentos e pesquisa → Explorar e adicionar arquivo**. O seletor Android permite navegar até Downloads e outras pastas acessíveis.
2. Escolha um arquivo. Na tela **Organizar documento**, confira o nome e o formato. O título na biblioteca é opcional; em branco, o app preserva os metadados do documento ou o nome do arquivo.
3. Escolha **Mangás, Manhwas, Quadrinhos, Livros, Artigos ou Documentos**. Um PDF pode pertencer a qualquer um desses tipos; não há classificação automática como livro pela extensão.
4. Deixe **Agrupar também pelo formato do arquivo** ativado para incluir uma categoria como **Formato: PDF**. Você também pode selecionar suas categorias existentes e criar uma categoria pessoal, por exemplo **Estudos**.
5. Toque em **Adicionar à biblioteca**. O app copia apenas o arquivo escolhido para seu armazenamento local e organiza a entrada nas categorias selecionadas. O original não é movido ou apagado.

**Cancelar** fecha a seleção sem copiar o arquivo ou criar uma entrada na biblioteca. Links, resultados de pesquisa e documentos recebidos por **Abrir com / Compartilhar** usam a mesma organização antes da inclusão.

As categorias são as mesmas da biblioteca atual: podem ser reorganizadas ou alteradas pelo editor já existente. Nomes correspondentes são reutilizados. A revisão não recategoriza automaticamente a biblioteca antiga. Reimportar manualmente o mesmo arquivo continua sendo uma nova importação; não há deduplicação por conteúdo nesta versão.

## Conferência no Android — pendente

Use as opções locais habituais **4** (compilar) e **9** (instalar), preservando a assinatura local, e confira **Polaris P20261031.4** em **Sobre** quando for iniciar a rodada de testes.

- Deixe vários PDFs em Downloads. Selecione apenas um e cancele a tela de organização: nenhum deve virar favorito ou ser copiado por essa seleção.
- Adicione um PDF como **Livros** e outro como **Artigos**, ambos com agrupamento de formato. Confira **Livros**, **Artigos** e uma única categoria **Formato: PDF** na biblioteca.
- Selecione uma categoria existente, como **Estudos**, e confira que ela foi preservada. Adicione outro documento à mesma categoria sem duplicá-la. Teste também uma nova categoria pessoal.
- Desative o agrupamento de formato em outra inclusão. A entrada deve receber o tipo e as categorias pessoais escolhidas, sem a categoria de formato.
- Teste o título opcional em um EPUB com metadados, incluindo deixar o campo em branco. Confira leitura, tradução e retomada conforme o [roteiro dos leitores](DOCUMENTS_P20261031_3.md).
- Use **Compartilhar → Polaris** no gerenciador de arquivos e escolha um resultado da busca. Ambos devem abrir a organização e aguardar **Adicionar à biblioteca**.

Os testes automatizados cobrem descrição da seleção sem abertura/cópia, categorias, concorrência e propagação de falhas. Seletor, diálogo e gravação no armazenamento Android ainda exigem esta conferência no dispositivo.
