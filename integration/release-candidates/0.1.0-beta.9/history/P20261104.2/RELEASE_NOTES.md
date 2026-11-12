## Polaris 0.1.0-beta.9

**Pré-lançamento para testes · Android 8 ou superior · ARM32 e ARM64 · P20261104.2 · código 110**

Esta versão melhora a apresentação das traduções, as opções de OCR e a recuperação de downloads de atualizações. Continua usando os modelos já disponíveis no aplicativo, sem exigir chave Gemini.

### Baixar e instalar

Escolha **somente um APK**, conforme a arquitetura do Android instalado:

| Sistema | Arquivo |
| --- | --- |
| ARM64 / 64 bits | [Polaris ARM64](https://github.com/Hailton-Reis/Polaris/releases/download/v0.1.0-beta.9/Polaris-0.1.0-beta.9-arm64-v8a.apk) |
| ARM32 / ARMv7 / 32 bits | [Polaris ARM32](https://github.com/Hailton-Reis/Polaris/releases/download/v0.1.0-beta.9/Polaris-0.1.0-beta.9-armeabi-v7a.apk) |

O APK é completo; não é necessário juntar partes nem executar CMD. O modelo comercial do aparelho, sozinho, não confirma se o Android instalado é de 32 ou 64 bits.

Instale sobre a versão anterior. Os APKs mantêm o identificador e a assinatura da beta.8. Em **Sobre**, confira **0.1.0-beta.9 / P20261104.2**. Se houver conflito de assinatura, preserve a instalação e os dados existentes. O roteiro cobre a verificação de biblioteca e progresso após atualizar.

### O que mudou

- **Cedilha na Anime Ace:** o arquivo incluído não continha Ç/ç. Essas letras agora usam um complemento de quadrinhos já disponível, com altura compatível. Acentos recebem espaço adequado entre linhas.
- **Tamanho e encaixe:** medição e desenho usam o mesmo texto estilizado. O ajuste compara os espaços seguros existentes para escolher letras maiores quando cabem, preservando palavras. **Fonte das traduções** escolhe a família; tamanho e quebras se adaptam a cada região. Não há identificação automática da fonte original dos balões.
- **Caixas e títulos:** áreas de escrita são limitadas ao fundo medido e organizadas em conjunto para reduzir sobreposições nos leitores paginado e vertical. A limpeza por cor respeita seu retângulo medido.
- **OCR por faixas:** corrigido um caso de repetição nas bordas quando o mesmo texto recebia caixas cortadas de alturas diferentes. As faixas continuam experimentais e usam ML Kit ou PaddleOCR em inglês.
- **Opções coerentes:** faixas e DBNet são escolhas exclusivas. Requisitos de idioma e arquitetura desligam as opções dependentes quando necessário. Restaurar o requisito não ativa um experimento sozinho. A opção AOT-GAN foi retirada da tela porque sua preferência não era usada pelo processamento.
- **Atualizações recuperáveis:** o download continua ao sair da tela, repete falhas transitórias e retoma o parcial quando o servidor permite. O APK completo é verificado por SHA-256 antes da instalação. A tela e a notificação de conclusão oferecem abrir o instalador do Android.

A correção de fonte aparece ao reabrir o leitor, inclusive em traduções salvas. Para comparar motores de OCR, remova **somente a tradução salva** do capítulo e traduza novamente; mudar a opção não refaz o OCR já armazenado.

### Configuração sugerida para comparar em inglês

**PaddleOCR · faixas ligadas · DBNet desligado · tradutor ML Kit no dispositivo · Português (Brasil) · Anime Ace · efeitos sonoros e edição avançada desligados.** Depois compare com OCR ML Kit mantendo as demais opções. A preparação inicial dos recursos de tradução exige internet; depois de preparados, o ML Kit permite tradução offline. As faixas só atuam em imagens individuais suficientemente altas.

### Benchmark e validação

O ensaio do capítulo 40 usa originais públicos da Asura com cenas correspondentes às referências, mas segmentação diferente da MangaCloud EN. Em **11 recortes difíceis / 465 caracteres**, Paddle Small teve **9 textos exatos e 2 erros de caracteres**; ML Kit, **7 textos exatos e 10 erros**. Os controles brancos passaram nos dois. Paddle executou em implementação desktop revisada e ML Kit na API Android real; esses números não comparam velocidade ou RAM em ARM. A passagem ML Kit por faixas ficou parcial por limites de tempo no emulador. O preparo do tradutor excedeu o prazo: **a qualidade da tradução automática completa não foi avaliada**.

- **635 testes JVM: 618 aprovações e 17 falhas preexistentes**, sem regressões novas, casos anteriores ausentes ou testes ignorados. Não é uma suíte totalmente verde.
- **16 controles Android aprovados**, incluindo as cinco fontes em três tamanhos, encaixe, caixas escuras, balões brancos, decodificação e máscara. Usam Application isolada em emulador por software; não validam a abertura completa do aplicativo.
- APKs conferidos por SHA-256, assinatura e identidade Polaris. Fontes, modelos, assets e bibliotecas nativas permanecem iguais à revisão interna anterior.

Ainda exigem teste: instalação com dados preservados, retomada ao alternar redes, notificações, leitor completo e desempenho em celulares ARM32/ARM64. Balões conectados, painéis decorados e linhas ausentes não são declarados resolvidos em todos os casos. A beta.8 instalada pode precisar de uma atualização manual inicial para receber o novo downloader; a correção não modifica versões já instaladas.

| APK | Download |
| --- | ---: |
| ARM64 | 193,0 MB / 184,0 MiB |
| ARM32 | 153,2 MB / 146,1 MiB |

Modelos baixados, capítulos, traduções, caches e espaço do instalador contam separadamente. A atualização continua usando um APK completo; a retomada reaproveita o que já chegou **do mesmo arquivo**, sem patches entre versões.

Leia [o roteiro de primeiro teste](https://github.com/Hailton-Reis/Polaris/releases/download/v0.1.0-beta.9/PRIMEIRO_TESTE.md). Para futuras prévias no atualizador, ative **Receber atualizações experimentais**. Rascunhos não aparecem no aplicativo.

[Tipografia e capturas de controle](https://github.com/Hailton-Reis/Polaris/blob/e6bab4bc4fade68e3aa74e2677500ea762d34d29/integration/typography/20261104/README.md) · [Benchmark de OCR](https://github.com/Hailton-Reis/Polaris/blob/e6bab4bc4fade68e3aa74e2677500ea762d34d29/integration/ocr-benchmark/20261104-chapter40/README.md) · [Validação](https://github.com/Hailton-Reis/Polaris/blob/e6bab4bc4fade68e3aa74e2677500ea762d34d29/integration/document-reader/TEST_RESULTS.json) · [Código do candidato](https://github.com/Hailton-Reis/Polaris/tree/e6bab4bc4fade68e3aa74e2677500ea762d34d29)
