# Próximos passos do Polaris

O roadmap indica prioridades e critérios de verificação. Não representa prazo de entrega nem recurso já aprovado.

## Estado da auditoria P20261107.1

A [auditoria geral](AUDITORIA_GERAL_P20261107_1.md) separa implementação, prova por componentes e aceite externo. A Jornada Polaris, títulos decorativos, três ícones alternativos e três temas estão implementados na revisão de desenvolvimento. A beta.10 publicada não muda com esta revisão.

Antes de ampliar a distribuição, priorizar:

- Medir abertura de capítulos, memória, armazenamento e processamento no A12/ARM32 e no S20FE/ARM64.
- Validar restauração e continuidade com fontes reais e ida/volta por banco/interface de leitores externos.
- Consolidar entradas antigas separadas da biblioteca, preservando progresso/categorias/downloads e backups. A [busca unificada P20261109.1](BUSCA_UNIFICADA_P20261109_1.md) já reúne resultados corroborados e abre uma favorita existente; isso não consolida os registros antigos.
- Ampliar a sandbox HTTP experimental, adaptar preferências/login/filtros e tratar novels explicitamente.
- Consolidar distribuição não depurável, preservando ID, assinatura e instalação por cima; validar callbacks dos rastreadores em navegador real.

## Prioridade atual: armazenamento antes da ampliação do beta

- Medir instalação completa, modelos, cópias, renderização e temporários nos aparelhos.
- Verificar espaço insuficiente no volume do cache e no volume da biblioteca.
- Avaliar reaproveitamento de materialização, importação repetida e recuperação de inclusão incompleta.
- Conferir a meta de cache com arquivos em uso e o crescimento dos caches fora dessa meta.
- Validar a limpeza conjunta de download/tradução mantendo o vocabulário.

A [análise crítica](ARMAZENAMENTO.md) explica o que motivou cada prioridade e qual evidência falta.

## Rodada interna de leitura e tradução

- Instalação/atualização nos sistemas ARM64/ARM32 correspondentes.
- Biblioteca e documentos: seleção manual, categorias, figuras, retomada e título.
- Paginado/faixa longa: alinhamento da tradução, corte de bordas e zoom.
- Inglês, japonês horizontal/vertical, chinês simplificado/tradicional e coreano.
- Glossário e correções antes/depois de exclusão e novo download.
- Memória, processamento e comportamento em segundo plano nos aparelhos mais modestos.

Os exemplos preparados ajudam a começar. Páginas reais autorizadas e revisão do idioma de origem continuam necessárias para avaliar a qualidade.

## Distribuição e versões

- Manter candidato, beta e estável claramente identificados no histórico.
- Registrar versão, revisão, commit, assinatura, hashes e limitações de cada pacote distribuído.
- Manter notas de versão e instruções de atualização coerentes com os APKs efetivamente disponibilizados.
- Publicar uma Release somente com o estado de validação correspondente; um rascunho permanece rascunho.

## Evolução do leitor

- Melhorias de fidelidade de EPUB/DOCX, navegação e tratamento de documentos complexos.
- Gerenciamento mais claro de modelos e dados regeneráveis.
- Medição e possível redução do pacote de instalação.
- Melhor acessibilidade e desempenho conforme resultados da rodada física.

## Múltiplas fontes

O objetivo é associar variantes de uma mesma obra, preservar a identidade do capítulo e selecionar fontes apropriadas. O aceite completo com duas fontes, a ponte de tradução canônica e a evolução de backup seguem os critérios próprios da engenharia. Não são declarados concluídos por esta página ou pelo pacote de leitura local.

Um servidor pessoal continua opcional; o projeto não deve depender dele para a leitura básica.
