# Ensaio de OCR executado em 02/11/2026

Leia [o resultado](report/RESULTADOS.md) ou abra [comparacao.html](report/comparacao.html) no navegador para ver cada imagem e a saída real de cada motor. São 39 recortes sintéticos e uma página longa em dois modos. Todos os ensaios de OCR terminaram; os testes em aparelhos físicos continuam pendentes.

O resultado favorece preservar escala por faixas em imagens muito altas. Nos recortes em inglês, Small com detector acertou 26/27 textos completos, Tiny 22/27 e ML Kit 19/27. Os runtimes são diferentes e os recortes são controles, portanto não determinam um vencedor universal. Nas faixas, os três recuperaram as 38 linhas do controle, com CER zero após a normalização descrita. O capítulo real relatado ainda não foi fornecido.

## O que está preservado

- `android/app/src/main/assets/cases/`: os pixels efetivamente usados e suas transcrições.
- `paddle-results.json`: reconhecedores isolados; não confundir com sistema completo.
- `paddle-pipeline-results.json`: detector Small + cada reconhecedor, nos mesmos recortes.
- `paddle-long-results.json`: pipeline Paddle na página longa, inteira e por faixas.
- `mlkit-results.json`: API Android real, quatro modelos de escrita, saídas brutas.
- `long-detector-results.json` e `detection-score.json`: avaliação separada da localização de linhas antes do unclip.
- `scored-results.json`: saídas avaliadas, normalização e tabelas por idioma/etapa.
- `provenance.json`, `MODELS.md`: hashes, versões e origem dos modelos.
- `android/`: fonte do aplicativo mínimo de medição, separado do leitor.

## Recalcular métricas sem modelos ou Android

Com Python 3:

```bash
python3 test_metrics.py
python3 score_final.py
python3 make_report.py
```

A geração do relatório usa somente a biblioteca padrão. Os sete testes verificam normalização, distância de edição e regras geométricas de remoção de duplicatas. Os JSON brutos são preservados. Maiúsculas e espaços não contam como erro; pontuação conta.

## Reexecutar Paddle em CPU

Use um ambiente Python separado, instale `requirements.txt` e execute `setup_models.py`. Ele baixa três arquivos oficiais de modelos e verifica SHA-256 do arquivo e dos pesos. Os modelos não fazem parte deste pacote nem são adicionados ao APK do produto.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 setup_models.py
python3 run_paddle.py
python3 run_paddle_pipeline.py
python3 run_paddle_long.py
python3 detect_long.py
python3 score_detection.py
python3 score_final.py
python3 make_report.py
```

Se já possuir os pesos Small, a variável `POLARIS_PADDLE_MODELS` pode apontar para a pasta que contém `det/inference.onnx` e `rec/inference.onnx` + `inference.yml`. O Tiny fica em `tiny/` ao lado dos scripts; `POLARIS_TINY_MODELS` permite indicar uma pasta existente. Os hashes esperados estão em `provenance.json`. Os scripts são um port desktop do processamento do SDK e não medem o binário Android Paddle nem seu desempenho ARM.

Os PNGs medidos estão incluídos; regenerá-los não é necessário. `create_cases.py` documenta sua construção e aceita `POLARIS_ENGINEERING_REPO` e `POLARIS_NATIVE_REPO`; a regeneração também exige as fontes DejaVu/Noto CJK do host e Anime Ace/Balsamiq do checkout nativo. Compare os hashes em `report/cases.json` se regenerar.

## Reexecutar a API ML Kit

O harness Java foi compilado com JDK 21, Gradle 9.6.1, AGP 9.3.1, SDK 37 e os quatro módulos Text Recognition 16.0.1. O arquivo Gradle registra as resoluções disponíveis no ambiente de medição. Execute `gradle -p android :app:assembleDebug` com o SDK configurado, instale o APK de debug num Android de teste e inicie `org.polaris.ocrbench/.MainActivity`.

A execução usada neste relatório foi em AOSP API26 x86_64, sem KVM, com `largeHeap=true`. O APK inicial sofreu uma incompatibilidade no inicializador Jetpack de UI antes do OCR. A execução válida preservou DEX/modelos/recursos e removeu somente `androidx.startup.InitializationProvider` do manifesto. `android/AndroidManifest.executed.xml` registra o manifesto mesclado efetivamente usado; o manifesto-fonte também remove esse provider para futuras compilações. `MlKitInitProvider` foi mantido. Uma nova compilação não é prometida como reprodução binária do APK medido.

O aplicativo grava `files/results.json` a cada caso e `files/done.txt` ao finalizar. Colete somente após `done.txt` conter `done`:

```bash
adb -s SERIAL shell run-as org.polaris.ocrbench cat files/done.txt
adb -s SERIAL exec-out run-as org.polaris.ocrbench cat files/results.json > mlkit-results.json
python3 score_final.py
python3 make_report.py
```

Substitua `SERIAL` pelo dispositivo de teste. O harness inclui só a ABI x86_64. Isso **não altera** a meta do produto de Android 8+ ARM32/ARM64; a medição física dessas ABIs é uma etapa posterior. O cronômetro de `en-long-full` no harness inclui a etapa de faixas, e os runtimes diferem: nenhum tempo deste ensaio deve ser usado para classificar os motores.

O harness não executa tradução, filtros de balão ou renderização do Polaris. Ele mantém a página completa na memória durante as faixas; não representa a memória do decodificador regional do app. A release pública e os APKs do leitor permanecem inalterados.
