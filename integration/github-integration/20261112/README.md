# Integração de main na branch de engenharia

Os conflitos estavam em README e CHANGELOG. As notas de publicação da beta.10 foram preservadas junto das revisões posteriores de desenvolvimento, com indicação explícita do escopo de cada resultado. Os demais arquivos de apresentação, histórico e publicação foram incorporados de main.

O patch Android permaneceu byte a byte igual ao checkpoint de 880 testes JVM e 37 Android. Não houve motivo para repetir essa suíte por mudanças de documentação. Os 12 testes do preparador/publicador incorporados de main passaram; os uploads impressos nesse log são mocks, sem acesso de publicação. O workflow de upload exige disparo manual.

Este commit integra main na branch de engenharia. Não integra o PR em main nem publica APKs. [Resultado](RESULT.json).
