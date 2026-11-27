# Auditoria após a beta.11 — P20261116.2

[Achados, correções e próximos passos](../../../docs/AUDITORIA_POS_BETA11_P20261116_2.md).

- `red-results.json`: três falhas reproduzidas com HTTP/arquivos reais em JVM. Para receber o contrato esperado, foi acrescentado apenas um parâmetro opcional inicialmente ignorado; o corpo anterior permaneceu sem proteção. Duas respostas maiores terminaram em erro tardio de digest; um segmento HTTP206 completo e válido terminou indevidamente em EOF.
- `new-tests.json`: dez casos de limites, resposta fragmentada, cache, tamanho contraditório, corpo truncado e retomada. Testes existentes também exercitam SHA incorreto, cancelamento, caminho legado e416.
- `unit-test-results.json` / `unit-comparison.json`: 911 casos do app beta + 85 de domain release, todos executados/aprovados; 996 no total, dez novos, sem casos anteriores ausentes. 37 controles do atualizador aprovados no foco. Não houve instrumentação Android nesta revisão.
- `RESULT.json` / `source-provenance.json`: compilação e rastreabilidade; 4 testes de overlay, 27 de empacotamento e 21 do comparador aprovados. Sem APK ou Release novos.
- `published-beta11-apk-inspection.json`: inventário do APK público original. 31 bibliotecas, ZIP alinhado a 16 KB e máquinas ELF coerentes com os nomes ARM; duas bibliotecas ARM64 têm PT_LOAD abaixo de 16 KB. Não foi executado aparelho de 16 KB nem inspecionada toda a semântica de carregamento/RELRO.
- `android-16k-reference.json`: referência oficial Android sobre AGP, NDK e bibliotecas pré-compiladas; hash do documento consultado e trechos, sem conteúdo executável.
- `declared-maven-osv-query.json`: quatro coordenadas declaradas consultadas; nenhum aviso retornado. Não é uma auditoria completa do grafo resolvido nem de código nativo.

O leitor de backup ainda carrega todo o conteúdo descompactado sem limite explícito. Isso foi identificado por inspeção; não se provocou OOM e não se impôs um limite arbitrário aos backups nesta revisão. Os próximos trabalhos estão no relatório. Sem logs brutos, chaves/senhas, ambiente local ou dados pessoais nestes resultados.
