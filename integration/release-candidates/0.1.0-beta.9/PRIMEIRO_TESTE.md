# Primeiro teste — Polaris beta.9 / P20261104.4

1. Baixe somente o APK compatível com seu Android: ARM64 ou ARM32. Instale sobre a versão anterior e confira **Sobre → 0.1.0-beta.9 / P20261104.4**. Confirme biblioteca, downloads e progresso. Preserve a instalação existente se houver conflito de assinatura.
2. Em **Traduções**, prepare inglês → português se os recursos ainda não estiverem prontos. Essa preparação inicial precisa de internet; depois, o ML Kit permite traduzir offline.
3. Para o primeiro comparativo: **OCR PaddleOCR**, **faixas ligadas**, **DBNet desligado**, **tradutor ML Kit no dispositivo**, **Português (Brasil)**, **Anime Ace**, efeitos sonoros e edição avançada desligados.
4. Reabra uma tradução salva. Confira palavras com **Ç/ç**, como “AÇÃO”, “PROTEÇÃO” e “FORÇA”, e os acentos. A fonte escolhida vale para as traduções; tamanho e quebras são automáticos. Trocar a apresentação não exige refazer o OCR.
5. No trecho problemático de Solo Leveling: Ragnarok ou em outra obra, compare original e tradução: balões brancos, caixas escuras, painéis de missão, títulos, balões conectados e primeiras/últimas linhas. Confira nos modos vertical e paginado, com zoom. As faixas só atuam se a imagem individual for suficientemente alta.
6. Para comparar o OCR ML Kit com Paddle, mantenha as demais escolhas. Remova **somente a tradução salva** e traduza novamente. O original baixado permanece. Retraduzir uma frase usa o texto OCR salvo e não compara o reconhecimento da imagem.
7. Confira que ligar faixas desliga DBNet e vice-versa. DBNet exige inglês e Android/processo ARM64. Ao retirar um requisito, o dependente deve desligar; restaurá-lo deve apenas permitir sua escolha.
8. Em atualização futura disponível, teste queda de conexão, mudança de rede e sair/voltar à tela. A retomada deve conservar bytes do mesmo APK e conferir o hash antes de instalar. Instalar beta.9 não oferece baixar a própria beta.9; esse ensaio de atualização precisa de uma versão posterior publicada. Rascunhos são ignorados pelo atualizador. A beta.8 instalada pode exigir uma instalação manual inicial.

Ao relatar problemas, informe versão/revisão, modelo, Android, arquitetura quando conhecida, fonte/extensão, obra/capítulo, motor OCR, opções ligadas e passos para reproduzir. Uma captura do original e outra do resultado ajudam a distinguir texto ausente, tradução e encaixe. Não inclua credenciais ou dados pessoais.

## Preparar fontes e conferir o backup

- Antes de atualizar ou migrar, exporte e guarde uma cópia do backup original. Não sobrescreva essa cópia durante os testes.
- Abra **Navegar → Extensões → ⋮ → Preparar fontes**. Confira a explicação e a ciência de riscos; escolha/adicione um repositório HTTPS somente depois de revisar endereço e certificado.
- Quem migra pode importar o backup primeiro e escolher **fontes da biblioteca**. Revise a seleção e confirme o lote; acompanhe erros, cancelamento e repetição das falhas. O assistente não dá acesso a catálogos sem preparar as extensões e não garante disponibilidade das fontes.
- As extensões novas ficam dentro do Polaris. Ao voltar ao Mihon/Tachiyomi, será necessário instalar as fontes naquele app; o backup não inclui seus APKs.
- Confira favoritos, categorias, fonte, capítulos lidos, marcadores e posição após restauração. A migração real com banco/UI ainda está pendente; os testes automatizados validam codecs e campos comuns, não todos os forks. O campo Mihon `nextUpdate` não é preservado.
- A fila de extensões existe enquanto o processo do Polaris estiver aberto. Após encerramento pelo Android, reabra o assistente e prepare o que falta. Fontes já prontas são reconhecidas.
