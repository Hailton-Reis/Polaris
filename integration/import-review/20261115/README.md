# Revisão de importações — P20261115.3

[Escopo, fluxo e limites](../../../docs/REVISAO_IMPORTACOES_P20261115_3.md).

O armazenamento passa a mostrar cópias interrompidas e pastas no antigo formato de nomeação. Inventário somente leitura, serializado com a publicação e limitado por entradas, filhos, resultados, metadados e orçamento cooperativo de tempo. A classificação por metadados não certifica o payload; a retomada continua dependendo da conferência completa do importador. Cópias antigas/incompletas/desconhecidas permanecem preservadas.

- `RESULT.json`: tarefas selecionadas, compilação e resultados; ausência continuada do executor da sandbox conferida no JAR de produção/manifesto mesclado.
- `unit-test-results.json` e `unit-comparison.json`: 873 casos do app executados e aprovados, incluindo 22 novos; mais 85 de domain já aprovados/UP-TO-DATE. Total de 958 casos nos relatórios, sem falhas/skips e nenhum dos 936 casos anteriores ausente.
- `new-tests.json`: identidades dos 22 cenários novos. Incluem arquivos e streams reais, recusa de leituras do payload, preservação de bytes, esquema/UTF-8 inválidos, metadados excessivos, falta de permissão, listagens nulas, limites/tempo/tamanhos, overflow, cancelamento e espera pelo mutex durante publicação até o registro simulado.
- `source-provenance.json`: hashes dos fontes alterados e overlay reproduzível.

App e instrumentação compilados. Dois cenários Android de UniFile nativo foram compilados, não executados: inspeção seguida de limpeza de cache preserva cópias e inspeção de pastas antigas/incompletas mantém os bytes. Quatro testes de aplicação/idempotência/CRLF/drift do overlay e 16 de empacotamento passaram.

Provedor e fronteira de registro no banco são simulados nos testes JVM; não há aceite de SAF remoto, interface real, aparelhos ou pico. Não foi gerado novo APK nem publicada Release. Os resultados não contêm logs brutos, arquivos ZIP, ambiente local, chaves ou senhas.
