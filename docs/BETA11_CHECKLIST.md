# Beta.11 — checklist de consolidação

Base pública: beta.10/código111. Base de engenharia: P20261112.1, commit 6952e5e.
Este checklist acompanha o trabalho autorizado em 13/11. Não é uma declaração de lançamento.

| Frente | Estado |
| --- | --- |
| Jornada, XP, conquistas e grimórios | Implementados no checkpoint anterior |
| Login de fontes isoladas | Primeira implementação P20261113.1; validação Android/real pendente |
| Sandbox: controles dinâmicos, provedores externos/OAuth e novels | Pendente |
| Biblioteca, fontes reais e backups entre leitores | Limpeza e gravação de backups verificadas em JVM; ida/volta e aceite completo pendentes |
| Leitura, OCR e tradução nos aparelhos | Pendente, incluindo diagnóstico do A12 |
| Armazenamento | Proteção de espaço na importação implementada nesta candidata; deduplicação/recuperação e medição física pendentes |
| Atualização beta.10 → beta.11 e distribuição não depurável | Pendente |

Ordem: autenticação/sandbox → biblioteca/backups → armazenamento/leitura → teste ARM → pacote.
Não repetir funcionalidades já entregues com base nos documentos históricos. Não transformar
resultado de teste de componentes em aprovação da próxima beta inteira.

A [primeira revisão](LOGIN_E_ARMAZENAMENTO_P20261113_1.md) e a [proteção de backups P20261113.2](../integration/backup-safety/20261113/README.md) registram código, testes e limites.
A publicação não foi iniciada; a beta.10 continua sendo a versão pública.
