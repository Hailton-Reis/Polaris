<p align="center">
  <img src="docs/assets/polaris-hero.png" alt="Polaris — um livro aberto transforma suas páginas em constelações sob a estrela do norte" width="100%">
</p>

<p align="center">
  <strong>Mangás, livros e documentos. Sua biblioteca, no seu ritmo e no seu idioma.</strong><br>
  Um leitor para Android com tradução, vocabulário consistente e organização por você.
</p>

<p align="center">
  <a href="https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10"><strong>Baixar beta.10 →</strong></a> &nbsp; · &nbsp;
  <a href="docs/COMECE_AQUI.md"><strong>Comece aqui</strong></a> &nbsp; · &nbsp;
  <a href="CHANGELOG.md"><strong>Versões e novidades</strong></a> &nbsp; · &nbsp;
  <a href="docs/ARMAZENAMENTO.md"><strong>Armazenamento</strong></a>
</p>

<table>
  <tr>
    <td width="33%" valign="top"><strong>01 · Leia</strong><br><br>Quadrinhos, livros e artigos. Leitura por páginas ou por texto, com retomada de posição.</td>
    <td width="33%" valign="top"><strong>02 · Traduza</strong><br><br>Inglês como prioridade. Tradução no aparelho, glossário por obra e nomes protegidos.</td>
    <td width="33%" valign="top"><strong>03 · Organize</strong><br><br>Escolha o que entra na biblioteca. Separe conteúdo, formatos e categorias pessoais.</td>
  </tr>
</table>

## Uma biblioteca que acompanha você

O Polaris reúne a leitura de quadrinhos, livros e documentos em um aplicativo Android. Você pode acompanhar capítulos de suas fontes, adicionar um livro já baixado no celular ou encontrar um artigo por título, autor ou DOI.

A leitura básica funciona no aparelho, sem exigir um servidor pessoal. Arquivos locais e capítulos baixados podem ser lidos offline. A tradução com ML Kit também pode funcionar offline depois da preparação dos recursos necessários.

**Em desenvolvimento · Android 8+ · ARM64 e ARM32 · Foco em português brasileiro**

**Beta público atual: [0.1.0-beta.10 · P20261106.1](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10).** APK universal ARM32/ARM64, recuperação de fontes após backups, preferência por português entre alternativas verificadas e inspeção preventiva de extensões. A versão é um pré-lançamento para testes; ainda não há versão estável.

## Inglês como prioridade

**O reconhecimento de texto em inglês já acompanha o APK.** O Polaris inclui OCR ML Kit e PaddleOCR para inglês; os demais idiomas suportados usam ML Kit. OCR lê a imagem; o mecanismo de tradução trabalha com o texto reconhecido.

Para **traduzir inglês → português**, o SDK precisa preparar seus recursos de tradução. O novo candidato acrescenta:

- Verificação local dos recursos já disponíveis, inclusive offline.
- Preparação automática ativada por padrão quando faltam recursos, em conexão sem cobrança e com a condição de espaço disponível do Android.
- Um cartão que mostra preparação, espera, falha ou disponibilidade do par.
- A opção **Preparar agora**, usando a conexão atual.
- A indicação **Pronto** somente depois da conclusão do SDK e de uma tradução de verificação no aparelho.

**Há uma conexão inicial necessária.** Os recursos de tradução são gerenciados por download pelo SDK; eles não foram inseridos manualmente dentro do APK. A preparação não troca os idiomas de OCR e saída que você escolheu, e pode ser desativada nas configurações.

A instalação inicial, o download e o funcionamento offline dessa preparação ainda precisam da conferência nos celulares. [Entenda os componentes e o primeiro uso](docs/INGLES_E_TRADUCAO.md).

## Atualizações no seu controle

O candidato consulta as Releases do **Polaris** ao abrir o aplicativo, com limite de uma tentativa automática por dia por canal, e oferece verificação manual em **Sobre** e nas configurações.

**Receber atualizações experimentais** começa desativado. Ative para encontrar betas e outras prévias publicadas; desligar não rebaixa a instalação. Baixar e instalar continuam sendo escolhas suas.

**O repositório e o [beta.10 público](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10) estão disponíveis**, com um APK universal para ARM64 e ARM32 (261,1 MB), disponível pelo navegador sem login no GitHub. A atualização real no aparelho ainda precisa de validação. [Canais, compatibilidade e publicação →](docs/ATUALIZACOES.md)

## Prepare as fontes pelo aplicativo

Depois da configuração inicial, use **Preparar fontes**; o guia também fica em **Navegar → Extensões → ⋮**. A introdução explica os riscos de código de terceiros, permite importar um backup primeiro e pode ser adiada.

Revise um repositório sugerido ou informe um link HTTPS. Confira endereço e certificado, selecione fontes da biblioteca, idiomas ou uma lista manual e confirme o lote. O Polaris prepara as extensões **dentro do próprio aplicativo**, com progresso, cancelamento e repetição das falhas. Não é preciso confirmar uma instalação Android para cada nova extensão desse fluxo. As extensões já instaladas pelo Android são preservadas.

A fila depende do processo do aplicativo e não retoma downloads de extensões após seu encerramento. **Guarde o backup original.** O formato e os identificadores continuam existentes, mas capítulos mesclados podem usar URLs específicas do Polaris, cuja exportação para Mihon/Tachiyomi ainda precisa de normalização. APKs privados não acompanham o backup: instale as fontes no outro leitor. A migração real em banco e o percurso completo no celular continuam pendentes. [Roteiro e limites](docs/versoes/0.1.0-beta.10.md).

## Uma sequência, com fontes por obra

Capítulo 0 Official e capítulo 0 Unofficial agora ocupam uma única posição na leitura. A mesma identidade atende retomada, próximos capítulos, downloads e contagens. As edições e seus arquivos permanecem guardados; partes, decimais, volumes, temporadas e extras identificados continuam separados.

Em **Opções de capítulos → Fontes desta obra**, deixe **Automático** ou escolha uma fonte fixa para aquela obra. A descoberta compara extensões instaladas e habilitadas nos idiomas selecionados, confirmando título, autoria e numeração. Verifica amostras de páginas e bytes de imagem e, entre as alternativas aprovadas, prioriza português; a fonte fixada é respeitada. Não testa todos os capítulos nem mede a qualidade editorial da tradução.

A descoberta usa metadados e amostras limitadas, sem instalar extensões nem baixar capítulos completos de todos os catálogos. Após restaurar um backup, também pode recuperar fontes de obras antigas e concluídas. A escolha da fonte também preserva o escopo do glossário. [Comportamento e limites](https://github.com/Hailton-Reis/Polaris/blob/v0.1.0-beta.10/docs/UNIVERSAL_FONTES_SEGURANCA_P20261106_1.md).

## Seu arquivo, sua classificação

```text
Escolha um arquivo → dê um lugar a ele → adicione à biblioteca
```

O seletor Android permite explorar as pastas acessíveis do celular. **O Polaris inclui os arquivos que você escolher**, sem pesquisar todos os PDFs do aparelho.

Você decide se o conteúdo é mangá, manhwa, quadrinho, livro, artigo ou documento. O formato pode virar um agrupamento adicional, como **Formato: PDF**. Suas categorias existentes podem ser reutilizadas, e novas categorias pessoais podem ser criadas.

Cancelar a organização não adiciona o arquivo. Ao incluir, o app mantém o original e guarda uma cópia gerenciada; essa escolha também tem um custo de armazenamento.

## Diferentes leituras, no mesmo lugar

| O que você abre | Como o candidato apresenta |
| --- | --- |
| Quadrinhos compactados | Leitor de imagens, paginado ou em faixa longa |
| PDF | Páginas renderizadas, figuras e tradução por OCR |
| EPUB | Texto por seções e imagens locais compatíveis |
| DOCX e TXT | Texto refluído, ajuste de fonte e retomada |

EPUB e DOCX não reproduzem integralmente a paginação do Word, fórmulas, estilos ou tabelas complexas. O PDF atual é traduzido por OCR, inclusive quando contém texto selecionável.

### Encontrar a próxima leitura

A pesquisa inicial consulta **Crossref e Europe PMC** para artigos, e **Gutendex e Open Library** para livros. Cada resultado mantém sua origem. Você também pode escolher um site de pesquisa para abrir dentro do app ou importar um link direto compatível.

A disponibilidade depende da fonte: um registro bibliográfico pode não oferecer o texto completo, e a busca não cobre toda a internet.

### Manter o fio da tradução

O glossário por obra conserva nomes e termos recorrentes. Correções aprendidas também podem ser reutilizadas. A tradução textual de documentos consulta esse mesmo vocabulário.

Excluir um capítulo baixado pelo fluxo do app remove sua tradução e as frases automáticas relacionadas, preservando glossário e correções. Um novo download segue a configuração automática da obra. Remover favorito, apagar externamente um arquivo e limpar dados do app são operações diferentes.

## Espaço precisa ser visível

O consumo envolve **instalação, modelos, originais, cópias, traduções e caches**. O tamanho do JSON de tradução, sozinho, não representa todo esse custo.

| Parcela | O que sabemos |
| --- | --- |
| Tradução salva | Ensaio sintético de 20 páginas/200 blocos: 48–53 kB; o custo real varia |
| Modelos de tradução | Referência do Google: aproximadamente 30 MB por idioma, reutilizados entre capítulos |
| Cache de documentos | Meta de 256 MiB; arquivos abertos podem ultrapassá-la temporariamente |
| Importação e leitura | Podem manter original, cópia gerenciada, materialização e temporários |

O painel **Dados e armazenamento → Armazenamento do Polaris** ajuda a separar essas parcelas. A limpeza do cache regenerável preserva importados, traduções salvas dos capítulos, modelos e vocabulário; páginas e texto em cache podem precisar ser preparados novamente.

**A revisão de armazenamento continua prioritária.** A meta de cache é parcial e a importação pode duplicar documentos. O pico de espaço, as falhas com armazenamento cheio e o consumo total precisam ser verificados nos aparelhos. [Leia a análise crítica e as próximas verificações →](docs/ARMAZENAMENTO.md)

## Onde o projeto está

O beta público atual é **`0.1.0-beta.10` · revisão `P20261106.1` · versionCode `111`**. Ele reúne um APK universal, recuperação de fontes, perfis com menos concorrência em processos limitados e inspeção preventiva/quarentena de extensões. Mantém o assistente de fontes, OCR e download de atualização recuperável da beta.9. PaddleOCR continua opcional em inglês.

**[Baixar e ver as notas da beta.10](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10)** · **[Primeiro teste](https://github.com/Hailton-Reis/Polaris/releases/download/v0.1.0-beta.10/COMECE_AQUI.md)**. Baixe o único APK universal para ARM32 e ARM64; o Android escolhe a arquitetura compatível durante a instalação. Não é necessário montar partes ou escolher entre duas versões.

**A sandbox completa ainda não está integrada:** extensões atuais executam no processo do aplicativo, com aviso de compatibilidade. A inspeção não garante ausência de código malicioso. **A exportação de obras mescladas para outros leitores ainda precisa de ajuste e teste real.** Preserve o backup original. A causa da falha de capítulos relatada no A12 e qualquer ganho de desempenho nesse aparelho ainda precisam de confirmação.

A comparação final executou **738 testes JVM: 721 aprovações e as mesmas 17 falhas preexistentes**, sem novas falhas ou casos ausentes/ignorados. Os 31 casos novos passaram, além de 13 controles do empacotamento/overlay e seis controles Android de isolamento em componente independente. Isso não equivale a uma suíte totalmente verde, sandbox integrada ou aceite em aparelhos. A [implementação](https://github.com/Hailton-Reis/Polaris/tree/v0.1.0-beta.10) e a [evidência](https://github.com/Hailton-Reis/Polaris/blob/v0.1.0-beta.10/integration/universal-recovery/20261106/TEST_RESULTS.json) estão identificadas pela versão. Ainda não há lançamento estável.

O resultado em inglês foi confirmado pelo mantenedor em um candidato anterior. Japonês, chinês simplificado/tradicional e coreano continuam com validação de OCR e tradução nas imagens pendente, incluindo japonês vertical. A automação global desses idiomas é opcional neste estágio; PaddleOCR permanece apenas em inglês.

A matriz inicial reúne **A12, S20 FE, S8+ e provável A52**. Android, arquitetura, instalação e desempenho ainda precisam ser confirmados em cada unidade.

## Acompanhe a evolução

- **[Histórico de versões](CHANGELOG.md)** — o que mudou e qual o estado de cada revisão.
- **[Próximos passos](docs/ROADMAP.md)** — armazenamento, testes e evolução da leitura.
- **[Releases](https://github.com/Hailton-Reis/Polaris/releases)** — beta público disponível para experimentar; rascunhos permanecem identificados.
- **[Relatar um problema](https://github.com/Hailton-Reis/Polaris/issues/new/choose)** — revisão em Sobre, aparelho, passos e resultado observado.

<details>
<summary><strong>Base técnica e validação</strong></summary>

A base Android vem do ecossistema **Yomotsu / Mihon**, com conceitos de múltiplas fontes do **TachiyomiSY**. A integração mantém um upstream fixado e camadas revisáveis. A branch `main` apresenta o projeto; a implementação em avaliação fica em `r001/multisource-foundation`.

[Registros de compilação e testes](https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/integration/document-reader/TEST_RESULTS.json) distinguem testes automatizados de aceite nos aparelhos. Existem falhas preexistentes no projeto-base; uma comparação sem novas regressões não significa que todos os testes estão verdes.

A beta.10 mantém o assistente de fontes, acrescenta recuperação de catálogos e inspeção preventiva de extensões e oferece um APK universal ARM. O aceite completo com extensões reais, aparelhos e migração de backups continua pendente.

Veja [como contribuir](CONTRIBUTING.md). Para problemas de armazenamento, informe tamanhos antes/depois. Para tradução, diferencie o texto que o OCR reconheceu do resultado traduzido.

</details>

---

Mantido por **Hailton Reis**. Licença **[Apache 2.0](LICENSE)** · **[Créditos e atribuições](NOTICE)**.
