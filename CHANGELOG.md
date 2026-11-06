# Histórico de versões do Polaris

Este arquivo registra a evolução real do código. **Revisões de desenvolvimento não são lançamentos públicos.** As datas abaixo usam America/Fortaleza, exceto quando houver indicação de UTC. O histórico de distribuição fica em [Releases](https://github.com/Hailton-Reis/Polaris/releases).

## 0.1.0-beta.10 · P20261106.1 — 06/11/2026

**Estado:** pré-lançamento público para testes; versionCode 111; Android 8+, um APK universal ARM32/ARM64 de 261.130.442 bytes, com a assinatura anterior.

- Recursos comuns compartilhados no APK; Android seleciona as bibliotecas nativas compatíveis na instalação.
- Lista de capítulos principal salva antes da descoberta de alternativas. Recuperação de fontes após restauração, inclusive obras antigas/concluídas, com amostragem de páginas/imagens e preferência por português entre fontes habilitadas e verificadas.
- Tentativas de outra edição confirmada quando a lista de páginas falha; fonte fixa, modo somente baixados e progresso preservados.
- Menor concorrência/cache em processos com memória limitada e diagnóstico de ABI/processo no Sobre.
- Inspeção preventiva, quarentena e aprovação por versão exata; confiança interna não importada de backups. A sandbox completa ainda não está integrada.

738 testes JVM: 721 aprovações e as mesmas 17 falhas preexistentes. 31 casos novos, 13 controles de empacotamento/overlay e seis controles Android isolados passaram. Sem aceite completo em celulares; falha do A12 ainda sem causa confirmada. A exportação de capítulos mesclados para Mihon/Tachiyomi precisa de normalização e teste real: **preserve o backup original**.

[Baixar beta.10](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10) · [Notas e limites](docs/versoes/0.1.0-beta.10.md).

## 0.1.0-beta.9 · P20261104.4 — 05/11/2026 (UTC)

**Estado:** pré-lançamento público para testes; versionCode 110; Android 8+, ARM32 e ARM64. Publicado com aceitação física, assistente completo e migração real em banco ainda pendentes.

- Assistente para revisar repositórios e preparar extensões internas em lote, com escolha por biblioteca/idiomas, progresso, cancelamento e repetição das falhas.
- Verificação criptográfica, identidade/certificado vinculados à seleção e proteção contra troca silenciosa de chave de repositório.
- Correções de cedilha Anime Ace, encaixe, caixas escuras e deduplicação das bordas do OCR por faixas.
- Opções dependentes coerentes de OCR e download de atualização recuperável com SHA-256.
- Formato de backup e identificadores preservados; seis testes de codec e duas leituras independentes passaram. Sem garantia para todos os forks; o campo Mihon `nextUpdate` não é preservado.

707 testes JVM: 690 aprovações e as mesmas 17 falhas preexistentes, sem regressões novas. 16 controles Android de tipografia e quatro de segurança passaram em componentes isolados. Isso não aprova o aplicativo completo em celulares. APKs: 199.132.104 bytes ARM64 e 159.334.281 bytes ARM32, com a assinatura da beta.8.

[Baixar beta.9](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.9) · [Notas, benchmark e limites](docs/versoes/0.1.0-beta.9.md).

## 0.1.0-beta.8 · P20261103.1 — 03/11/2026

**Estado:** pré-lançamento público para testes; versionCode 109; Android 8+, ARM32 e ARM64. Instalação/atualização e consumo em aparelhos físicos continuam pendentes de aceite.

- Uma sequência lógica agrupa Official/Unofficial, preservando progresso e arquivos. Partes, decimais, volumes, temporadas e extras identificados permanecem separados.
- Escolha automática entre catálogos de fontes compatíveis e fonte fixa por obra.
- Retomada, leitor, próximos downloads, atualizações e contagens adotam a mesma identidade de capítulo.
- Cache e traduções separados por edição; escopo do glossário mantido por obra.
- Dedicatória escondida no Sobre e correções de identidade, leitura e OCR acumuladas desde a beta.3.

589 testes JVM: 555 aprovações e as mesmas 34 falhas preexistentes, sem regressões novas. Todos os 42 testes novos passaram. APKs com a mesma assinatura da beta.3 distribuída; acréscimo de 1,60 MiB por APK versus beta.7, sem modelo novo. Descoberta foi testada com provedores simulados; fontes reais e aparelhos permanecem em validação.

[Baixar beta.8](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.8) · [Notas e validação](docs/versoes/0.1.0-beta.8.md).

## Revisões internas beta.5, beta.6 e beta.7 — 02/11/2026

Estas revisões não foram publicadas como Releases. Suas mudanças integram a beta.8:

- **beta.5 / P20261102.2 / código 106:** edição avançada de tradução desligada por padrão e ferramentas de diagnóstico de leitura.
- **beta.6 / P20261102.3 / código 107:** melhorias de retenção de texto reconhecido e OCR por regiões sobrepostas em páginas longas, inicialmente com ML Kit em inglês.
- **beta.7 / P20261102.4 / código 108:** caminho regional compartilhado por ML Kit e Paddle Small em inglês, com controles de geometria e decodificação limitada. O rascunho permaneceu sem APKs publicados.

As comparações do benchmark usaram controles sintéticos; não aprovam a qualidade de todos os capítulos reais. Nenhum modelo Tiny foi adicionado ao aplicativo.

## 0.1.0-beta.4 · P20261102.1 — 02/11/2026 (UTC)

**Estado:** candidato compilado; versionCode 105. Os APKs da beta.4 ainda não foram publicados nas Releases. Conferência visual no A12 pendente.

- Corrige o nome Yomotsu exibido pelo instalador e pelo Android, aplicando **Polaris**.
- Ícone de estrela e livro no instalador, na tela inicial, na abertura e no Sobre, com ícone temático no Android 13+.
- Preserva identificador e assinatura da beta.3 distribuída, permitindo solicitar atualização dessa instalação.
- Acrescenta uma barreira de exportação que verifica o nome e os ícones no APK compilado.

ARM32, ARM64 e x86_64 tiveram a identidade verificada. A comparação Android mantém 491 aprovações e as mesmas 34 falhas preexistentes; os seis testes do empacotador passaram.

[Notas da revisão](docs/versoes/0.1.0-beta.4.md)

## Apresentação inicial do repositório — 01/11/2026

- Página inicial em português, identidade visual e navegação.
- Análise crítica de armazenamento e distinção entre medições sintéticas e consumo real.
- Guia inicial, roadmap, modelos de relatos e organização das notas de versão.
- Atualização documental inicial, sem recompilação do aplicativo nem publicação de APK.

## 0.1.0-beta.3 · P20261101.3 — 01/11/2026

**Estado:** primeiro pré-lançamento publicado em 01/11/2026 e agora aberto ao público; versionCode 104. Aceite nos aparelhos ainda pendente.

- Sobre com descrição do aplicativo, mantenedor, créditos, versão/revisão, projeto, histórico, Releases, licenças e privacidade.
- Atualizador direcionado ao Polaris, incluindo os builds internos, com busca ao abrir e verificação manual.
- Configurações de busca automática e de versões experimentais; experimentais desativadas por padrão, inclusive no beta.
- Seleção por versão SemVer, código, identificador do app, Android e arquitetura, com manifesto de atualização e SHA-256 do APK.
- Rascunhos ignorados; desativar betas não rebaixa a instalação. A consulta não inicia o download do APK.

O repositório e a Release são públicos, com download sem login no GitHub. O título e a descrição foram adaptados para todas as pessoas que desejam experimentar o beta. Os seis anexos publicados mantêm os tamanhos e hashes SHA-256 conferidos com o pacote verificado. A atualização real no celular e a continuidade da assinatura ainda precisam de validação.

[Baixar o primeiro beta](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3).

Os 20 testes novos passaram. A comparação completa registrou 525 testes: 491 aprovações e as mesmas 34 falhas preexistentes, sem novas regressões. Consulta, download e instalação reais ainda não têm aceite nos aparelhos.

[Implementação](https://github.com/Hailton-Reis/Polaris/commit/c54644cf396c816ebeb45bbfa5c619b570984523) · [Como as atualizações funcionam](docs/ATUALIZACOES.md) · [Privacidade e serviços](docs/PRIVACIDADE.md)

## 0.1.0-beta.2 · P20261101.2 — 01/11/2026

**Estado:** candidato compilado ao beta interno; instalação e preparação real dos modelos ainda pendentes nos aparelhos. Sem APK publicado. versionCode 103.

- Preparação automática dos recursos de tradução inglês → português, via mecanismo oficial do ML Kit.
- Espera por rede sem cobrança e condição de espaço do Android; preparação manual disponível com a conexão atual.
- Estado visível em Documentos e pesquisa e nas configurações de tradução, com verificação antes de exibir Pronto.
- Preservação dos idiomas de OCR/saída escolhidos pelo usuário.
- Nova capa ilustrada e página inicial com navegação e apresentação mais claras.

O OCR latino já acompanhava o APK. Os recursos de tradução continuam exigindo conexão inicial; esta versão não os empacota manualmente dentro do APK. Download, agendamento e funcionamento offline ainda precisam de conferência nos aparelhos.

Sete testes novos passaram. A comparação completa terminou com 505 testes: 471 aprovações e as mesmas 34 falhas preexistentes, sem novas regressões. Isso não representa aceite Android.

[Implementação](https://github.com/Hailton-Reis/Polaris/commit/3866531931c7705bd238d83467ce40c497343ba5) · [Como a preparação funciona](docs/INGLES_E_TRADUCAO.md)

## 0.1.0-beta.1 · P20261101.1 — 01/11/2026

**Estado:** candidato compilado ao beta interno; armazenamento total, instalação e qualidade nos aparelhos ainda em avaliação. Sem lançamento publicado nas Releases. versionCode 102.

- Painel de armazenamento com originais, cópias importadas, traduções, caches, dados internos/modelos, APKs e bibliotecas nativas extraídas.
- Meta de 256 MiB para o cache regenerável de documentos, com proteção de arquivos em uso.
- Exclusão do capítulo baixado junto de sua tradução e cache de frases, preservando glossário e correções.
- Roteamento do idioma de OCR pelos metadados conhecidos da fonte; automação global asiática opcional.
- Glossário na tradução textual e proteção de termos CJK sem exigir espaços.
- Fila de tradução mais conservadora para reduzir processamento simultâneo.
- Exportação local de APKs ARM64/ARM32, verificação de assinatura e exemplos originais de idiomas.

**Evidência:** 12 novos testes passaram; comparação total com 498 testes, 464 aprovados e as mesmas 34 falhas preexistentes. Isso não valida a qualidade do OCR nos aparelhos.

[Código desta revisão](https://github.com/Hailton-Reis/Polaris/commit/617aa0b992cc5b5966a6069d6e39eb3ebd50c4e7) · [Notas detalhadas](docs/versoes/0.1.0-beta.1.md)

## P20261031.4 — 31/10/2026

**Estado:** revisão de desenvolvimento compilada; fluxo Android pendente de aceite.

- Organização antes da inclusão de arquivos escolhidos no celular.
- Tipos de conteúdo independentes do formato: mangás, manhwas, quadrinhos, livros, artigos e documentos.
- Categorias existentes, categoria pessoal e agrupamento opcional por formato.
- Cancelamento da seleção antes de copiar o documento para a biblioteca.
- Dez novos testes aprovados, sem novas regressões na comparação registrada.

[Código](https://github.com/Hailton-Reis/Polaris/commit/a6d66d78cc5b0be65a2b113cd15169084d26bcf2)

## P20261031.3 — 31/10/2026

**Estado:** implementação inicial de documentos; validação nativa pendente.

- PDF no leitor de páginas; EPUB/DOCX/TXT em leitura textual por seções.
- Importação local e por link direto, tradução textual e retomada.
- Pesquisa em Crossref, Europe PMC, Gutendex e Open Library.
- Site de pesquisa configurável dentro do aplicativo.
- Dezenove novos testes aprovados, preservando as falhas anteriores do projeto-base.

[Código](https://github.com/Hailton-Reis/Polaris/commit/2b3cc36cf336a5f05aefd8294d44d3204727481d)

## P20261031.2 — 31/10/2026

- Proteção da geometria original nas páginas traduzidas quando o corte de bordas está ativado.
- O mantenedor confirmou que desligar o corte alinhava as traduções salvas na revisão anterior.
- A confirmação do diagnóstico não equivale ao aceite visual da correção automática.

[Código](https://github.com/Hailton-Reis/Polaris/commit/b252b225a32746c1409dbfd084db16982fd1c2fd)

## P20261031.1 — 31/10/2026

- Sincronização do posicionamento da tradução com a imagem paginada.
- Identificação explícita da revisão do Polaris em Sobre.
- O diagnóstico posterior identificou o corte de bordas como causa adicional do desalinhamento.

[Código](https://github.com/Hailton-Reis/Polaris/commit/8a23fa6)

## Revisões de engenharia — 29 e 30/10/2026

- Ação de baixar e traduzir por capítulo, solicitações persistidas e ajuste do encaixe de palavras.
- Ajustes de posicionamento, automação de downloads em inglês e respeito à escolha por obra.
- Catálogo inicial de repositórios e apresentação mais clara dos grupos/versões dos capítulos.

[Código de 29/10](https://github.com/Hailton-Reis/Polaris/commit/87c5ce7) · [Tradução em inglês](https://github.com/Hailton-Reis/Polaris/commit/e8ef402) · [Descoberta e capítulos](https://github.com/Hailton-Reis/Polaris/commit/582e8c4)

## Como registrar as próximas versões

Cada lançamento deve informar versão, revisão, commit, estado de validação, mudanças, limitações e compatibilidade. Os APKs distribuídos devem trazer seus próprios hashes e assinatura verificada. Os hashes de uma compilação local não devem ser tratados como hashes universais de qualquer recompilação.

Não atribuir datas de lançamento ou status de estabilidade a revisões que foram apenas compiladas.
