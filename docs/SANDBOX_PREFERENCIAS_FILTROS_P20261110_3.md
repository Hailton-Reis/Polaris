# Sandbox: preferências e filtros — P20261110.3

Revisão de desenvolvimento da beta.11/código 112, posterior a ea7cb05. A beta.10 publicada permanece inalterada. A validação desta rodada e seus limites estão em [evidências](../integration/sandbox-settings/20261110/README.md).

## Comportamento

Extensões HTTP isoladas passam a oferecer filtros de texto, seleção, marcação, três estados, ordenação e grupos aninhados no painel existente. O Polaris constrói controles próprios a partir de descrições limitadas; no processo isolado os valores são aplicados às instâncias originais dos filtros da extensão. Classes e listeners da extensão não são carregados na interface do app. Se as opções mudarem, uma seleção antiga é recusada: reabra/redefina o painel para obter os filtros atuais.

A ação de configurações só aparece no catálogo quando a fonte isolada declara suporte. A raiz de preferências é registrada antes de a extensão montar os campos, permitindo resolver dependências entre controles como no fluxo nativo. A tela de configuração carrega de forma assíncrona e suporta texto, switches, caixas de seleção, listas, seleção múltipla e grupos. As validações e callbacks executam no processo isolado. Um callback que retorna falso pode gravar seu próprio valor, conforme o comportamento do AndroidX, inclusive um inteiro vindo de um campo de texto. O host grava apenas valores primitivos e conjuntos de strings dentro de limites de tamanho e quantidade. Ações de login, intents e telas personalizadas ficam indisponíveis nesse modo; não há troca automática para compatibilidade.

## Separação de dados

O armazenamento pertence à combinação de pacote e identidade de assinatura verificada. Uma extensão recebe uma cópia apenas das suas configurações de fontes. Outro pacote ou outra assinatura não herda essa cópia. O worker usa preferências em memória, não um Context do processo principal. Nomes globais de arquivos de preferências são negados.

Cada sessão é serializada e lê o estado mais recente após entrar na exclusão mútua. Os resultados são validados e persistidos antes da próxima sessão, evitando perder uma mudança quando duas chamadas estavam aguardando. Limites e validação de toda a mensagem precedem a gravação. Isso não transforma vários arquivos de preferências em uma transação de banco.

## Backups existentes

O formato Protobuf e as chaves nativas `source_<id>` são mantidos, com os tipos originais dos valores. A exportação lê as preferências do proxy isolado, sem exportar os nomes internos do armazenamento Polaris. Configurações antigas/restauradas ficam no arquivo nativo; a tela da fonte oferece **importação explícita**, com confirmação, dos campos editáveis declarados por aquela fonte. O arquivo original é preservado. Não se distribuem automaticamente credenciais de backups a código recém-instalado.

Uma falha encontrada na revisão permitia à seção de preferências de fontes de um backup escolher nomes arbitrários de arquivos do host. Agora somente nomes nativos canônicos com ID Long são aceitos, incluindo IDs legados negativos. Nomes de estado interno, caminhos e namespaces da sandbox são recusados. Não houve mudança no esquema SQL nem no formato de backup.

Quando a opção de incluir configurações privadas está desligada, a exportação isolada também omite chaves obviamente sensíveis, como token/password/api_key. Esse critério é uma heurística de nomes, não identificação universal de segredos. O comportamento das fontes em compatibilidade não foi reescrito.

## Limites e próximas etapas

- Preferências básicas e filtros estáticos não resolvem todas as extensões. Opções dinâmicas, backing types personalizados, inicializações com APIs globais e alterações de domínio precisam de testes com cada implementação.
- WebView, login/challenges, persistência de cookies entre sessões, ações personalizadas, arquivos e novels ainda precisam de adaptação própria.
- A sandbox continua experimental e optativa por extensão. Compatibilidade executa fora dela, por decisão explícita; nenhuma dessas etapas promete risco zero.
- Faltam aceite de fontes reais, fluxo completo com biblioteca pessoal e backups de outros leitores, ARM32/ARM64 e Android recente. A rodada de componentes em API26 não mede fluidez no A12.

Reprodução: aplicar os overlays ao upstream fixado, executar testes JVM e montar os APKs de componentes com os init scripts arquivados. A fixture DEX foi compilada de código sintético auditável, sem contas, capítulos protegidos ou extensões de terceiros.
