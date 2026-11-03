# Sequência de capítulos, fontes por obra e dedicatória

**0.1.0-beta.8 / versionCode 109 / P20261103.1**. Em 3 de novembro de 2026, o mantenedor autorizou preparar e publicar esta versão como pré-lançamento público. A publicação não representa aceite dos aparelhos físicos nem versão estável. As betas intermediárias continuam identificadas como revisões internas.

## Comportamento

- Capítulo 0 Official e capítulo 0 Unofficial representam uma única posição na sequência. A mesma política atende lista, início/retomada, leitor, próximos downloads e contagens da biblioteca. Filtros de leitura são aplicados depois do agrupamento.
- Capítulos decimais, partes, volumes, temporadas e extras identificados permanecem separados. Entradas sem número confiável usam sua URL; o antigo valor desconhecido `-1` não reúne avisos e galerias em um único capítulo.
- A edição atual, o progresso parcial e downloads existentes têm preferência. Entre edições disponíveis, a seleção usa continuidade do catálogo e cobertura de capítulos. O rótulo Official só desempata; não comprova qualidade visual ou de tradução.
- Ler ou marcar/desmarcar um capítulo aplica o estado ao grupo correspondente. Excluir um download pela lista remove todas as suas edições armazenadas e suas traduções; glossário e correções aprendidas permanecem conforme a política já existente.
- **Opções de capítulos → Fontes desta obra** oferece Automático ou uma fonte fixa para aquela obra. A preferência é portátil e incluída no memo já suportado pelo backup. Trocar a escolha preserva registros, arquivos e histórico.

## Busca automática

Somente extensões HTTP instaladas, habilitadas e do mesmo idioma participam. Documentos locais, fontes virtuais e leitores de novels não entram na descoberta. Nenhuma extensão é instalada automaticamente.

A associação exige título normalizado exato e autor/artista em comum. Sem autoria suficiente, a correspondência fica ambígua e a fonte atual permanece. Também se exige numeração compatível e sobreposição de capítulos: não se mistura automaticamente uma edição dividida em partes ou com temporadas explícitas com uma sequência que omite essas informações.

A descoberta ocorre no primeiro refresh em primeiro plano, em “Buscar fontes” ou após mudança das extensões habilitadas; há cache de 24 horas. Atualizações da biblioteca consultam somente fontes já vinculadas. Três consultas podem ocorrer em paralelo, cada operação tem prazo limitado, e a descoberta encerra em até 60 segundos, preservando resultados concluídos. Até quatro catálogos ficam ativos; a fonte original é preservada como alternativa. Cada catálogo aceita até 20 mil entradas na comparação automática. Falhas isoladas não apagam os capítulos anteriores. Cancelamento do usuário/tarefa é propagado.

“Melhor fonte” aqui significa **continuidade, disponibilidade e cobertura do catálogo**. Não é uma medição automática da qualidade artística, da resolução das imagens ou do texto de uma scan. Numerações incompatíveis não são corrigidas por suposição.

## Armazenamento e compatibilidade

A obra mantém o mesmo ID, categorias, título e escopo de glossário. Não são criados favoritos adicionais, pais virtuais ou uma migração de banco. Edições alternativas recebem uma identidade de armazenamento que inclui a fonte; a rede recebe a URL real daquela extensão. Assim, arquivos de diferentes provedores não compartilham cache ou tradução por acidente. Arquivos e traduções da fonte original mantêm seus nomes anteriores.

A descoberta baixa **metadados de catálogos**, não as imagens dos capítulos. O download automático recebe apenas novos capítulos lógicos, sem baixar novamente uma edição alternativa de um capítulo já conhecido. A leitura antecipada segue a sequência exibida no leitor. Nenhum modelo OCR, de tradução ou de IA novo foi incluído. A compilação final cresceu **1.676.188 bytes por APK (1,60 MiB)**: ARM64 tem 194.508.943 bytes e ARM32 tem 154.711.120 bytes. Os 78 arquivos de assets/bibliotecas nativas comparados em ARM64 e os 77 em ARM32 são idênticos aos da beta.7.

Edições já vistas permanecem no banco para preservar histórico e downloads. O limite de quatro catálogos ativos e o cache de descoberta de 24 horas **não são uma quota de tamanho do banco**. Em um cenário artificial de mil capítulos nas mesmas quatro fontes, o JSON de origem e o acréscimo das URLs somam aproximadamente 0,85 MiB. Isso exclui os demais campos das novas edições, páginas e índices SQLite, WAL, imagens, traduções e metadados específicos da extensão. É uma estimativa de payload, não uma medição de instalação ou do banco no celular. Os parâmetros e cenários estão em [source-storage-estimate_P20261103_1.json](../integration/document-reader/source-storage-estimate_P20261103_1.json).

Contagens lógicas são recalculadas nas alterações do repositório de capítulos e armazenadas junto à obra. Snapshots incompatíveis com o total de linhas retornam às contagens do banco. A atualização de uma obra antiga preenche essas contagens sem apagar suas edições.

O suporte mínimo continua Android 8/API 26 e os pacotes ARM32 e ARM64 continuam separados.

## Dedicatória

O Sobre contém uma dedicatória local a Deus, “minha esposa” e “minha irmã”. O gesto é local, não gera telemetria nem altera a leitura. O teste cobre acionamento deliberado, intervalo entre toques e reinício do relógio. O gesto exato não é divulgado nas notas públicas para preservar o easter egg.

## Validação e limites

A comparação final executou **589 testes JVM: 555 aprovações e as mesmas 34 falhas da base**. Os 42 testes adicionados nesta revisão passaram. Os APKs foram compilados, a assinatura coincide com a beta.3 distribuída e os 153 arquivos da sobreposição conferidos são idênticos aos usados na árvore de compilação. Os quatro testes de aplicação da sobreposição e os seis testes do empacotador passaram.

A implementação inclui testes de identidade de capítulos, numeração, continuidade da retomada, estado agregado, preferência por downloads, origem portátil, separação dos arquivos de tradução e descoberta com provedores simulados. A simulação não mede disponibilidade real de sites nem substitui testes do leitor completo em ARM.

O relatório final é registrado em `integration/document-reader/TEST_RESULTS.json`. As 34 falhas já presentes na base precisam continuar explicitadas; ausência de regressões não significa uma suíte totalmente verde. A aceitação em aparelhos físicos, a qualidade de scans reais e a interface da troca de fonte ainda exigem teste no app. Nenhuma dessas etapas é declarada concluída somente por compilação ou testes JVM.


A verificação automática confirma a disponibilidade dos catálogos; não comprova que todas as páginas de um site estão acessíveis. O leitor conserva a edição escolhida durante o capítulo, sem substituir imagens e coordenadas de tradução no meio da leitura. Se a fonte original for desinstalada, o caminho de downloads ainda precisa de validação específica: manter a extensão original instalada é a configuração prevista neste candidato. Esses cenários constam da revisão antes de publicação, junto com o teste entre duas extensões reais.
