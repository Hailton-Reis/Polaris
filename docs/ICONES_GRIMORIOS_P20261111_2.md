# Coleção de grimórios — P20261111.2

Registro do primeiro ensaio visual. O refinamento e a ampliação das conquistas seguem na [revisão P20261112.1](CONQUISTAS_GRIMORIOS_P20261112_1.md).

Beta.11/código112 em desenvolvimento, posterior a fdc768e. A beta.10 pública permanece inalterada. Esta etapa troca as artes/nomes de ícones e cores de fundo; não altera a implementação das sessões HTTP ou da biblioteca.

## Progressão visual

O Grimório Polaris usa livro azul noturno e estrela do norte. A alternativa de três folhas usa couro verde e trevo esmeralda. O grimório de quatro folhas, chamado Amado pela mana, usa marfim, ouro e aura luminosa. O de cinco folhas é negro com magia vermelha/violeta. As quatro ilustrações foram geradas como imagens e preservadas em [originais e proveniência](../design/polaris-grimoires/20261111/README.md).

Os recursos Android de 512×512 somam 443.012 bytes. As margens adaptativas existentes são mantidas. O tratamento monocromático do sistema usa a transparência da imagem e não preserva toda a cor da ilustração; aceite de máscaras/ícones temáticos em Android recente continua pendente.

## Recompensas e compatibilidade

Os marcos continuam em 900/4.500/9.000 pontos, com original livre, sem gasto e com desbloqueios permanentes. A escolha anterior continua na mesma posição da coleção. Enum, chaves de preferências, nomes de aliases e limites não mudam. O backup mantém o formato existente e os temas Boreal/Aurora/Âmbar continuam disponíveis.

Esta etapa não altera a lógica de recompensa, assinatura, identificador do aplicativo, manifestos, fontes/extensões, OCR, tradução, dependências ou esquemas SQL/Protobuf. Os arquivos de arte antigos permanecem arquivados na engenharia.

## Verificação

A compilação e os testes específicos desta etapa ficam registrados em [evidências de grimórios](../integration/grimoire-icons/20261111/README.md). Os 872 testes JVM e 35 Android da etapa de sessões/guardiões são uma [linha de base anterior](../integration/sessions-icons/20261111/README.md), não uma nova rodada declarada para estes recursos. A validação atual deve conferir os novos desenhos e a preservação da seleção/desbloqueios.

Continuam pendentes login por WebView, fontes/contas reais, fluxo completo leitor/downloads, aparelhos ARM e ida/volta por banco/interface de leitores externos.
