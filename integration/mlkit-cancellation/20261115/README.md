# Cancelamento do processamento ML Kit — P20261115.5

[Problema, comportamento e limites](../../../docs/CANCELAMENTO_MLKIT_P20261115_5.md).

Cancelar o await da corrotina não necessariamente interrompe a Task do SDK. A proteção mantém o recurso reservado até a tarefa de processamento terminar e reconfere o chamador antes de entregar o resultado. É usada em OCR de página inteira/faixas e tradução de quadrinhos/documentos; downloads de modelo permanecem canceláveis.

- `red-results.json`: três falhas de ciclo de vida reproduzidas com Tasks reais, coordenador de produção e motor de controle. O await existente foi centralizado sem proteção antes da correção. Não foram usados modelos/bitmaps/inferência real. Erros de preparação e ajustes de asserção de identidade de exceção não contam como RED funcional.
- `new-tests.json`: 12 controles aprovados de conclusão, cancelamento, descarte de resultado, falha, fila/serialização e liberação única. Exceções são conferidas por tipo, mensagem e cadeia da causa original, pois corrotinas podem recuperar/copiar a stack trace.
- `unit-test-results.json` / `unit-comparison.json`: 901 testes do app executados/aprovados, incluindo 12 novos; mais 85 de domain previamente aprovados/UP-TO-DATE. Total 986 casos nos relatórios, sem falhas/skips; nenhum dos 974 casos anteriores ausente.
- `RESULT.json`: compilação do app/instrumentação aprovada; quatro testes de overlay e 16 de empacotamento passaram. Dois controles Android de Task/corrotina foram compilados, não executados. Eles também não executam modelos/bitmaps/inferência.
- `source-provenance.json`: hashes dos fontes e overlay reproduzível. Dependências de build inalteradas. Sandbox de extensões segue ausente e o worker OCR independente foi preservado.

Se a Task do SDK não terminar, o recurso permanece reservado; não há novo timeout ou cancelamento nativo forçado. Não se garante tempo total, memória máxima ou ausência de OOM. Desempenho/diagnóstico no A12/ARM32/ARM64, qualidade e interface de leitura/tradução continuam pendentes. Não foram gerados APK ou Release. Sem logs brutos, ZIPs, ambiente local, chaves/senhas ou dados pessoais nos resultados.
