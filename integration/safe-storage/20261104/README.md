# Preservação de extensões e backups — P20261104.3

Candidato interno beta.9, versionCode 110. Não publicado. A beta.8 permanece pública. Este relatório resolve os três achados P1 da [auditoria](../../../docs/AUDITORIA_DADOS_E_EXTENSOES_20261104.md), dentro dos limites dos testes abaixo.

## Mudanças

- Extensões privadas: cópia em arquivo temporário único no mesmo diretório, somente leitura antes de escrever, sincronização, validação dos bytes preparados e substituição atômica. Falhas anteriores à substituição preservam o arquivo funcional. Instalação/desinstalação são serializadas; continuam as verificações de assinatura e versão. Arquivos `.pending` não são carregados como extensões.
- Downloads de extensões: temporários e identificadores próprios por tentativa, cancelamento da chamada HTTP durante leitura, estados terminais e limpeza condicionada à tentativa correspondente. Um fluxo antigo não pode remover o registro de uma nova tentativa; pacotes com o mesmo hash não compartilham identificação.
- Backups: serialização antes de criar o destino; gravação/fechamento, verificação de gzip e comparação integral dos bytes descomprimidos; renomeação e nova conferência da URI final em pastas. Erros ao reler são explícitos e não registram sucesso. Destinos existentes não vazios são preservados.
- Retenção: só ocorre após o novo backup ser verificado. Mantém quatro cópias verificadas, usa nomes com milissegundos e UUID e preserva arquivos antigos inválidos/ilegíveis sem contá-los como substitutos úteis. Criações concorrentes são serializadas.

Não foram alterados protobuf, identificadores de fontes, modelos de OCR, bibliotecas nativas ou fontes tipográficas. Assets, bibliotecas e fontes dos dois APKs ARM foram comparados byte a byte com o candidato .2: nenhuma diferença. A assinatura, a identidade Polaris e a revisão compilada foram verificadas pelo empacotador. Consulte [artefatos](artifact-check.json).

## Evidências

- [Reprodução com implementação anterior](before-tests.json): os três testes selecionados falharam antes da correção. A cópia antiga era removida antes de uma escrita malsucedida; corrupção e impossibilidade de releitura não impediam sucesso. A adaptação de teste introduziu apenas o resolvedor de arquivos, mantendo o corpo anterior do criador.
- [Testes direcionados](targeted-tests.json): 32 testes de armazenamento, coordenação e HTTP real local, mais os seis testes existentes de interoperabilidade do codec; todos passaram. XMLs JUnit estão nesta pasta.
- [Regressão completa](unit-comparison.json): 673 casos, 656 aprovações e as mesmas 17 falhas anteriores; zero casos ausentes, falhas novas ou testes ignorados. O Gradle termina com código1 por essas falhas anteriores, portanto a suíte não é totalmente verde.
- [Guardas do patch e empacotamento](host-tests.log): dez testes passaram. Todos os 199 arquivos do overlay foram comparados com a árvore efetivamente compilada, sem divergência.

Os testes cobrem falhas de escrita/fechamento/releitura, gzip truncado e bytes excedentes, corrupção, cancelamento, destino não vazio, retenção concorrente, falha de renomeação e substituição, resposta HTTP malsucedida, leitura HTTP interrompida e conflitos entre tentativas. A validação real de assinaturas pelo PackageManager não está coberta pelos testes HTTP, cuja fronteira de instalação é simulada.

## Limites e próximos aceites

Os quatro testes Android foram compilados, mas não executados até obter resultados: a instalação do APK alvo não retornou conclusão após cerca de dez minutos no emulador sem aceleração. A tentativa foi encerrada, sem repetição automática. [Registro](android-runtime.json). Nenhum desses quatro casos conta como aprovação ou falha de produto. Ela não equivale a testes com fornecedores SAF remotos, interrupção de energia, espaço físico esgotado, Android 14+ ou celulares ARM. SAF não oferece a mesma garantia de atomicidade da substituição local. Provedores precisam permitir leitura e renomeação para concluir backups em pastas. Provedores incompatíveis falham explicitamente, preservando as cópias anteriores.

Restauração no banco real, migração/fusão de bibliotecas, campos legados não aprovados no relatório de interoperabilidade e consentimento/instalação em lote continuam pendentes. Arquivos incompletos de uma queda do processo podem permanecer como `.pending`; não entram na retenção e não são considerados backups concluídos. Não se implementou instalação silenciosa em massa nem nova confiança automática.
