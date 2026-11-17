# OpenCV integrado — P20261117.1

Evidências filtradas da integração oficial, sem novo APK/Release.

- `RESULT.json`: compilação/mesclagem, 1.017 relatórios sem regressões, controles e limites. 932 app executados/aprovados e 85 domain anteriores/UP-TO-DATE. Nenhum caso JUnit novo. A primeira seleção pediu uma tarefa SDK inexistente e foi corrigida antes de executar testes.
- `merged-native.json`: saída real da tarefa Gradle; 31 ELF, quatro OpenCV/C++ oficiais, 27 peers inalterados, alinhamento/congruência ARM64 para 16 KiB e importações anteriormente fornecidas pelo C++ conferidas. Não certifica toda a ABI, APIs/relocações/namespaces do linker, JNI ou OCR.
- `previous-merged-native-hashes.json`: inventário anterior registrado antes de a tarefa de mesclagem executar.
- `resolved-artifact.json` e `dependency-resolution.json`: AAR efetivamente resolvido e grafo runtime, sem QuickBird.
- `java-members.json`: 59 referências do JAR real recompilado, presentes com mesmo descritor/caráter estático; não é certificação integral da ABI Java/constantes.
- `negative-controls.json`: verificador final recusa C++ antigo e ausência de OpenCV ARM32, em cópias temporárias de ELF reais. Produção preservada.
- `merged-manifest.json`: API mínima26, ID e versão de desenvolvimento preservados; atributos ausentes usam o padrão desabilitado. Não é inspeção de APK novo.
- `unit-comparison.json`, `unit-test-results.json`: tarefas reais beta/release, casos anteriores mantidos, sem falhas/skips.
- `source-provenance.json`: hashes do código e overlay validados.

O conjunto nativo cresce 3.213.164 bytes brutos; tamanho de APK/instalação e RAM não foram medidos. Faltam APK/ZIP final, JNI/OCR/qualidade e aparelhos ARM32/ARM64/16 KiB. Sem nova instrumentação ou inferência.

Reprodução com as saídas/artefatos locais correspondentes:

```sh
python3 scripts/audit/check_merged_native_libraries.py --merged merged/lib --candidate opencv-4.12.0.aar --previous-apk Polaris-beta11.apk --previous-manifest previous-merged-native-hashes.json --readelf llvm-readelf --output merged-native.json
```

Sem bibliotecas/AAR/JAR, logs brutos, caminhos privados, dados pessoais ou credenciais neste diretório. [Decisões e limites](../../../docs/OPENCV_P20261117_1.md).
