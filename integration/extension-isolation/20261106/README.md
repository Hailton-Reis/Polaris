# Prova Android de isolamento — 06/11/2026

Seis controles passaram no Android 8/API 26 x86_64 por software, em um APK de teste independente. O host era UID 10065; o serviço declarado com isolatedProcess=true recebeu UID 99000. Não herdou INTERNET, não leu nem alterou arquivos privados sintéticos do host, não conectou diretamente ao socket de teste e recusou uma operação IPC não prevista. O host também conferiu seu arquivo intacto e a ausência de conexão recebida.

**Não é um executor de extensões integrado ao Polaris.** O controle não carrega APK de extensão, não inicia o leitor nem valida UI, ARM, Android 14+, intermediário HTTP, cookies ou provedores SAF. O código é intencionalmente pequeno para verificar a fronteira do Android com UID normal de aplicativo. O emulador foi encerrado depois do teste.

- [Código Java e manifesto](probe/)
- [Resultado](TEST_RESULTS.json), [log da instrumentação](android-runtime.log), [proveniência](provenance.json)
- [Desenho e condições para integração](../../../docs/ISOLAMENTO_DE_EXTENSOES.md)

## Reprodução

O construtor exige saída fora de checkouts Git e gera uma chave sintética local, sem reutilizar a assinatura de distribuição:

```sh
python scripts/extensions/build_isolation_probe.py --output /tmp/polaris-isolation-probe --sdk /caminho/sdk --java-home /caminho/jdk21 --gradle-home /caminho/gradle
adb -s SERIAL install -r /tmp/polaris-isolation-probe/probe.apk
adb -s SERIAL shell am instrument -w -r test.polaris.isolation.probe/.Probe
```

O SDK usado contém platform 37/build-tools 37 e o cache Gradle contém o builder 9.3.1 para D8. O DEX resultante tem mínimoAPI 26. A execução deve informar status PASS, passed_checks 6 e INSTRUMENTATION_CODE -1. A chave privada gerada fica na saída local e não acompanha este registro.
