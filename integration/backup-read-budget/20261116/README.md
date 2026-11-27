# Leitura limitada de backups — P20261116.3

Evidências filtradas para a próxima versão. **Sem novo APK/Release.**

- `RESULT.json`: escopo, política e resultado. Limite de entrada: 1/8 do heap máximo da VM, até 64 MiB decodificados; não garante ausência de OOM. Criação automática confere após serialização e antes de publicar/podar; exportação manual permanece disponível acima do orçamento.
- `red-results.json`: três falhas anteriores reproduzidas com payloads sintéticos e parâmetros opcionais inicialmente ignorados; nenhum OOM provocado.
- `unit-test-results.json`, `new-tests.json`, `unit-comparison.json`: 932 casos do app executados/aprovados e 85 anteriores de domain/UP-TO-DATE, total 1.017; 21 novos, nenhum anterior ausente. Tarefas reais beta/release, sem renomear relatórios. 38 controles focados aprovados.
- `source-provenance.json`: fontes e overlay efetivamente validados; inclui hashes da base anterior.
- `opencv-candidate-download.json`: origem pública, hashes e tamanho do AAR oficial. SHA-1 conferido com Maven Central; não é certificação integral de cadeia de suprimentos.
- `opencv-4.12.0-inspection.json`: oito ELF e PT_LOAD; offsets ZIP pertencem ao AAR intermediário, não ao APK final.
- `opencv-candidate-java-members.json`: 59 referências públicas do JAR compilado do OCR SDK presentes com descritor e caráter estático correspondentes. Não é certificação de toda a ABI, constantes, JNI ou inferência.
- `opencv-api-negative-control.json`: consumidor sem referências não recebe aprovação vazia.
- `opencv-candidate-compatibility.json`: minSdk21/ARM32/ARM64 e comparação dos quatro binários ARM, +3.213.164 bytes brutos. Dependência não alterada, candidata não integrada/compilada; tamanho do APK novo não medido.

4 controles de overlay, 27 de empacotamento e 21 do comparador aprovados. O ViewModel foi exercitado com validador controlado, Main dedicada e dispatcher IO real; o decoder real tem testes separados. Interface/SAF/WorkManager em aparelho, pico de RAM e execução nativa não foram validados nesta revisão.

Reprodução da pesquisa, com os artefatos locais correspondentes:

```sh
python3 scripts/audit/inspect_android_apk.py opencv-4.12.0.aar --native-root jni --output candidate-elf.json
python3 scripts/audit/check_java_api_references.py --consumer ocr-sdk-classes.jar --old opencv-old-classes.jar --new opencv-new-classes.jar --output candidate-members.json
```

Sem AAR/JAR, logs brutos, dados pessoais, keystore ou senhas neste diretório. [Decisões e limites](../../../docs/LEITURA_BACKUPS_P20261116_3.md).
