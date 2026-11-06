# Candidata beta.10 — universal ARM e recuperação de fontes

**Publicado posteriormente como beta.10 em 06/11/2026.** O texto abaixo conserva o contexto de preparação; [publicação e limites atuais](../integration/release-candidates/0.1.0-beta.10/README.md).

**P20261106.1 / código 111 / Android 8+; ainda sem publicação.** A versão pública continua sendo a beta.9. Os resultados de compilação e testes desta candidata serão registrados separadamente; a lista abaixo descreve implementação e limites, não aceite em celulares.

## Um APK para ARM32 e ARM64

O APK universal inclui o código e os recursos comuns uma vez, com bibliotecas nativas próprias para ARM32 e ARM64. O Android escolhe as bibliotecas compatíveis durante a instalação, antes de o aplicativo executar. Não é necessário o app abrir primeiro, identificar o aparelho e instalar outro APK. Um processador de 64 bits pode ter Android de 32 bits; vale a compatibilidade informada pelo sistema.

O pacote completo continua no aparelho; ele não vira automaticamente um download pequeno para cada arquitetura. A escolha de bibliotecas evita carregar as duas arquiteturas ao mesmo tempo, mas o tamanho instalado e o temporário do instalador precisam de medição. Não foi implementado um instalador que baixa uma segunda versão.

A medição dos APKs públicos beta.9 encontrou 85.421.577 bytes comprimidos idênticos e 260.414.901 bytes de conteúdo comprimido único combinado. É uma estimativa, excluindo empacotamento e assinatura. O tamanho real da candidata deve ser usado quando o APK estiver pronto. O pacote para celulares exclui x86/x86_64, usados em emuladores.

O manifesto conserva dois descritores de ABI apontando para **o mesmo arquivo, tamanho e SHA-256**. Assim, atualizadores antigos podem escolher sua arquitetura e baixar um único APK. Isso não cria dois arquivos de instalação nem dois downloads.

Para compilar o pacote de celular, use `:app:assembleDebug -Ppolaris.universalArm=true`. O fluxo de desenvolvimento preserva primeiro os APKs de emulador e depois faz esse empacotamento específico antes de exportar o beta. Sem a propriedade, os splits originais de desenvolvimento continuam disponíveis. O exportador recusa um universal que inclua por engano bibliotecas x86 ou que não contenha as dependências de leitura/OCR nas duas arquiteturas ARM.

## Capítulos primeiro; alternativas depois

O caminho anterior podia esperar até a descoberta de fontes alternativas terminar antes de salvar os capítulos já retornados pela fonte original. A candidata salva a resposta principal primeiro e faz a descoberta adicional sem manter a lista vazia por esse motivo. Isso é uma correção de caminho identificado no código; não confirma a causa da falha relatada no A12, onde obras da MangaDex apareciam mas os capítulos não carregavam.

A recuperação permite procurar uma substituição quando o backup não tem mais a fonte original nem alternativas guardadas. Usa apenas fontes carregadas, habilitadas e dos idiomas selecionados. Título, autoria e numeração continuam conferidos; título parecido sozinho não confirma a identidade. Obras sem autoria ou com títulos traduzidos não corroborados podem continuar exigindo escolha manual. Fontes ocultas ou não autorizadas não são instaladas/ativadas por essa busca.

Durante uma descoberta, há amostragem de lista de páginas e de bytes de imagem de capítulos das extremidades do catálogo, com limites. As escolhas mostram se a amostra abriu, falhou ou não foi verificada. Fontes com amostra aprovada têm prioridade; entre elas, português brasileiro e português precedem outros idiomas, depois entram continuidade/cobertura. **A amostragem não testa todos os capítulos**, nem mede a qualidade editorial da tradução. Uma fonte fixada pela pessoa é respeitada. Se o backup habilitava somente inglês nos filtros de fontes, habilite também português/português brasileiro para incluí-los na descoberta; a preparação de extensões não substitui essa preferência global silenciosamente.

Depois da restauração de biblioteca, o trabalho de recuperação usa a fila de atualização com conexão disponível, progresso e cancelamento. Ele percorre também obras antigas/concluídas, sem baixar capítulos inteiros automaticamente. Se faltarem extensões, a conclusão de um lote autorizado de preparação pode solicitar novamente a recuperação pendente. Isso não concede confiança aos repositórios do backup nem acrescenta APKs ao arquivo de backup.

Repositórios restaurados com identidade nova precisam de revisão local para autorizar código. Os campos de URL/certificado continuam portáveis; o guia permite escolher e confirmar o lote depois de importar, sem uma instalação Android por extensão. Preferências internas de confiança e exceções não são aceitas mesmo quando um backup as inclui manualmente.

Se a lista de páginas de um capítulo falhar no leitor, a candidata pode tentar até três edições já corroboradas do mesmo capítulo. Não muda a numeração ou a fonte fixada, respeita o modo somente baixados e não confunde cancelamento com falha de provedor. A página exata de outra edição não é presumida equivalente: o progresso anterior fica preservado na edição original. Falhas que só aparecem em uma imagem posterior ainda precisam de recuperação adicional; não são declaradas resolvidas por essa reserva.

## Menos concorrência nos aparelhos limitados

O perfil usa o processo real de 32/64 bits, a indicação de pouca RAM do Android e a classe de memória; não o nome comercial do aparelho. Processos de 32 bits, aparelhos de pouca RAM ou heap pequeno usam dois carregamentos de imagem, um decodificador, limite menor de cache e duas threads no PaddleOCR. Aparelhos maiores mantêm o perfil mais concorrente. O ML Kit, idiomas e recursos disponíveis não são substituídos por essa escolha.

Esses limites reduzem trabalho simultâneo e pressão de memória; não comprovam melhora de tempo ou fluidez no A12. A abertura, leitura e tradução precisam de medição nos aparelhos.

## Segurança

A candidata acrescenta inspeção preventiva e quarentena antes do carregamento da extensão, com exceção vinculada aos bytes exatos e aviso de compatibilidade sem isolamento. **O executor de sandbox real ainda não está integrado.** Veja [o desenho, a decisão do mantenedor e os critérios de aceite](ISOLAMENTO_DE_EXTENSOES.md). Assinatura válida e ausência de achados não garantem código seguro.

Há também proteção de caminhos e HTTPS para plugins de novels, cujo runtime é diferente. A prova Android de separação de UID/permissões passou em seis controles independentes; ela não executa extensões reais. A revisão mantém explícita essa diferença.

## Primeiro teste quando o pacote estiver validado

1. Guarde o backup original. Instale o único APK universal sobre o Polaris, usando a assinatura distribuída. Não desinstale para contornar conflito de assinatura.
2. Em Sobre, confira beta.10 / P20261106.1 e Compatibilidade do aparelho. Toque na versão para copiar os dados de Android, ABIs e processo junto da revisão.
3. Teste uma fonte atualizada, uma obra nova e uma obra antiga restaurada. Compare a primeira lista, a conclusão da descoberta e as indicações de amostra das fontes.
4. Confira fonte fixa, português/inglês, capítulos sem páginas, progresso e arquivos já baixados. Não sobrescreva o backup original durante os testes de migração.
5. Revise os motivos das extensões em quarentena. Mantenha desativada ou exclua o que não desejar autorizar. O rótulo de compatibilidade informa que essa execução ainda acontece fora de sandbox.

O formato ProtoBuf e os identificadores originais da biblioteca não foram substituídos. A compatibilidade universal com todos os forks e a ida/volta por banco/UI do Mihon continuam sem aceite; a limitação previamente documentada de `nextUpdate` permanece.

## Pacote e verificação finais

Um APK: **261.1MB / 249.0MiB**; SHA-256 `f1a556d2620a5984c76cebe2dc5a10e461d8d5a2feb6a91018371beaec0a90da`. A redução diante da soma dos dois APKs beta.9 é de 97.3MB. Foram executados 738 testes JVM, com 721 aprovações e as mesmas 17 falhas preexistentes, e seis controles Android de isolamento em componente independente. [Registro e pendências](../integration/universal-recovery/20261106/README.md).

A exportação de capítulos mesclados para leitores externos ainda precisa de normalização e teste: os codecs leem o arquivo, mas isso não confirma a leitura de URLs alternativas específicas do Polaris no Mihon. Mantenha o backup original.
