# Histórico de versões do Polaris

Este arquivo registra a evolução real do código. **Revisões de desenvolvimento não são lançamentos públicos.** As datas abaixo usam America/Fortaleza. O histórico de distribuição fica em [Releases](https://github.com/Hailton-Reis/Polaris/releases).

## Apresentação inicial do repositório — 01/11/2026

- Página inicial em português, identidade visual e navegação.
- Análise crítica de armazenamento e distinção entre medições sintéticas e consumo real.
- Guia inicial, roadmap, modelos de relatos e organização das notas de versão.
- Atualização documental inicial, sem recompilação do aplicativo nem publicação de APK.

## 0.1.0-beta.3 · P20261101.3 — 01/11/2026

**Estado:** candidato compilado ao beta interno; versionCode 104. Sem APK publicado.

- Sobre com descrição do aplicativo, mantenedor, créditos, versão/revisão, projeto, histórico, Releases, licenças e privacidade.
- Atualizador direcionado ao Polaris, incluindo os builds internos, com busca ao abrir e verificação manual.
- Configurações de busca automática e de versões experimentais; experimentais desativadas por padrão, inclusive no beta.
- Seleção por versão SemVer, código, identificador do app, Android e arquitetura, com manifesto de atualização e SHA-256 do APK.
- Rascunhos ignorados; desativar betas não rebaixa a instalação. A consulta não inicia o download do APK.

O repositório permanece privado. A busca pública e a atualização real no celular ainda dependem de Releases acessíveis, artefatos publicados e da assinatura original. Esta revisão não alterou a visibilidade nem publicou pacotes.

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
