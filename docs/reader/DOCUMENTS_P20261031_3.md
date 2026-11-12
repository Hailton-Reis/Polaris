# Polaris P20261031.3 — documentos e pesquisa

## Atualização

Use o fluxo local habitual: atualize a branch de engenharia, compile pela opção **4** do CMD e instale pela opção **9**, mantendo a assinatura local. Confira **Polaris P20261031.3** em **Sobre**. A revisão é independente do versionCode Android e da data da compilação.

A rodada anterior confirmou que desligar **Cortar bordas** alinhou as traduções salvas. Este candidato inclui a proteção automática de P20261031.2 e o suporte inicial a documentos. Não é necessário repetir OCR apenas para conferir o alinhamento.

## Conferência no Android — pendente

Os [arquivos de exemplo](../../integration/document-reader/fixtures) são material original em inglês para estes testes.

1. Em **Mais → Documentos e pesquisa**, importe PDF, EPUB, DOCX e TXT pelo seletor Android. Confira a entrada na biblioteca e abra seu capítulo.
2. No PDF, confira as duas páginas e as figuras. Avance, feche e reabra. Use a tradução do capítulo; confira o resultado no paginado e na faixa longa, incluindo zoom. Com **Cortar bordas** ativado, uma página traduzida deve preservar a geometria e o alinhamento.
3. No EPUB, confira a ordem das duas seções, o texto e a imagem. No DOCX, confira parágrafos, imagem e texto das células. O layout é refluído; não deve ser comparado à paginação do Word.
4. No EPUB/DOCX/TXT, ajuste a fonte, role, mude de seção, feche e reabra. Confira a retomada de seção e posição. Traduza a seção, alterne original/tradução e marque como lido ao terminar. Configure entrada em inglês e saída em português antes de comparar os exemplos.
5. Busque um artigo por título, autor e DOI. Confira Crossref/Europe PMC, a indicação de origem e a importação de um PDF disponível. Resultado bibliográfico sem arquivo deve oferecer a página da fonte.
6. Busque um livro, por exemplo *Pride and Prejudice*. Confira Gutendex/Open Library e importe um EPUB disponível. Teste também a URL de um arquivo direto.
7. No campo de site configurável, use `https://duckduckgo.com/?q={query}` ou outro site escolhido. Confira a pesquisa dentro do app e a persistência da configuração ao voltar.
8. Pelo gerenciador de arquivos Android, use **Abrir com / Compartilhar → Polaris** em um documento. Teste um arquivo inválido ou um link HTML apresentado como PDF: deve mostrar erro sem substituir documentos já importados.

Registre a revisão em Sobre, formato, ação e resultado. Estes passos permanecem pendentes até a execução no dispositivo; os testes automatizados não os substituem.
