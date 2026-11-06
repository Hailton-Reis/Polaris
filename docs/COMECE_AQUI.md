# Comece aqui

## Baixar e instalar

O [beta.10 público](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10) está disponível para experimentar. Ainda não há lançamento estável. Instalação, continuidade dos dados e consumo nos aparelhos continuam pendentes de aceite.

1. Abra a Release no navegador do celular. Não é necessário ter conta do GitHub.
2. Baixe **Polaris-0.1.0-beta.10-universal.apk** (261,1 MB). O Android escolhe as bibliotecas ARM32 ou ARM64 compatíveis na instalação.
3. Abra o arquivo no Android e confirme a instalação. Se já usa o Polaris, instale como atualização.
4. Confira **Polaris 0.1.0-beta.10 / P20261106.1** em Sobre.

O mínimo é Android 8. A arquitetura do sistema instalado importa: ter processador de 64 bits não garante Android de 64 bits. O modelo comercial do celular não substitui essa verificação. Os APKs do GitHub são arquivos completos; não é necessário juntar partes nem executar CMD.

A identidade visual é Polaris. Os arquivos publicados mantêm identificador e assinatura da beta.3 distribuída; se houver conflito de assinatura, preserve a instalação e os dados para investigação. Use sempre o manifesto e os hashes do pacote efetivamente recebido: recompilações podem ter hashes e assinaturas diferentes.

## Preparar repositórios e extensões

Guarde uma cópia do backup do aplicativo de origem antes de migrar. Após a configuração inicial, o guia **Preparar fontes** permite importar esse backup primeiro; também pode ser aberto em **Navegar → Extensões → ⋮ → Preparar fontes**.

1. Leia a explicação e confirme ciência dos riscos de extensões de terceiros, ou adie a preparação.
2. Revise um repositório sugerido ou informe um link HTTPS; confira endereço e certificado antes de adicionar.
3. Escolha fontes da biblioteca, idiomas ou uma seleção manual. Fontes adultas exigem opção explícita; conflitos e versões incompatíveis são informados.
4. Revise a quantidade e confirme o lote. O Polaris baixa e instala as novas extensões internamente, com progresso, cancelamento e repetição das falhas. As extensões já instaladas pelo Android são preservadas.

A fila continua fora da tela enquanto o processo existir. Se o Android encerrar o app, reabra o guia para preparar o que falta. **Preserve o backup original: a exportação de capítulos mesclados para outros leitores ainda precisa de normalização e teste real.** O backup não inclui APKs privados: ao voltar ao Mihon/Tachiyomi, instale as fontes nesse aplicativo. O formato e os identificadores foram preservados; restauração/mescla real e todos os forks ainda não foram validados. O campo Mihon `nextUpdate` não é preservado. [Notas e roteiro completo](versoes/0.1.0-beta.10.md).

**Segurança:** as extensões atuais ainda executam fora de sandbox completa, no processo do app. A inspeção preventiva e a quarentena não garantem ausência de riscos; revise os motivos antes de conceder exceções.

## Capítulos e fontes

A lista reúne versões do mesmo capítulo em uma posição, evitando repetir Official/Unofficial na sequência. Não confunde números decimais, partes, volumes, temporadas ou extras identificados.

Em **Opções de capítulos → Fontes desta obra**, deixe Automático ou escolha uma fonte fixa. A busca automática consulta extensões instaladas e habilitadas nos idiomas selecionados, confirma título/autoria/numeração e verifica amostras de páginas e bytes de imagem. Entre alternativas aprovadas, prioriza português; habilite português nos filtros se desejar incluí-lo. Não testa todos os capítulos nem baixa capítulos completos dos catálogos. A lista principal é salva antes da descoberta adicional. Se a identidade da obra for ambígua, a fonte atual é mantida.

Trocar a preferência preserva arquivos e histórico. Mantenha a extensão original instalada neste candidato. Verifique o resultado com fontes reais e acompanhe [o roteiro de teste](https://github.com/Hailton-Reis/Polaris/releases/download/v0.1.0-beta.10/COMECE_AQUI.md).

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

**Sobre** reúne descrição, versão/revisão, mantenedor, créditos, projeto, histórico, Releases, licenças e privacidade. Em **Configurações → Atualizações do aplicativo**, a busca automática começa ativada e **Receber atualizações experimentais** começa desativado. A verificação manual respeita esse canal. O repositório e a Release são públicos, com download pelo navegador sem login. A atualização pelo app ainda precisa de teste no aparelho. [Como funciona](ATUALIZACOES.md).

## Como funciona o APK universal?

A beta.10 oferece **um APK de 261,1 MB**, com recursos comuns compartilhados e bibliotecas ARM32 e ARM64. O Android escolhe as bibliotecas compatíveis durante a instalação; não é necessário identificar manualmente a arquitetura nem baixar uma segunda versão. Um processador de 64 bits pode usar Android de 32 bits, e a seleção respeita o sistema instalado.

O pacote inclui ambas as arquiteturas e continua sendo um download completo; o consumo instalado e o temporário do instalador precisam de medição no aparelho. As Releases anteriores mantêm seus APKs separados por arquitetura.

## Compilar para desenvolvimento

A apresentação fica em `main`; o código integrado desta versão está na [tag beta.10](https://github.com/Hailton-Reis/Polaris/tree/v0.1.0-beta.10). O [CMD de preparação do Windows](https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/tools/windows-setup/00_POLARIS_TUDO_EM_UM.cmd) é uma ferramenta de desenvolvimento. A opção 4 compila e pode exportar um pacote local com APKs, exemplos e hashes. Compilar não aprova automaticamente os testes físicos nem reproduz a assinatura da distribuição.
