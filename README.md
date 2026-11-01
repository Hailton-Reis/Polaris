<p align="center">
  <img src="docs/assets/polaris-header.svg" alt="Polaris — leitura, tradução e organização" width="100%">
</p>

<p align="center">
  <strong>Um leitor Android para reunir mangás, livros e documentos, com tradução e uma biblioteca organizada por você.</strong>
</p>

<p align="center">
  <img alt="Android 8 ou superior" src="https://img.shields.io/badge/Android-8%2B-3ddc84?logo=android&amp;logoColor=white">
  <img alt="ARM64 e ARM32" src="https://img.shields.io/badge/Arquiteturas-ARM64%20%7C%20ARM32-6173b7">
  <img alt="Candidato ao beta interno" src="https://img.shields.io/badge/Status-candidato%20ao%20beta-a78bfa">
  <a href="LICENSE"><img alt="Licença Apache 2.0" src="https://img.shields.io/badge/Licen%C3%A7a-Apache%202.0-586276"></a>
</p>

<p align="center">
  <a href="#estado-atual">Estado atual</a> ·
  <a href="docs/COMECE_AQUI.md">Comece aqui</a> ·
  <a href="CHANGELOG.md">Histórico</a> ·
  <a href="docs/ARMAZENAMENTO.md">Armazenamento</a> ·
  <a href="docs/ROADMAP.md">Próximos passos</a> ·
  <a href="https://github.com/Hailton-Reis/Polaris/releases">Releases</a>
</p>

## O que é o Polaris?

O Polaris é um projeto de leitura para Android voltado a quem acompanha quadrinhos, lê livros em outros idiomas ou consulta documentos e artigos. Reúne leitura, tradução para português e organização da biblioteca, com funcionamento no próprio aparelho e provedores externos opcionais.

Você escolhe o que incluir na biblioteca. Um PDF pode ser um livro, um artigo ou um quadrinho; o formato do arquivo não determina sua classificação. A proposta é manter a leitura simples, o vocabulário consistente e o consumo de armazenamento visível.

## Estado atual

**Candidato compilado: `0.1.0-beta.1` · revisão `P20261101.1` · versionCode `102`.**

O projeto está em avaliação para um beta interno. **Ainda não há lançamento estável ou APK publicado nas Releases.** A geração do pacote não significa aprovação do consumo de armazenamento nem validação nos celulares.

| Área | Evidência atual |
| --- | --- |
| Inglês → português | Resultado favorável confirmado pelo mantenedor em candidato anterior |
| Compilação e testes | 498 testes registrados: 464 passaram e 34 falhas preexistentes permaneceram; nenhuma nova regressão detectada nessa comparação |
| Armazenamento | Medição sintética de JSON e controles implementados; consumo total e picos nos aparelhos ainda pendentes |
| Japonês, chinês e coreano | Exemplos e testes de texto preparados; qualidade do OCR e da tradução nas imagens ainda pendente |
| A12, S20 FE, S8+ e provável A52 | Matriz inicial de teste; instalação, Android/ABI, memória e desempenho ainda pendentes |
| Seleção automática entre fontes | Objetivo de engenharia; aceite completo com duas fontes ainda pendente |

A revisão crítica de armazenamento vem antes da recomendação de distribuição. Consulte os [pontos encontrados e critérios de verificação](docs/ARMAZENAMENTO.md#revisao-critica).

## Recursos do candidato

### Ler

- Quadrinhos nos formatos compactados já suportados pela base do projeto.
- **PDF** no leitor de páginas, com imagens e tradução por OCR.
- **EPUB** textual, seguindo a ordem das seções e preservando imagens locais compatíveis.
- **DOCX e TXT** em leitura por seções, com ajuste de fonte e retomada de posição.
- Leitura paginada e em faixa longa para conteúdo em imagens.

EPUB e DOCX usam texto refluído. Paginação do Word, tabelas complexas, fórmulas e estilos não são reproduzidos integralmente. PDF é renderizado como imagem; a tradução atual usa OCR.

### Traduzir e conservar vocabulário

- Tradução com **ML Kit no aparelho**, após baixar os modelos necessários.
- Provedores externos opcionais, conforme configuração de cada pessoa.
- Ação de baixar e traduzir capítulos e configuração automática por obra.
- Glossário por obra, nomes protegidos e correções aprendidas.
- Consulta do glossário também na tradução textual de documentos.
- Exclusão conjunta do capítulo baixado e de sua tradução pelo fluxo do app, preservando o vocabulário.

Fontes que declaram inglês, japonês, chinês ou coreano podem orientar a entrada do OCR. Fontes mistas, desconhecidas e documentos locais usam a entrada escolhida manualmente. Isso não detecta o idioma pela imagem. A automação global dos idiomas asiáticos começa desativada neste candidato; a escolha explícita por obra tem prioridade. PaddleOCR permanece apenas em inglês.

### Incluir e organizar

```text
Explorar o celular → escolher um arquivo → organizar → adicionar à biblioteca
```

- Inclusão manual pelo seletor Android, sem varrer todos os PDFs do aparelho.
- Tipos como mangás, manhwas, quadrinhos, livros, artigos e documentos.
- Agrupamento opcional por formato: PDF, EPUB, DOCX, TXT e outros suportados.
- Reutilização das categorias existentes e criação de categorias pessoais.
- Cópia gerenciada do arquivo selecionado, mantendo o original onde estava.

Cancelar a tela de organização não inclui o documento. Reimportar o mesmo conteúdo ainda pode criar outra cópia; a deduplicação está entre os pontos da revisão de armazenamento.

### Encontrar livros e artigos

| Pesquisa | Fontes iniciais |
| --- | --- |
| Artigos por título, autor ou DOI | Crossref e Europe PMC |
| Livros por título ou autor | Gutendex e Open Library |
| Outras pesquisas | Site configurável aberto dentro do app |
| Arquivo já encontrado | Importação por link direto compatível |

Cada resultado informa sua origem. A busca não cobre toda a internet e um registro bibliográfico não garante acesso ao texto completo. Fontes e extensões de terceiros mantêm seus próprios requisitos de acesso e disponibilidade.

## Armazenamento: parte central do projeto

O custo total envolve **instalação + modelos + originais + traduções + caches**. O JSON de tradução é apenas uma dessas parcelas.

| Parcela | Referência disponível |
| --- | --- |
| APK ARM64 | 201,4 MB no pacote compilado; não representa todo o tamanho instalado |
| APK ARM32 | 161,6 MB no pacote compilado; não representa todo o tamanho instalado |
| Modelos de tradução ML Kit | Cerca de 30 MB por idioma, segundo o Google; reutilizados entre capítulos |
| JSON de tradução | 48–53 kB em exemplo sintético de 20 páginas/200 blocos; não é uma taxa por capítulo real |
| Cache regenerável de documentos | Meta de 256 MiB; arquivos em uso podem ultrapassá-la temporariamente |
| Livros e quadrinhos | Originais, cópias importadas e temporários variam conforme os arquivos escolhidos |

**256 MiB não é um limite total do Polaris.** Importar um arquivo e prepará-lo para leitura pode manter mais de uma cópia. Ainda precisamos medir os picos e o comportamento com pouco espaço livre nos aparelhos.

O candidato acrescenta o painel **Dados e armazenamento → Armazenamento do Polaris** e uma limpeza do cache regenerável. O glossário fica separado dessa limpeza. Veja a [análise crítica completa](docs/ARMAZENAMENTO.md), incluindo duplicação, temporários, limites de medição e próximos ajustes.

## Requisitos e funcionamento offline

- Android **8.0 / API 26 ou superior**.
- APK correspondente ao sistema **ARM64** ou **ARM32** do aparelho.
- Espaço livre para instalação, modelos, documentos e preparação da leitura.
- Conexão para buscas, fontes, downloads e instalação inicial de modelos.

Arquivos locais e capítulos baixados podem ser lidos offline. ML Kit pode traduzir no aparelho depois de instalar os modelos correspondentes. Provedores de API continuam exigindo conexão e podem enviar texto/contexto ao serviço escolhido. Não é necessário manter um servidor pessoal.

O modelo comercial do celular, sozinho, não garante compatibilidade. A matriz física ainda precisa ser executada, especialmente nos aparelhos mais modestos.

## Versões, instalação e atualizações

O [histórico de desenvolvimento](CHANGELOG.md) registra as revisões e seu nível de validação. As [Releases](https://github.com/Hailton-Reis/Polaris/releases) serão o local de distribuição quando houver um pacote aprovado para esse fim; um rascunho não equivale a lançamento publicado.

O fluxo atual de engenharia gera APKs e exemplos localmente. Atualizações que preservem os dados devem usar a mesma assinatura da instalação anterior. Não existe atualizador automático do Polaris via Releases habilitado por esta apresentação.

Leia o [guia inicial](docs/COMECE_AQUI.md). A versão candidata e suas evidências estão na [branch de engenharia](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation).

## Próximos passos

1. Concluir a revisão de armazenamento e medir instalação, leitura, tradução, exclusão e novo download nos aparelhos.
2. Priorizar os ajustes de cópias, espaço insuficiente e repetição de importação encontrados nessa revisão.
3. Validar inglês e os idiomas asiáticos, incluindo japonês vertical, com páginas reais autorizadas.
4. Conferir importação, categorias, retomada e estabilidade antes de ampliar o beta.
5. Evoluir o trabalho de múltiplas fontes com as verificações próprias dessa camada.

O [roadmap](docs/ROADMAP.md) distingue o que já está no código do que ainda precisa ser comprovado.

## Relatar um problema

Abra um [relato de problema](https://github.com/Hailton-Reis/Polaris/issues/new/choose) com revisão em **Sobre**, aparelho, Android, passos e resultado observado. Para armazenamento, registre os números antes e depois da ação. Os exemplos originais do projeto ajudam a reproduzir falhas sem compartilhar documentos pessoais.

## Desenvolvimento e origem

A base Android utiliza o ecossistema **Yomotsu / Mihon**, com conceitos de múltiplas fontes vindos do **TachiyomiSY**. O desenvolvimento atual mantém o upstream fixado e aplica camadas de integração revisáveis. A branch `main` apresenta o projeto; a implementação em avaliação está em `r001/multisource-foundation`.

Seleção inteligente de fontes, correlação de obras e progresso canônico continuam como objetivos sujeitos aos testes de engenharia. Consulte [como contribuir](CONTRIBUTING.md) antes de enviar alterações.

## Licença e créditos

O repositório mantém a licença [Apache 2.0](LICENSE) e os créditos em [NOTICE](NOTICE). Bibliotecas, modelos e materiais de terceiros podem ter condições próprias. As atribuições da base são preservadas.

---

Projeto mantido por **Hailton Reis**.
