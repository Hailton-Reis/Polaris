# Comece aqui

## Antes de instalar

O Polaris tem seu [primeiro pré-lançamento privado publicado](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3), para o mantenedor testar primeiro. Ainda não possui lançamento estável. A revisão crítica de armazenamento está [registrada aqui](ARMAZENAMENTO.md). Instalação, consumo total e leitura nos aparelhos continuam pendentes de aceite.

A apresentação do projeto fica em `main`. A implementação em avaliação está em [r001/multisource-foundation](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation). Não é necessário criar outro repositório para acompanhar o Polaris.

## Acesso atual para desenvolvimento e teste interno

O mantenedor utiliza o [CMD de preparação do Windows](https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/tools/windows-setup/00_POLARIS_TUDO_EM_UM.cmd). A opção 4 compila e pode gerar o pacote local `beta/`, com APKs ARM, exemplos e hashes. Essa geração não aprova automaticamente o armazenamento ou os testes nos aparelhos.

O pacote atual usa versão `0.1.0-beta.3`, revisão `P20261101.3` e versionCode 104. Atualizações precisam manter a assinatura da instalação anterior para conservar a continuidade dos dados. Uma recompilação pode ter data, assinatura e hash diferentes; use o manifesto e `SHA256SUMS.txt` do pacote efetivamente recebido.

Os APKs ARM64 e ARM32 destinam-se às respectivas arquiteturas do sistema Android; x86 é para ambientes de desenvolvimento compatíveis. O mínimo é Android 8. O modelo comercial do aparelho não substitui essa verificação.

## Incluir um arquivo já baixado no celular

1. Abra **Mais → Documentos e pesquisa → Explorar e adicionar arquivo**.
2. Escolha um arquivo no seletor Android.
3. Confira o título opcional e escolha o tipo de conteúdo.
4. Use suas categorias existentes ou crie uma categoria pessoal; o agrupamento por formato é opcional.
5. Toque em **Adicionar à biblioteca**.

Cancelar essa tela não inclui o arquivo. A inclusão guarda uma cópia gerenciada e mantém o original no celular; isso aumenta o espaço usado. Repetir a importação ainda pode criar outra cópia.

## Traduzir

- O reconhecimento de texto em inglês já acompanha o APK. A preparação automática do par inglês → português é ativada por padrão, aguardando rede sem cobrança e a condição de espaço do Android. O cartão só exibe Pronto depois da preparação e verificação do SDK.
- Ainda há uma conexão inicial necessária para os recursos de tradução. Use Preparar agora para solicitar o uso da conexão atual. [Veja a diferença entre OCR e tradução](INGLES_E_TRADUCAO.md).
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

## Sobre e atualização do aplicativo

**Sobre** reúne descrição, versão/revisão, mantenedor, créditos, projeto, histórico, Releases, licenças e privacidade. Em **Configurações → Atualizações do aplicativo**, a busca automática começa ativada e **Receber atualizações experimentais** começa desativado. A verificação manual respeita esse canal. O repositório ainda é privado; a atualização sem login depende de Releases acessíveis e continua pendente. [Como funciona](ATUALIZACOES.md).

## Por que há dois APKs?

São alternativas para o mesmo aplicativo. Baixe e instale **um**: `arm64-v8a` para Android de 64 bits (196,2 MB) ou `armeabi-v7a` para Android de 32 bits (156,4 MB). A arquitetura do sistema instalado importa; ter processador de 64 bits não garante Android de 64 bits.

Os arquivos separados evitam incluir ambas as arquiteturas em cada download. Um APK universal poderia reuni-las, com tamanho maior. Quando a consulta de atualizações estiver acessível, o atualizador usa os metadados do aparelho para escolher o arquivo compatível.
