# Limpeza de recortes Paddle — P20261117.2

Evidências filtradas para a próxima versão, sem novo APK/Release.

- `RESULT.json`: duas falhas reproduzidas, sete casos novos e 15 controles focados aprovados. 939 app executados/aprovados + 85 domain anteriores/UP-TO-DATE = 1.024 casos sem regressões. Overlay4/empacotamento27/comparador21 aprovados.
- `red-results.json`: motor de produção anterior inalterado, sem parâmetro opcional de roteamento; verificações falham pela chamada de liberação ausente. Rastros privados/raw XML não incluídos.
- `test-setup.json`: primeira compilação sem os tipos OpenCV no classpath de testes, corrigida antes da reprodução válida. Não é falha de comportamento.
- `focused-results.json`, `new-tests.json`, `unit-test-results.json`, `unit-comparison.json`: casos, fronteiras e comparação usando tarefas reais beta/release, sem renomear relatórios.
- `native-libraries-unchanged.json`: os 31 ELF ainda coincidem por hash com a mesclagem OpenCV P20261117.1. Essa comparação não executa o código nativo.
- `source-provenance.json`: fontes/overlay efetivamente validados e hashes da base anterior.

Os testes executam OCREngine.run/construção real, ordenação, lotes, índices, filtro e finally, com carregamento de modelos/detecção/corte/reconhecimento/Mats simulados. Provam chamadas de liberação e saídas de controle; não executam JNI, alocação nativa ou inferência e não medem RAM. O escopo cobre recortes devolvidos ao motor; temporários internos de operações que falham antes de devolver o recorte e falhas na própria liberação não estão cobertos.

Sem bibliotecas/modelos, logs brutos, caminhos privados, dados pessoais ou credenciais. [Correção, casos e limites](../../../docs/LIMPEZA_RECORTE_OCR_P20261117_2.md).
