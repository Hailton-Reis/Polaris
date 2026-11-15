# Pausa da sandbox e aviso de extensões — P20261114.4

## Decisão atual

A pedido do usuário, toda a frente de sandbox está pausada e deixa de bloquear a beta.11. O foco ativo passa a ser armazenamento, backups, leitura e distribuição. Conta/login Google/nuvem continuam adiados. Os testes pessoais ficam para a consolidação final.

O código experimental foi preservado para possível retomada. A política de produção está desligada, o seletor de ativação não aparece e o ViewModel não permite ativá-lo. Serviço isolado e tela de login da sandbox estão desabilitados no manifesto. Três classes de instrumentação exclusivas da sandbox estão explicitamente ignoradas durante a pausa; os contratos JVM preservados continuam sendo verificados. Não há novas adaptações de controles, OAuth/Cloudflare ou novels isoladas nesta etapa.

## Aviso único

Antes da primeira instalação/atualização iniciada no Polaris, um aviso explica que extensões são código de terceiros, podem acessar dados/recursos disponíveis ao app e enviar informações pela internet. A versão atual não oferece isolamento para elas. O texto recomenda fontes confiáveis e informa que instalação/uso são por conta e risco da pessoa.

Ao final ficam as duas caixas solicitadas:

- Estou ciente
- Terei cuidado, relaxa

Continuar fica desabilitado até marcar ambas. Voltar/tocar fora não fecha o aviso e não confirma nada. O aceite só é registrado ao continuar. Depois disso, outras extensões, atualizações e lotes usam a mesma decisão local, sem repetir o aviso geral. Fechar o processo antes de confirmar não autoriza instalação.

O fluxo cobre APKs pela lista de extensões (incluindo toque longo, atualização individual e todas), preparação/repetição em lote e plugins de novels. Os gerentes também recusam iniciar essas instalações sem o aceite, inclusive chamadas em segundo plano. A coleta de metadados de catálogos não equivale a instalar código. Instalações feitas por fora do Polaris não podem ser interceptadas por esse diálogo.

O aceite é estado interno local: não é exportado em backup nem pode ser pré-autorizado por um backup importado. Volta a ser necessário após limpar dados, reinstalar sem os dados ou trocar de aparelho. Assinaturas, integridade, revisão de repositórios e quarentena por achados continuam independentes; esse aviso não concede confiança automática a código desconhecido.

## Seleções experimentais anteriores

Uma extensão marcada para isolamento antes da pausa não é carregada automaticamente no processo comum enquanto o aviso não foi aceito. Ela aguarda revisão com fontes inativas. Abrir as telas de extensões/preparação/detalhes oferece o mesmo aviso; após aceite, as seleções experimentais são retiradas e as extensões são recarregadas no modo normal. O código não troca de modo em silêncio.

Os dados de preferências/cookies experimentais continuam no armazenamento separado. Credenciais não são copiadas automaticamente para o modo normal; pode ser necessário configurar a fonte novamente. Nada apaga biblioteca, progresso, arquivos importados ou backups existentes.

## Tamanho do aplicativo

Pausar e desativar preservando código não representa remoção desses bytes do APK. A referência interna P20261113.3 mede 272.970.356 bytes: 192.659.644 bytes compactados estão em bibliotecas nativas (70,6%). Isso não mede a contribuição da sandbox, nem representa o candidato atualizado. Uma diferença real de tamanho requer comparar pacotes equivalentes na etapa de distribuição. Não houve novo APK do app ou Release nesta revisão.

## Validação e limites

Os testes JVM exercitam o aceite, combinações das caixas, gravação/recusa, controle antes da ação, chave real de preferências, exportação/importação de backup e transição de execução durante a pausa. A interface Compose e os caminhos de instalação são compilados. O manifesto mesclado é inspecionado para serviço/tela desabilitados.

Dois cenários Android de preferências nativas/componentes foram preparados, mas não executados nesta rodada. Não há aceite visual/interação real de instalação ou promessa de proteção equivalente ao isolamento. O aviso informa riscos; não bloqueia o comportamento de uma extensão já autorizada em execução compartilhada.

[Evidências filtradas](../integration/extension-risk-notice/20261114/README.md) · [Checklist ativo](BETA11_CHECKLIST.md).
