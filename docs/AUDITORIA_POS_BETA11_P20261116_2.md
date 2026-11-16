# Auditoria após a beta.11 — P20261116.2

16/11/2026, America/Fortaleza. Base auditada: beta.11 publicada, P20261116.1/código 112, implementação 32a9c831c32b83f761001cf1a298348defaed2fa. Esta revisão é desenvolvimento para a próxima versão; não gera APK nem altera a Release pública. O próximo lançamento precisará de versão e código superiores aos da beta.11.

## Achados e decisões

| Achado | Evidência e impacto | Estado |
| --- | --- | --- |
| AUD-01: tamanho aprovado no manifesto era descartado antes do download | O campo era conferido na seleção do asset, mas o downloader recebia somente URL/SHA. Um corpo maior, inclusive chunked sem Content-Length, podia ocupar cache antes de falhar no digest | Corrigido no código desta revisão |
| AUD-02: trecho HTTP206 completo, porém menor que a cauda inteira, virava EOF | O downloader exigia o tamanho total após cada resposta. Dependia de tentativas externas para continuar e podia esgotar o orçamento de retries | Corrigido no código desta revisão |
| AUD-03: duas bibliotecas ARM64 com PT_LOAD abaixo de 16 KB | `libc++_shared.so` e `libopencv_java4.so` no APK público. O ZIP já está alinhado a 16 KB; isso não corrige o layout ELF do fornecedor | Revisar dependências e validar em sistema 16 KB; sem crash em aparelho reproduzido |
| AUD-04: decodificação de backup sem limite explícito após descompressão | `BackupDecoder.decode` usa `readByteArray()` no fluxo raw/gzip. A retenção também o utiliza para conferir cópias antigas; payload e objetos podem elevar o pico de heap | Inspeção confirmada; proteção de memória ainda não implementada |
| AUD-05: alvo real da atualização de OpenCV difere do catálogo | `ppocr-sdk/build.gradle.kts` fixa `com.quickbirdstudios:opencv:4.5.3.0`; o alias 4.5.3 do catálogo não é o que esse módulo consome | Atualizar/recompilar o artefato efetivo preservando ARM32; não alterar somente o alias |

O decoder de backup foi apenas inspecionado: não se provocou OOM e não se impôs um teto arbitrário que pudesse excluir bibliotecas legítimas. A próxima correção deve limitar bytes depois da descompressão, preservar CRC/fechamento, tratar cancelamento e testar backups grandes antes de definir política de heap. Limitar a entrada também não garante, sozinho, o pico do grafo Protobuf desserializado.

## Correção do atualizador

O tamanho segue do manifesto para `Release`, os dois pontos de abertura da tela (checagem automática/manual), CreationExtras/ViewModel, WorkManager e downloader. Fica persistido na entrada do trabalho, permitindo mantê-lo numa retomada após recriação do processo. A propagação das telas/WorkManager foi compilada; não foi executada como fluxo Android em aparelho.

Quando o tamanho é conhecido:

- Resposta 200 com Content-Length divergente e resposta 206 com total contraditório são recusadas antes de gravar o corpo.
- Sem Content-Length, o corpo não pode gravar além do total aprovado. A verificação ocorre antes de somar/gravar o próximo bloco. Bufferização HTTP não é uma promessa de tráfego limitado byte a byte.
- Cópia parcial maior que o esperado é descartada. APK em cache e resposta 416 também precisam respeitar o tamanho.
- Cada trecho206 completo continua no próximo offset até completar o APK. Corpo realmente truncado continua preservado para retomar depois.
- SHA-256 ainda é obrigatório para confirmar integridade nos fluxos oficiais; tamanho correto não o substitui. Pedidos legados sem tamanho mantêm a compatibilidade existente, sem prometer a nova quota de manifesto para eles.

Três falhas reproduzidas antes da correção com HTTP e arquivos reais em JVM. Foi acrescentado um parâmetro opcional inicialmente ignorado para expressar o contrato esperado; o corpo anterior permaneceu com o mesmo comportamento. Dois casos terminaram em erro tardio de digest e um em EOF indevido.

Após a correção: 37 controles focados aprovados, incluindo dez novos. Compilação final aprovada em 3min05s; 911 casos do app beta e 85 de domain release executados/aprovados, total 996, sem falhas/skips ou casos anteriores ausentes. Quatro controles de overlay,27 de empacotamento e21 do comparador aprovados. Instrumentação e instalação/uso em aparelhos não foram executados nesta revisão.

## Inspeção do APK publicado

Arquivo de 259.481.310 bytes, SHA-256 `27feeaadc4aec9f54c9a6b57760421dee601e9f3bfe7efef9866fd3ae7fa40e3`. As bibliotecas nativas somam **192,286,636 bytes (74.1% do arquivo)** nas duas arquiteturas. Assets somam 29.595.933 bytes comprimidos e DEX 29.461.103 bytes comprimidos. Esses números vêm do ZIP: não são tamanho instalado nem RAM.

As 31 bibliotecas têm máquina ELF coerente com a ABI no caminho; os offsets ZIP estão alinhados a 16 KB. Duas ARM64 têm PT_LOAD abaixo de 16 KB. Não se verificaram todas as condições de RELRO/carregamento nem se executou Android de 16 KB. [Orientação oficial Android](https://developer.android.com/guide/practices/page-sizes) exige atenção tanto ao empacotamento quanto aos binários pré-compilados; NDK 28 alinha builds novos por padrão, mas não reescreve bibliotecas antigas de terceiros.

Reprodução da inspeção:

```sh
python3 scripts/audit/inspect_android_apk.py Polaris-0.1.0-beta.11-universal.apk --output apk-inspection.json
```

Redução de tamanho deve começar pelas bibliotecas maiores e seu uso real. `libtdjni.so` tem uso em `TelegramCloudManager`; não foi classificada como descartável. O armazenamento sem compressão das bibliotecas permite carregamento direto, portanto uma mudança de empacotamento precisa medir também instalação e runtime. Não foram removidos recursos/modelos nesta revisão.

## Consulta de dependências

OSV consultado para quatro coordenadas Maven declaradas: jsoup 1.23.2, Guava 33.7.2-android, OkHttp 5.4.0 e kotlinx-serialization-protobuf 1.11.0. Nenhum aviso retornado naquela consulta. Isso não cobre todo o grafo resolvido, todos os provedores de extensões ou as bibliotecas nativas; versão antiga sozinha não é prova de vulnerabilidade.

## Próximos passos

1. Investigar OpenCV/runtime C++ para 16 KB, conferindo o artefato realmente consumido e mantendo ARM32/API 26 antes de qualquer substituição.
2. Projetar e reproduzir os limites de leitura/descompressão de backups e medir o pico, sem apagar cópias existentes.
3. Incorporar os relatos da rodada de testes da beta.11 nos aparelhos: fonte/capítulo, documento, recuperação de progresso, armazenamento e contexto do erro.

Sandbox e conta Google/nuvem continuam adiadas por decisão do mantenedor. As correções deste relatório ficarão para a próxima versão. [Evidências filtradas](../integration/post-beta11-audit/20261116/README.md).
