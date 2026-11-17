# Leitura de backups — P20261116.3

Revisão de desenvolvimento após a beta.11 pública, em 16/11/2026. Sem novo APK ou Release. O código de desenvolvimento ainda identifica beta.11/112; uma próxima distribuição exige nova versão e código maior que 112.

## Comportamento

O decoder anterior acumulava todo o conteúdo raw/gzip antes do Protobuf e não recebia cancelamento durante a leitura. A validação inicial da tela de restauração também executava essa operação na interface.

A leitura passa a contar os bytes **depois da descompressão**, com orçamento de **1/8 do heap máximo configurado da VM, limitado a 64 MiB**. Não usa o tamanho comprimido nem a RAM disponível naquele instante. Exemplos: heap de 64 MiB permite 8 MiB de payload; 256 MiB permite 32 MiB; 512 MiB ou mais permite 64 MiB. É uma política conservadora de entrada, sujeita a revisão após medições em aparelhos. Backups legítimos maiores podem ser recusados neste dispositivo.

O leitor usa blocos de até 64 KiB e rejeita excesso antes de acrescentá-lo ao acumulador. Uma leitura sentinela no limite exato exige também o fechamento gzip: CRC inválido, trailer truncado e bytes adicionais continuam recusados. Os streams são fechados em sucesso, falha e cancelamento. O documento selecionado não é alterado.

Cancelamento é conferido entre leituras e antes/depois do parse. A restauração reconfere o chamador antes de começar a aplicar os dados. Essas verificações não interrompem uma chamada bloqueante do provedor nem o parser no meio da execução.

A tela valida em `Dispatchers.IO`, mostra o estado de carregamento e mantém restaurar desabilitado até terminar. O ViewModel também recusa o início prematuro. Cancelamento não vira erro de backup; excesso apresenta uma orientação própria em português/inglês, sem classificar o arquivo como inválido.

## Criação e cópias existentes

Backups **automáticos** conferem o mesmo orçamento após serializar o snapshot, antes de resolver/criar o destino, alterar a data ou podar a retenção. Se o conteúdo exceder o limite, a cópia nova não substitui as anteriores. A verificação de retenção também usa leitura limitada e cancelável; arquivos antigos ilegíveis ou grandes permanecem preservados.

A exportação **manual** continua disponível acima desse orçamento para manter a portabilidade. Um arquivo assim pode exigir um aparelho com orçamento maior ou uma nova exportação com menos campos opcionais para ser restaurado. Essa assimetria é intencional; o controle não bloqueia todas as exportações.

O limite não garante ausência de OOM: cópia para byte array, grafo Protobuf, outras operações concorrentes e dados já carregados continuam consumindo heap. Na criação, o snapshot e a serialização acontecem antes da conferência e seus picos não foram limitados por esta revisão. Não houve medição de RAM em aparelho.

## Validação

Três falhas anteriores reproduzidas: raw acima do limite, gzip pequeno que expande além do limite e cancelamento durante leitura. A reprodução acrescentou apenas parâmetros opcionais inicialmente ignorados para expressar o contrato, mantendo o corpo anterior do decoder. Foram usados payloads sintéticos e limites pequenos; não se provocou OOM.

Após a correção, 38 controles focados aprovados. São 21 casos novos: 15 do decoder/orçamento, quatro do ViewModel e dois de criação automática/manual. Cobrem limite exato, CRC/trailer, fechamento, entradas inválidas, cancelamento, validação fora da Main, bloqueio inicial, mensagem específica e preservação de quatro cópias anteriores/data. Os seis controles de interoperabilidade com arquivos sintéticos Mihon/Tachiyomi também passaram. O ViewModel usa validador controlado e Main dedicada; o decoder real é exercitado separadamente.

Compilação/validação final `BUILD SUCCESSFUL` em 2min53s: **932 testes do app beta executados/aprovados**, mais **85 de domain release já aprovados e UP-TO-DATE**. Total de 1.017 casos nos relatórios, sem falhas/skips ou casos anteriores ausentes contra a base de 996. Quatro testes de overlay, 27 de empacotamento e 21 do comparador aprovados. Não houve nova instrumentação Android, instalação ou pacote nesta revisão; interface/SAF e fluxo real permanecem para validação em aparelho.

## Candidata do OpenCV: pesquisa, sem integração

O pin efetivamente consumido continua `com.quickbirdstudios:opencv:4.5.3.0` em `ppocr-sdk/build.gradle.kts`. Foi inspecionado o AAR oficial `org.opencv:opencv:4.12.0` do Maven Central, com SHA-1 do repositório conferido e SHA-256 registrado. Seu minSdk é 21, compatível com a base API 26 do app; contém ARM32/ARM64 e x86/x86_64. Os oito ELF têm máquina/classe coerentes com o caminho; os dois ARM64 têm PT_LOAD de pelo menos 16 KiB.

A análise do JAR realmente compilado do OCR SDK encontrou 59 referências distintas em 52 classes. Todos os membros públicos referidos têm o mesmo nome/descritor e caráter estático na candidata. O verificador também recusa um consumidor sem referências OpenCV. Isso não certifica toda a ABI Java, valores de constantes, JNI ou resultado da inferência.

Comparando somente OpenCV e C++ nas duas ABIs ARM: 38.039.892 bytes na beta.11 e 41.253.056 na candidata, **acréscimo bruto de 3.213.164 bytes**. Não é uma medição de APK final. O alinhamento ZIP do AAR intermediário não determina o alinhamento do APK.

Nenhuma dependência foi alterada. Ainda faltam integração/compilação, escolha do runtime C++ mesclado, inspeção do APK final e execução OCR em ARM32/ARM64 e sistema de páginas de 16 KiB antes de adotar a candidata. A inspeção não certifica todas as condições de RELRO/carregamento. [Orientação Android](https://developer.android.com/guide/practices/page-sizes).

As [evidências filtradas](../integration/backup-read-budget/20261116/README.md) registram hashes, casos e limites. A [auditoria P20261116.2](AUDITORIA_POS_BETA11_P20261116_2.md) conserva o diagnóstico anterior. Sandbox e conta/nuvem seguem adiadas.
