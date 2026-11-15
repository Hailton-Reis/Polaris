# Remoção da sandbox — P20261115.2

O executor está arquivado na [branch anterior](https://github.com/Hailton-Reis/Polaris/tree/archive/sandbox-P20261115.1) e saiu dos fontes compilados. O aviso único com duas marcações e as verificações de assinatura/integridade permanecem. [Escopo e recuperação](../../../docs/ARQUIVAMENTO_SANDBOX_P20261115_2.md).

- `archive-inventory.json`: hashes dos 32 arquivos Android retirados, dos dois scripts históricos e identidades dos 94 casos JVM exclusivos arquivados.
- `unit-comparison.json` / `unit-test-results.json`: dos 1030 casos anteriores, 94 saem junto com o executor. Os 936 restantes constam aprovados: 851 do app executados nesta compilação e 85 de domain já aprovados/UP-TO-DATE. Nenhum caso fora da remoção está ausente, falhando ou ignorado.
- `artifact-inspection.json`: serviço/tela ausentes nos manifestos fonte/mesclados e nenhuma classe do pacote da sandbox nos JARs de código de produção. Worker OCR e teste de idioma preservados. Classes antigas de instrumentação não permaneceram na saída atual.
- `RESULT.json`: tarefas selecionadas e resultados de compilação/overlay/empacotamento.
- `source-provenance.json`: hashes dos fontes selecionados e do overlay reproduzível.

App e instrumentação foram compilados; testes de aparelho não foram executados. Quatro testes de aplicação completa/idempotência/CRLF/drift do overlay e 16 de empacotamento passaram. Não foi produzido APK atualizado, não se mediu redução de tamanho e nenhuma Release foi publicada. Não há logs brutos, ZIPs, ambiente local, chaves ou senhas nestes resultados.
