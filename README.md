<p align="center">
  <img src="docs/assets/polaris-hero.png" alt="Polaris — um livro aberto transforma suas páginas em constelações sob a estrela do norte" width="100%">
</p>

<p align="center">
  <strong>Mangás, livros e documentos. Sua biblioteca, no seu ritmo e no seu idioma.</strong><br>
  Um leitor para Android com tradução, vocabulário consistente e organização por você.
</p>

<p align="center">
  <a href="docs/COMECE_AQUI.md"><strong>Comece aqui →</strong></a> &nbsp; · &nbsp;
  <a href="CHANGELOG.md"><strong>Versões e novidades</strong></a> &nbsp; · &nbsp;
  <a href="docs/ARMAZENAMENTO.md"><strong>Armazenamento</strong></a>
</p>

**Pré-lançamento público atual: [beta.10 / P20261106.1 / código 111](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10).** Um APK universal ARM32/ARM64, recuperação de fontes e inspeção preventiva de extensões. [Publicação, downloads e limites](integration/release-candidates/0.1.0-beta.10/README.md). Na beta.10 publicada, a sandbox e a normalização de capítulos mesclados para outros leitores ainda não estão integradas. A [próxima revisão em desenvolvimento](integration/reading-continuity/20261106/README.md) implementa isolamento optativo experimental e a projeção de backup, com aceite nos aparelhos e em leitores externos ainda pendente; preserve o backup original. Esta branch contém a engenharia; a apresentação atual fica em [main](https://github.com/Hailton-Reis/Polaris).

**Revisão em desenvolvimento P20261110.2:** a [revisão da biblioteca](docs/REVISAO_BIBLIOTECA_P20261110_2.md) revalida a numeração durante a leitura e a gravação da associação, distingue temporadas/volumes/partes e corrige escolhas fora dos favoritos. A [biblioteca unificada](docs/BIBLIOTECA_UNIFICADA_P20261110_1.md), a [busca por obra](docs/BUSCA_UNIFICADA_P20261109_1.md) e a [Jornada Polaris](docs/AUDITORIA_GERAL_P20261107_1.md) continuam em desenvolvimento. A validação com bibliotecas reais, aparelhos e leitores externos está pendente. Essa revisão ainda não é uma nova Release.

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

**Nome e ícone no Android:** os APKs públicos beta.9 usam a identidade Polaris e preservam a assinatura da beta.8. Os APKs históricos da beta.3 continuam com o nome Yomotsu; os arquivos antigos não mudam com a edição da página de Release.

## Inglês como prioridade

**O reconhecimento de texto em inglês já acompanha o APK.** O Polaris usa a biblioteca latina embarcada do ML Kit para ler o texto das imagens.

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

**O repositório e o [primeiro beta público](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3) estão disponíveis**, com APKs ARM64 e ARM32 para baixar pelo navegador, sem login no GitHub. A atualização real no aparelho ainda precisa de validação. [Canais, compatibilidade e publicação →](docs/ATUALIZACOES.md)

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

O beta público disponível é **`0.1.0-beta.10` · revisão `P20261106.1` · versionCode `111`**. [Notas e registro de publicação](integration/release-candidates/0.1.0-beta.10/README.md). A revisão `P20261110.2` (beta.11 em desenvolvimento, sem publicação) acrescenta a biblioteca unificada à busca por obra, continuidade entre fontes, isolamento experimental e personalização. [Escopo e limites](docs/BIBLIOTECA_UNIFICADA_P20261110_1.md). A implementação está em avaliação na [branch de engenharia](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation).

**O [primeiro beta público](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3) está disponível; ainda não há lançamento estável.** O pacote de teste e a compilação não equivalem a aprovação do consumo, da compatibilidade ou da qualidade em todos os idiomas.

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

[Registros de compilação e testes](https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/integration/internal-beta/TEST_RESULTS.json) distinguem testes automatizados de aceite nos aparelhos. Os resultados históricos incluem falhas do projeto-base, corrigidas na auditoria P20261107.1. A revisão atual tem seu próprio registro de testes; isso não substitui o aceite nos aparelhos.

Seleção inteligente entre fontes, correlação de obras e progresso canônico permanecem como objetivos sujeitos à sua própria validação. O aceite completo com duas fontes continua pendente.

Veja [como contribuir](CONTRIBUTING.md). Para problemas de armazenamento, informe tamanhos antes/depois. Para tradução, diferencie o texto que o OCR reconheceu do resultado traduzido.

</details>

---

Mantido por **Hailton Reis**. Licença **[Apache 2.0](LICENSE)** · **[Créditos e atribuições](NOTICE)**.
