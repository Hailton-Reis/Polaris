# Comece aqui

## Antes de instalar

O Polaris tem um candidato compilado, mas ainda não possui lançamento estável ou APK publicado nas Releases. A revisão crítica de armazenamento está [registrada aqui](ARMAZENAMENTO.md). Instalação, consumo total e leitura nos aparelhos continuam pendentes de aceite.

A apresentação do projeto fica em `main`. A implementação em avaliação está em [r001/multisource-foundation](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation). Não é necessário criar outro repositório para acompanhar o Polaris.

## Acesso atual para desenvolvimento e teste interno

O mantenedor utiliza o [CMD de preparação do Windows](https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/tools/windows-setup/00_POLARIS_TUDO_EM_UM.cmd). A opção 4 compila e pode gerar o pacote local `beta/`, com APKs ARM, exemplos e hashes. Essa geração não aprova automaticamente o armazenamento ou os testes nos aparelhos.

O pacote atual usa versão `0.1.0-beta.1`, revisão `P20261101.1` e versionCode 102. Atualizações precisam manter a assinatura da instalação anterior para conservar a continuidade dos dados. Uma recompilação pode ter data, assinatura e hash diferentes; use o manifesto e `SHA256SUMS.txt` do pacote efetivamente recebido.

Os APKs ARM64 e ARM32 destinam-se às respectivas arquiteturas do sistema Android; x86 é para ambientes de desenvolvimento compatíveis. O mínimo é Android 8. O modelo comercial do aparelho não substitui essa verificação.

## Incluir um arquivo já baixado no celular

1. Abra **Mais → Documentos e pesquisa → Explorar e adicionar arquivo**.
2. Escolha um arquivo no seletor Android.
3. Confira o título opcional e escolha o tipo de conteúdo.
4. Use suas categorias existentes ou crie uma categoria pessoal; o agrupamento por formato é opcional.
5. Toque em **Adicionar à biblioteca**.

Cancelar essa tela não inclui o arquivo. A inclusão guarda uma cópia gerenciada e mantém o original no celular; isso aumenta o espaço usado. Repetir a importação ainda pode criar outra cópia.

## Traduzir

- Comece com ML Kit e os idiomas de entrada/saída desejados. Os modelos precisam ser baixados antes do uso offline.
- Em fontes conhecidas, os metadados podem selecionar inglês, japonês, chinês ou coreano para o OCR. Documentos locais e fontes desconhecidas/mistas usam a entrada escolhida manualmente.
- A tradução automática dos downloads pode ser configurada por obra. A automação global dos idiomas asiáticos é opcional nesta candidata.
- Use o glossário no menu da obra para nomes e termos recorrentes. O vocabulário também é consultado na tradução textual de documentos.
- PaddleOCR permanece apenas em inglês; os testes de idiomas asiáticos devem usar ML Kit.

O resultado favorável em inglês foi observado em candidato anterior. Qualidade em japonês, chinês e coreano, especialmente em leitura vertical e páginas difíceis, ainda precisa de conferência nos aparelhos e revisão por falantes desses idiomas.

## Conferir o armazenamento

Abra **Dados e armazenamento → Armazenamento do Polaris**. O painel distingue parcelas, mas oferece uma estimativa; um `+` indica medição incompleta.

**Limpar cache regenerável de documentos** mantém originais importados, downloads, traduções salvas dos capítulos, modelos e vocabulário. Páginas de PDF podem ser renderizadas novamente e texto de documentos pode precisar de nova tradução.

Excluir um capítulo baixado pelo fluxo do app remove também sua tradução e frases de cache relacionadas, preservando glossário/correções. Remover favorito, apagar externamente um arquivo ou limpar dados do app são operações diferentes. O ciclo de exclusão e novo download ainda precisa da validação física descrita na análise de armazenamento.

## Relatar um problema

Use [Issues](https://github.com/Hailton-Reis/Polaris/issues/new/choose) com revisão em Sobre, aparelho/Android e passos. Para armazenamento, informe o tipo/tamanho do arquivo e os números antes/depois. Evite incluir chaves de API ou documentos pessoais; os exemplos originais da engenharia ajudam a reproduzir o caso.
