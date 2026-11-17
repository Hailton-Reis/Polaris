# Descoberta entre fontes — P20261117.3

Evidências filtradas, para a próxima versão. **Sem novo APK/Release.**

- `RESULT.json`: política, limites e validação final. 952 app executados/aprovados + 87 domain anteriores/UP-TO-DATE = 1.039 casos; 15 novos, nenhum anterior ausente. Overlay4/empacotamento27/comparador21 aprovados.
- `red-results.json`: quatro falhas anteriores reproduzidas, com os dois arquivos de produção inalterados e sem parâmetro de roteamento novo. Rastros/XML privados não incluídos.
- `simulated-timings.json`: atrasos virtuais de provedores e checagens simuladas, com código de catálogo real. Não é benchmark de rede/aparelho. 3→2 segundos, 4→2 segundos, consulta repetida 1→0 e elegibilidade de nova tentativa após minuto são provas de controle/política.
- `focused-results.json`: 118 casos focados antes dos ajustes finais; todos os casos atuais estão cobertos pela rodada completa.
- `new-tests.json`, `unit-test-results.json`, `unit-comparison.json`: variantes reais beta/release; cancelamento/vagas, duas obras, resultado parcial, conclusão diária, timeout individual/confirmado, fonte fixa e compatibilidade de memo antigo.
- `native-libraries-unchanged.json`: os 31 ELF continuam com os hashes da mesclagem OpenCV P20261117.1.
- `source-provenance.json`: hashes dos fontes e do overlay realmente validados, mais os originais da reprodução.

O semáforo limita operações alternativas deste serviço, sem prometer duas requisições HTTP no app inteiro. A descoberta tem orçamento próprio, além das etapas anteriores. Timeouts dependem de cancelamento cooperativo. Nova elegibilidade não cria um temporizador; o app precisa solicitar outra tentativa. Dados de associação/numeração não foram afrouxados.

Interface e recursos compilados, sem nova instrumentação ou execução em aparelho. Fontes reais, qualidade dos resultados e tempo/RAM no dispositivo permanecem para validação. Nenhum log bruto, biblioteca/modelo, caminho privado, dado pessoal ou credencial publicado. [Comportamento, exemplos e limites](../../../docs/BUSCA_FONTES_P20261117_3.md).
