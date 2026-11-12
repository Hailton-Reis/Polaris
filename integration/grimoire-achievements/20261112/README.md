# Conquistas e grimórios — P20261112.1

Beta.11/código112 em desenvolvimento, posterior a fdc768e. A beta.10 pública permanece igual. [Critérios e limites](../../../docs/CONQUISTAS_GRIMORIOS_P20261112_1.md), [artes e proveniência](../../../design/polaris-grimoires/20261111/README.md).

## Implementação

Doze conquistas oferecem quatro caminhos alternativos para cada grimório: pontos, biblioteca, exploração e conclusão. Basta um caminho; os marcos não são um saldo gastável. A biblioteca lógica já projetada fornece os dados antes de filtros. Não há observador de banco, varredura de capítulos ou consulta de rede novos. Contagens máximas são guardadas em String comum; desbloqueios permanecem no StringSet existente. A restauração cosmética combina maiores marcos/ícones conhecidos e ignora tipos incorretos, sem alterar a restauração de fontes nem os esquemas SQL/Protobuf.

A edição inicial do grimório teve a névoa externa removida por edição com `image_gen.imagegen`; a primeira geração está arquivada. Margens de 22% ampliam os livros. Recursos somam 414.354 bytes. O [ensaio anterior](../../grimoire-icons/20261111/README.md) passou nos componentes, mas a inspeção identificou a névoa; este registro trata da versão refinada e das conquistas.

## Verificação

- **880/880 testes JVM passaram**, preservando os 872 anteriores, com oito novos e nenhum skip. Cobrem alternativas, limites, máximos permanentes, repetições de adicionar/remover, edições vinculadas, conclusão conservadora, valores inválidos e serialização. [Comparação](unit-comparison.json).
- **37/37 testes Android passaram em API26/x86_64**, em 263,697 segundos. Os 35 anteriores são mantidos, incluindo sessões, filtros, preferências, busca e biblioteca. Dois casos novos verificam liberação com zero XP e 25 obras, retenção após remoção e reabertura de preferências, criação de preferências de backup nativas, serialização Protobuf e restauração no núcleo de produção. Um backup mais antigo não reduz os marcos; tipo incorreto é ignorado. O caso de backup não executa agendamento WorkManager nem a ida/volta em aplicativo externo.
- **13 controles de overlay/empacotamento passaram**, incluindo aplicação limpa/CRLF, hashes das quatro imagens e fixture DEX binária. Os 398 caminhos cumulativos correspondem aos fontes compilados. [Escopo](source-delta.json).
- O ZIP do APK contém as quatro imagens atuais com bytes/hashes iguais aos recursos gerados. [Inspeção](packaged-artwork.json). Os APKs de componentes ficam fora do Git; [hashes](artifacts.json) são registrados antes da instrumentação e conferidos no resultado final.
- Nenhuma dependência, modelo OCR, permissão, manifesto ou esquema SQL/Protobuf novo. A consulta anterior de vulnerabilidades não foi repetida. [Entradas preservadas](unchanged-inputs.json).

## Conferência visual

As [quatro imagens nativas](preview/icons/) foram renderizadas pelo PackageManager, mantendo um único atalho e os links da atividade principal. O grimório inicial está sem a névoa retangular; as figuras ficam maiores e sem cortes aparentes na máscara arredondada desta VM.

A [seleção de aparência](preview/appearance/appearance-aurora-light.png) mostra 450 pontos, três folhas selecionado, quatro folhas disponível e cinco folhas bloqueado. A [tela de conquistas](preview/appearance/achievements-library.png) mostra quatro folhas disponível com apenas Colecionador cumprido: 25/25 obras; 450/4.500 pontos, 3/10 iniciadas e 1/5 concluídas ainda não atingidos. A interpretação de alternativa é visível. Jornada e configurações mantêm suas capturas. [Inspeção](ui-review.json).

## Reprodução e ambiente

Aplicar os overlays do projeto sobre o upstream fixado, usar JDK21/SDK37 e os dois init scripts arquivados. Executar `:domain:testDebugUnitTest :data:testDebugUnitTest :source-api:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest`. O init seleciona x86_64 e o runner de componentes; não serve para distribuir celulares. A constante BUILD_TIME é fixada para reprodução; os horários reais estão nos registros.

O ensaio inicial encontrou conversão permissiva de texto em número na desserialização das conquistas; os campos conhecidos agora exigem inteiros JSON. O teste foi preservado e passou na suíte final. A fixture de backup Android também foi corrigida para fornecer a lista obrigatória de obras vazia ao construir o envelope. Os logs dos dois diagnósticos estão arquivados.

O System UI da VM apresentou ANR após verificar/instalar o APK; a captura foi inspecionada e a mensagem fechada antes de iniciar a instrumentação, aguardando foco no Launcher. Nenhuma recuperação de interface ocorreu durante os testes. Dados do app/guest foram preservados; SELinux e verificação de APK não foram desativados. [Ambiente](runtime-environment.json).

## Limites

Esta é uma prova de componentes em VM API26/x86_64. Não certifica inicialização completa, desempenho ARM, máscaras ou ícones temáticos em Android recente, fontes/contas reais nem toda a próxima beta. Login WebView, biblioteca pessoal, fluxo completo leitor/downloads e ida/volta por banco/interface de leitores externos continuam pendentes. Preservar o backup original.

[Resultado](TEST_RESULTS.json), [instrumentação](android-final.log), [proveniência](android-run.json) e [hashes](SHA256SUMS.txt).
