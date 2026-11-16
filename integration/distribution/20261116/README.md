# Distribuição beta não depurável — P20261116.1

A variante `beta` usa o mesmo identificador `.dev` e certificado da beta.10, com código 112. Depuração, `testOnly` e profiling por shell foram conferidos no APK compilado. A otimização R8/remoção de recursos permanece desativada nesta variante para preservar o comportamento de carregamento dinâmico de extensões já exercitado.

- `candidate-manifest.json`: tamanho/hash, identidade, certificado, arquiteturas, revisão e inventário de classes DEX do novo APK interno. Os dois descritores ARM apontam para um único arquivo.
- `unit-test-results.json` / `unit-comparison.json`: 901 casos do app na variante beta e 85 de domain release, todos executados/aprovados antes da retomada do empacotamento; nenhum caso anterior ausente. A primeira montagem foi interrompida pela proteção de disco após os testes. Com os fontes inalterados, a montagem foi retomada com sucesso e pôde reutilizar os relatórios completos como UP-TO-DATE (`validation-resume.json`). O comparador seleciona os diretórios reais dessas tarefas, sem reaproveitar relatórios debug para mascarar sua ausência.
- `RESULT.json`: compilação/empacotamento aprovados; overlay4, empacotamento27 e comparador21 aprovados. Não foram executados testes de instrumentação nesta etapa.
- `build-model.json`: flags e ausência de dependência de aparelho/emulador no grafo de montagem. Assinatura e identidade são reconferidas no artefato, não inferidas apenas do modelo Gradle.
- `native-inventory.json`: bibliotecas ARM32/ARM64; o worker independente de OCR Dbnet permanece. Seu backend nativo opcional continua exclusivo ARM64.
- `legacy-apk-rejections.json`: o APK interno anterior foi efetivamente recusado pelo novo verificador de flags/componentes e classes. O inventário lê definições de classes de todos os DEX, em vez de confundir strings legadas com código executável.
- `artifact-comparison.json`: diferença entre pacotes internos, sem atribuir a variação exclusivamente à retirada da sandbox.
- `source-provenance.json`: hashes dos fontes e overlay reproduzível.

O exportador exige manifesto anterior e recusa código não crescente, chave/identidade incompatível, depuração ativa, componentes de teste/sandbox e classes JDBC/JUnit de teste. Chave privada e senhas não integram estes resultados. O APK permanece um candidato interno; não houve Release pública. Mesmos ID/certificado/código crescente são condições necessárias e não substituem a instalação real preservando dados.

Aceite final pendente: atualização beta.10→beta.11, SAF/interface Android, SQLite/preferências e troca pela interface de leitores externos, leitura/tradução/inferência real e qualidade/pico de memória no A12/ARM. Conta/nuvem e sandbox de extensões continuam adiadas. Não há logs brutos, ZIPs de ambiente ou dados pessoais nesta evidência.
