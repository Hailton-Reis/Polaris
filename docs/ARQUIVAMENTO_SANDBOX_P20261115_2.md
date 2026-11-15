# Sandbox arquivada — P20261115.2

A sandbox de extensões foi retirada dos fontes compilados da beta.11, por decisão do usuário. Antes estava apenas desativada. O aviso único com “Estou ciente” e “Terei cuidado, relaxa” continua obrigatório antes das instalações/atualizações feitas no app.

## Arquivo recuperável

A branch [archive/sandbox-P20261115.1](https://github.com/Hailton-Reis/Polaris/tree/archive/sandbox-P20261115.1) aponta ao commit anterior `668c350401a4e6625df97877f2723bad44a43678`. Ela preserva o overlay Android e as evidências/fontes de fixtures. Para retomar a pesquisa, partir dessa revisão e aplicar a pilha de overlays ao checkout Android fixado, conforme os scripts daquele checkpoint; não reintroduzir esse código na candidata atual.

O [inventário](../integration/sandbox-removal/20261115/archive-inventory.json) registra caminhos, tamanhos e hashes de 32 arquivos retirados: 19 fontes de produção, oito arquivos de testes JVM, três classes de instrumentação, uma Activity de apoio debug e a fixture APK. Os scripts de criação da fixture e do teste de sessão também saíram da pasta ativa de scripts; são recuperáveis pela branch arquivada.

## Código ativo

- Removidos serviço isolado, Activity de login, declarações nos manifestos main/debug, executor, IPC, intermediário HTTP, bancos/cookies próprios e interfaces de preferências da sandbox.
- Removidas 32 mensagens exclusivas da sandbox em cada um dos dois idiomas. O aviso de quarentena antiga agora explica que uma aprovação libera execução normal dentro do Polaris.
- Retiradas as ramificações correspondentes de carregamento, capas, backup, WebView e detalhes da extensão; não há flag que reative o executor.
- Mantida a revisão de seleções experimentais antigas antes da execução normal. Chaves antigas de seleção/quarentena continuam apenas para migração e preservação de decisões; arquivos privados de usuários não são apagados nem credenciais copiadas automaticamente.
- Verificações de assinatura/integridade, inspeção preventiva e revisão de confiança continuam no fluxo normal. O aviso informa o risco, sem oferecer isolamento às extensões.
- O worker independente de OCR e o teste de idioma automático foram preservados; o teste de idioma foi movido para seu pacote de tradução.

## Validação e limites

Resultados da compilação, comparação dos casos e inspeção dos artefatos constam na [evidência filtrada](../integration/sandbox-removal/20261115/README.md). A retirada arquiva 94 casos JVM exclusivos do executor; a comparação exige todos os demais casos anteriores, sem contabilizar os arquivados como aprovados nesta candidata.

Não foi gerado outro APK nem publicada uma Release nesta revisão. A redução exata do APK será medida na distribuição; bytes de fontes removidos não equivalem ao tamanho final instalado. As quatro frentes ativas seguem sendo armazenamento, backups, leitura e distribuição. Conta/nuvem continuam adiadas.
