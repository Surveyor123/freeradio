# FreeRadio — Complemento para o NVDA

FreeRadio é um complemento completo de rádio pela Internet, podcasts e audiolivros para o leitor de ecrã NVDA. O que começou como uma forma simples de transmitir estações de rádio pela Internet tornou-se um centro de escuta completo e totalmente acessível — cada ecrã, caixa de diálogo e controlo é concebido de raiz para uso com teclado e leitor de ecrã, sem necessidade de rato em momento algum.

## O Que o FreeRadio Pode Fazer

- **Rádio pela Internet** — Navegue e pesquise mais de 50 000 estações no diretório [Radio Browser](https://www.radio-browser.info/), com resultados complementados por TuneIn e iHeartRadio. Guarde favoritos, reordene-os e aceda diretamente a qualquer um deles com um atalho de teclado global a partir de qualquer parte do Windows — veja [Diretório Radio Browser](#diretório-radio-browser) e [Favoritos](#favoritos).
- **Podcasts** — Subscreva qualquer feed RSS/Atom, ou pesquise no diretório de podcasts da Apple e pré-visualize episódios antes de subscrever. A posição de reprodução é guardada automaticamente e retoma onde ficou — veja [Podcasts](#podcasts).
- **Audiolivros** — Pesquise e transmita ou descarregue livros de duas fontes: [GETEM](https://getem.boun.edu.tr/), a biblioteca digital da Universidade de Boğaziçi para pessoas com deficiência visual, e [LibriVox](https://librivox.org/), o projeto de audiolivros de domínio público lidos por voluntários (sem necessidade de conta), com retoma automática em obras de várias partes — veja [Audiolivros (GETEM e LibriVox)](#audiolivros-getem-e-librivox).
- **Gravação** — Grave o que está a tocar instantaneamente, capture automaticamente uma única música quando começa e termina, ou agende gravações únicas ou recorrentes — tudo sem interromper a reprodução — veja [Gravação](#gravação).
- **Time-Shift (recuar na rádio em direto)** — Pause e recue numa estação em direto como um DVR, e depois volte ao direto sempre que quiser — veja [Time-Shift (Recuar na Rádio em Direto)](#time-shift-recuar-na-rádio-em-direto).
- **Reconhecimento musical e músicas gostadas** — Identifique faixas sem metadados usando reconhecimento baseado em Shazam, guarde músicas gostadas num ficheiro de texto e consulte as suas letras — veja [Reconhecimento Musical](#reconhecimento-musical) e [Músicas Gostadas](#músicas-gostadas).
- **Perfis e efeitos de áudio** — Guarde definições separadas de volume, efeitos, equalizador e velocidade de reprodução por estação, por podcast ou por audiolivro, e aplique efeitos em tempo real (Chorus, Reverb, reforços de equalizador e mais) através do motor BASS — veja [Perfil de Áudio da Estação](#perfil-de-áudio-da-estação).
- **Espelhamento de áudio** — Envie o mesmo fluxo para dois dispositivos de saída de áudio em simultâneo, como colunas e auscultadores ao mesmo tempo — veja [Espelho de Áudio](#espelho-de-áudio).
- **Modo Obligato (música de fundo)** — Reproduza em ciclo uma estação favorita escolhida discretamente em segundo plano, no seu próprio dispositivo de saída e volume, independentemente do que estiver (ou não) a tocar como média principal — veja [Modo de Música de Fundo (Obligato)](#modo-de-música-de-fundo-obligato).
- **Temporizadores** — Agende o início da reprodução de uma estação favorita, ou agende a paragem da reprodução, a uma hora específica — veja [Temporizador](#temporizador).
- **Acesso profundo por teclado e braille** — Todas as funcionalidades são acessíveis inteiramente pelo teclado, com atalhos globais que funcionam a partir de qualquer parte do Windows, teclas de atalho diretas para estações favoritas individuais, e saída braille opcional para todas as notificações faladas do FreeRadio.

## Diretório Radio Browser

FreeRadio utiliza a base de dados aberta [Radio Browser](https://www.radio-browser.info/) para o seu catálogo de estações. O Radio Browser é um diretório gratuito gerido pela comunidade com mais de 50.000 estações de rádio online de todo o mundo. Não é necessário registo e a API é aberta a todos.

Cada estação inclui endereço, país, género, idioma e bitrate; as estações são classificadas por votos dos utilizadores. O FreeRadio liga-se à API através de servidores espelho localizados na Alemanha, Países Baixos e Áustria; se um servidor estiver inacessível, muda automaticamente para o seguinte.

Para manter o navegador rápido e evitar sobrecarregar a API a cada pesquisa ou mudança de país, o FreeRadio mantém uma cache local do catálogo de estações em disco. Esta cache é atualizada automaticamente em segundo plano de forma periódica, pelo que a lista apresentada está normalmente já atualizada sem qualquer ação da sua parte. Também pode forçar uma nova sincronização imediata a qualquer momento com o botão **Atualizar Lista de Estações** — consulte Navegador de Estações abaixo.

## Adicionar uma Estação ao Radio Browser

Se a estação que procura não estiver no diretório Radio Browser, pode submetê-la em [https://www.radio-browser.info/add](https://www.radio-browser.info/add). Não é necessária conta nem registo.

Preencha o formulário da página:

- **URL da transmissão (Stream URL)** *(obrigatório)* — o endereço direto da transmissão de áudio, terminado em `.mp3`, `.aac`, `.ogg` ou semelhante. Não é o endereço do site da estação, mas sim o endereço bruto da transmissão que colaria num leitor multimédia. A maioria das estações publica o URL da transmissão no seu site ou na secção "Ouvir em direto".
- **Nome da estação** *(obrigatório)* — o nome da estação tal como deve aparecer no diretório.
- **Página inicial** — o endereço do site da estação.
- **País e idioma** — selecione o país de emissão e o idioma a partir das listas pendentes.
- **Etiquetas** — palavras-chave de género ou tema separadas por vírgulas, por exemplo `notícias`, `jazz`, `clássica`. São utilizadas para pesquisa e filtragem.
- **URL do logótipo** — uma ligação direta à imagem do logótipo da estação, se disponível.

Após a submissão, a estação é revista e adicionada ao diretório público. Uma vez aceite, aparecerá automaticamente nas pesquisas e nas listagens por país do FreeRadio, uma vez que o diretório é atualizado a partir da API em tempo real.

## Requisitos

- NVDA 2024.1 ou posterior
- Windows 10 ou posterior
- Ligação à Internet

## Instalação

Descarregue o ficheiro `.nvda-addon`, prima Enter sobre ele e reinicie o NVDA quando solicitado.

## Atalhos de Teclado

Todos os atalhos podem ser reatribuídos em Menu NVDA → Preferências → Definir comandos → FreeRadio. Estes atalhos funcionam em qualquer lugar, independentemente da janela que estiver em foco.

| Atalho | Função | Descrição |
|---|---|---|
| `Ctrl+Win+R` | Abrir navegador de estações | Abre a janela do navegador se estiver fechada, ou traz-a para primeiro plano se já estiver aberta. |
| `Ctrl+Win+P` | Pausar / retomar | Pausa a estação atual se estiver a reproduzir; retoma se estiver em pausa. Se nada estiver a reproduzir, inicia a última estação ou abre a lista de favoritos conforme a definição. Premir duas vezes rapidamente salta diretamente para um separador à escolha. Premir três vezes pode desencadear uma ação separada conforme a definição. |
| `Ctrl+Win+S` | Parar | Para completamente a estação atual e reinicia o leitor. |
| `Ctrl+Win+→` | Próximo favorito | Avança para a próxima estação na lista de favoritos. Volta ao início no final da lista. |
| `Ctrl+Win+←` | Favorito anterior | Recua para a estação anterior na lista de favoritos. Salta para o fim quando está no início. |
| `Ctrl+Win+↑` | Aumentar volume | Aumenta o volume em 10; máximo 100. |
| `Ctrl+Win+↓` | Diminuir volume | Diminui o volume em 10; mínimo 0. |
| `Ctrl+Win+V` | Adicionar aos favoritos | Adiciona a estação em reprodução à lista de favoritos. Anuncia se a estação já está na lista. |
| `Ctrl+Win+I` | Informação da estação | Anuncia o nome da estação em reprodução. Premir duas vezes mostra detalhes como país, género e bitrate numa caixa de diálogo. Premir três vezes copia as informações da faixa atual (metadados ICY) para a área de transferência, se disponíveis; se não existirem metadados, inicia o reconhecimento musical Shazam. Premir quatro vezes força o reconhecimento musical em caso de metadados ICY incorretos. |
| `Ctrl+Win+M` | Espelho de áudio | Espelha a transmissão atual para um dispositivo de saída de áudio adicional em simultâneo. Prima novamente para parar o espelhamento. |
| `Ctrl+Win+Shift+M` | Modo Obligato (música de fundo) | Reproduz em ciclo uma estação favorita escolhida discretamente em segundo plano, no seu próprio dispositivo de saída e volume, independentemente do que estiver a tocar no leitor principal. A primeira pressão abre uma caixa de diálogo para escolher a estação, o dispositivo de saída e o volume relativo. Prima novamente para o parar. |
| `Ctrl+Win+E` | Gravação instantânea | Prima uma vez para iniciar a gravação da estação atual; prima novamente para parar. Prima **duas vezes** para iniciar uma **gravação de canção** — o ficheiro recebe o nome da faixa atual e a gravação para automaticamente quando a faixa muda. Prima duas vezes novamente enquanto uma gravação de canção está ativa para terminá-la antecipadamente. A reprodução continua sem interrupção em todos os modos de gravação. Disponível apenas em estações que difundem metadados ICY. |
| `Ctrl+Win+W` | Abrir pasta de gravações | Abre a pasta com os ficheiros gravados no Explorador de Ficheiros. |
| `Ctrl+Win+J` | Retrocesso do time-shift | Retrocede a rádio em direto 15 segundos. A primeira pressão entra no modo time-shift; cada pressão adicional retrocede mais 15 segundos, até ao limite do buffer (~10 minutos). Requer que o buffer de time-shift esteja ativado nas Definições. |
| `Ctrl+Win+K` | Avanço rápido do time-shift | Avança 15 segundos enquanto está em modo time-shift. Ao atingir a margem do direto, a reprodução regressa automaticamente ao direto e este comando não tem efeito até retroceder novamente. |
| `Ctrl+Win+T` | Alternar buffer de time-shift | Ativa ou desativa o buffer de time-shift instantaneamente, refletindo a caixa de verificação nas Definições. Ao desativar, regressa imediatamente ao direto se estiver em modo time-shift e interrompe a captura em segundo plano. |
| *(não atribuído)* | Alternar silenciamento de notificações | Ativa ou desativa o silenciamento de notificações em tempo real. Pode atribuir uma combinação de teclas em Menu NVDA → Preferências → Definir comandos → FreeRadio. |
| *(não atribuído)* | Reproduzir estação favorita diretamente | Cada estação da lista de favoritos aparece como uma entrada separada em Menu NVDA → Preferências → Definir comandos → **FreeRadio Stations**. Atribua um atalho de teclado a qualquer estação para a iniciar imediatamente a partir de qualquer lugar, sem abrir o navegador. |

Os atalhos seguinte/anterior apenas navegam na lista de favoritos; não funcionam com a lista de todas as estações. Quando uma lista está em foco na janela do navegador, as teclas de seta esquerda e direita têm a mesma função — consulte Atalhos na Caixa de Diálogo.

## Navegador de Estações

O FreeRadio adiciona também um submenu **FreeRadio** ao menu Ferramentas do NVDA, a partir do qual pode abrir diretamente o Navegador de Estações e as Definições do FreeRadio.

A janela aberta com `Ctrl+Win+R` contém cinco separadores: Todas as Estações, Favoritos, Gravação, Temporizador e Músicas Gostadas. Pode navegar entre separadores com `Ctrl+Tab`.

Quando o separador Todas as Estações abre, as 1.000 estações mais votadas são carregadas automaticamente a partir do Radio Browser. Selecionar um país na lista pendente atualiza a lista para mostrar as estações desse país. Escrever no campo de pesquisa executa automaticamente uma pesquisa completa na base de dados Radio Browser em simultâneo por nome, país e género (com um atraso de 500 ms após a última tecla premida); não é necessário premir Enter nem qualquer botão.

A lista pendente **Dispositivo de saída** na parte inferior da janela do navegador — fora dos separadores — lista todos os dispositivos de saída de áudio reconhecidos pelo BASS. Selecionar um dispositivo redireciona imediatamente o áudio para ele e guarda a escolha permanentemente; o mesmo dispositivo é utilizado automaticamente na próxima sessão. Se o dispositivo selecionado não estiver ligado, o complemento reverte automaticamente para a predefinição do sistema. Este controlo só é funcional quando o backend BASS está ativo.

Os controlos **Volume** (0–200) e **Efeitos** na mesma área podem ser ajustados em qualquer altura com a janela aberta. Na lista de Efeitos, é possível ativar simultaneamente Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost e EQ: Vocal Boost; as alterações são aplicadas à transmissão ativa instantaneamente. Cada efeito também pode ser ativado ou desativado instantaneamente com `Ctrl+1` a `Ctrl+0`, sem largar o teclado — consulte Atalhos de Efeitos abaixo. Estes controlos só são totalmente funcionais quando o backend BASS está ativo.

Quando um ou mais efeitos EQ estão ativos, surge automaticamente um **controlo de ganho** para cada banda ativa. O ganho pode ser ajustado entre −15 dB e +15 dB; os valores predefinidos são Graves +9 dB, Agudos +9 dB e Vocal +6 dB. Os controlos só aparecem para as bandas EQ selecionadas e ocultam-se automaticamente quando o efeito é desmarcado. Os valores são guardados permanentemente e restaurados na sessão seguinte.

O botão **Reproduzir/Pausar** encontra-se também na parte inferior da janela. Se nenhuma estação estiver a reproduzir, inicia a estação selecionada; se uma estação já estiver em reprodução, pausa a reprodução.

O botão **Atualizar Lista de Estações** sincroniza imediatamente o catálogo local de estações com a API do Radio Browser, em vez de esperar pela atualização periódica em segundo plano. Enquanto a atualização decorre, o botão fica desativado e o NVDA anuncia que está a decorrer uma atualização; se voltar a premi-lo antes de a atualização atual terminar, o NVDA informa que já está uma em curso. Assim que a atualização termina, o NVDA anuncia que a lista de estações foi atualizada e os resultados de pesquisa ou a listagem de país atualmente apresentados são atualizados automaticamente para refletir os novos dados.

Quando uma estação está selecionada na lista, o botão **Detalhes da Estação** apresenta informações como país, idioma, género, formato, bitrate, website e URL da transmissão numa caixa de diálogo separada. Cada campo aparece na sua própria caixa de texto só de leitura; pode mover-se entre campos com Tab e copiar todas as informações para a área de transferência de uma só vez com o botão **Copiar tudo para a área de transferência**. Este botão está disponível nos separadores Todas as Estações e Favoritos.

### Menu de Contexto da Estação

Clique com o botão direito numa estação na lista Todas as Estações ou Favoritos, ou selecione-a e prima a tecla Aplicações ou `Shift+F10`, para abrir um menu de contexto com ações rápidas:

- **Detalhes da Estação** — igual ao botão Detalhes da Estação descrito acima.
- **Adicionar aos Favoritos** *(separador Todas as Estações)* / **Eliminar Estação** *(separador Favoritos)*.
- **Mudar Nome da Estação** *(separador Favoritos)* — igual a `F9`.
- **Guardar Perfil de Áudio para Esta Estação** / **Limpar Perfil de Áudio** *(separador Favoritos)* — ver Perfil de Áudio da Estação.
- **Testar URL** — verifica se a transmissão da estação selecionada está atualmente acessível, sem iniciar a reprodução, e anuncia o resultado (acessível, ou o motivo da falha, como um erro HTTP ou um tempo limite de rede).

Apenas os itens relevantes para o separador e seleção atuais são apresentados como disponíveis.

### Atalhos na Caixa de Diálogo

As teclas seguintes funcionam apenas quando a janela do Navegador de Estações está ativa.

### Teclas F

| Atalho | Função | Descrição |
|---|---|---|
| `F1` | Guia de ajuda | Abre o ficheiro de ajuda do complemento no browser predefinido. É pesquisado primeiro o guia para o idioma do NVDA ativo; se não for encontrado, abre o guia predefinido. |
| `F2` | Informação da estação | Anuncia o nome da estação em reprodução. Premir duas vezes mostra detalhes como país, género e bitrate numa caixa de diálogo. Premir três vezes copia as informações da faixa atual (metadados ICY) para a área de transferência, se disponíveis; se não existirem metadados, inicia o reconhecimento musical Shazam. Premir quatro vezes força o reconhecimento musical em caso de metadados ICY incorretos. |
| `F3` | Estação anterior | Recua para a estação anterior no separador Todas as Estações ou Favoritos e inicia a reprodução imediatamente. Salta para o fim quando está no início da lista. |
| `F4` | Próxima estação | Avança para a próxima estação no separador Todas as Estações ou Favoritos e inicia a reprodução imediatamente. Volta ao início no final da lista. |
| `F5` | Diminuir volume | Diminui o volume em 10 (mínimo 0). |
| `F6` | Aumentar volume | Aumenta o volume em 10 (máximo 200). |
| `F7` | Pausar / retomar | Pausa se uma estação estiver a reproduzir; retoma se estiver em pausa e os média estiverem carregados. |
| `F8` | Parar | Para completamente a estação atual e reinicia o leitor. |
| `F9` | Renomear | Abre a caixa de diálogo de renomeação para a estação em foco no separador Favoritos. |

### Atalhos de Lista e Navegação

| Atalho | Função | Descrição |
|---|---|---|
| `→` | Próxima estação | Quando a lista Todas as Estações ou Favoritos está em foco, avança para a próxima estação e reproduz-a imediatamente. Volta ao início no final da lista. |
| `←` | Estação anterior | Quando a lista Todas as Estações ou Favoritos está em foco, recua para a estação anterior e reproduz-a imediatamente. Salta para o fim quando está no início. |
| `Enter` | Reproduzir | Quando a lista Todas as Estações ou Favoritos está em foco, inicia a reprodução da estação selecionada imediatamente. Muda para a estação selecionada mesmo que outra estação já esteja a reproduzir. |
| `Espaço` | Reproduzir / Pausar | Pausa se uma estação estiver a reproduzir; caso contrário, inicia a reprodução da estação selecionada. |
| `Ctrl+Tab` | Próximo separador | Muda para o próximo separador (Todas as Estações → Favoritos → Gravação → Temporizador → Músicas Gostadas). |
| `Ctrl+Shift+Tab` | Separador anterior | Volta ao separador anterior. |
| `Escape` | Ocultar | Oculta a janela; o complemento continua a reproduzir em segundo plano. |

### Atalhos de Volume

| Atalho | Função | Descrição |
|---|---|---|
| `Ctrl+↑` | Aumentar volume | Aumenta o volume em 10. Só funciona com a janela do navegador aberta. |
| `Ctrl+↓` | Diminuir volume | Diminui o volume em 10. Só funciona com a janela do navegador aberta. |

### Atalhos de Efeitos

| Atalho | Função | Descrição |
|---|---|---|
| `Ctrl+1` | Alternar Chorus | Ativa ou desativa o efeito Chorus e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+2` | Alternar Compressor | Ativa ou desativa o efeito Compressor e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+3` | Alternar Distortion | Ativa ou desativa o efeito Distortion e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+4` | Alternar Echo | Ativa ou desativa o efeito Echo e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+5` | Alternar Flanger | Ativa ou desativa o efeito Flanger e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+6` | Alternar Gargle | Ativa ou desativa o efeito Gargle e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+7` | Alternar Reverb | Ativa ou desativa o efeito Reverb e aplica-o instantaneamente à transmissão ativa. |
| `Ctrl+8` | Alternar EQ: Bass Boost | Ativa ou desativa a banda EQ: Bass Boost e aplica-a instantaneamente à transmissão ativa. |
| `Ctrl+9` | Alternar EQ: Treble Boost | Ativa ou desativa a banda EQ: Treble Boost e aplica-a instantaneamente à transmissão ativa. |
| `Ctrl+0` | Alternar EQ: Vocal Boost | Ativa ou desativa a banda EQ: Vocal Boost e aplica-a instantaneamente à transmissão ativa. |

Cada atalho reflete marcar ou desmarcar o item correspondente na lista **Efeitos**: o NVDA anuncia se o efeito foi ativado ou desativado, a alteração é guardada automaticamente e o controlo de ganho dessa banda (se aplicável) aparece ou desaparece em conformidade. Disponível apenas quando o backend BASS está ativo.

### Atalhos da Tecla Alt

| Atalho | Função | Descrição |
|---|---|---|
| `Alt+R` | Ir para o campo de pesquisa | Move o foco para a caixa de texto de pesquisa. Pesquisa nome, país e género em simultâneo à medida que escreve. |
| `Alt+V` | Adicionar / remover favorito | Adiciona a estação selecionada aos favoritos; remove-a se já estiver na lista. |
| `Alt+1` | Todas as Estações | Muda para o separador Todas as Estações. |
| `Alt+2` | Favoritos | Muda para o separador Favoritos. |
| `Alt+3` | Gravação | Muda para o separador Gravação. |
| `Alt+4` | Temporizador | Muda para o separador Temporizador. |
| `Alt+5` | Músicas Gostadas | Muda para o separador Músicas Gostadas. |
| `Alt+K` | Fechar | Fecha a janela; o complemento continua a reproduzir em segundo plano. |

## Favoritos

A lista de favoritos é uma coleção pessoal de estações guardada permanentemente. Para adicionar uma estação, selecione-a na lista e prima o botão Adicionar aos Favoritos ou use o atalho `Alt+V`. O mesmo atalho remove uma estação que já esteja na lista quando está selecionada.

Os favoritos podem ser reproduzidos com `Ctrl+Win+→` e `Ctrl+Win+←`; estes atalhos funcionam mesmo quando a janela do navegador não está aberta.

Para eliminar uma estação da lista de favoritos, selecione-a e prima o botão **Eliminar Estação** ou a tecla `Delete`. Após a eliminação, o foco e a seleção movem-se automaticamente para a estação seguinte. Se a estação eliminada era a última, o foco vai para a estação anterior. Se a lista ficar vazia, o foco vai para o botão Reproduzir.

### Exportar e Importar Favoritos

O separador Favoritos inclui dois botões para fazer cópias de segurança e restaurar a sua lista de estações:

**Exportar Favoritos…** — guarda toda a sua lista de favoritos num ficheiro. Uma caixa de diálogo permite-lhe escolher entre dois formatos:
- **JSON** (`.json`) — uma cópia de segurança completa que preserva nomes de estações, URLs de transmissão e todos os metadados. Recomendado para restaurar a sua lista mais tarde ou movê-la para outro computador.
- **Lista de reprodução M3U** (`.m3u`) — um formato de lista de reprodução padrão compatível com a maioria dos leitores de multimédia e aplicações de rádio. Note que o M3U não armazena todos os metadados das estações, pelo que restaurar a partir de M3U pode resultar em menos detalhes do que uma cópia de segurança JSON.

**Importar Favoritos…** — carrega estações de um ficheiro JSON ou M3U previamente exportado. Após selecionar o ficheiro, é perguntado como adicionar as estações:
- **Sim (Intercalar)** — adiciona as estações importadas à sua lista existente sem remover os favoritos atuais. Estações duplicadas não são adicionadas duas vezes.
- **Não (Substituir)** — limpa completamente a sua lista de favoritos atual e substitui-a pelo conteúdo do ficheiro importado.
- **Cancelar** — regressa ao navegador sem efetuar quaisquer alterações.

Após uma importação bem-sucedida, a lista de favoritos, a lista de estações de gravação agendada e a lista de estações do temporizador são todas atualizadas automaticamente.

### Reordenar Favoritos

Com uma estação selecionada no separador Favoritos, prima `vírgula` para entrar no modo de mover — ouvirá um sinal sonoro. Navegue até à posição pretendida com as teclas de seta e prima `vírgula` novamente. A estação é colocada na posição escolhida e a nova ordem é guardada imediatamente. Premir `vírgula` novamente na mesma posição cancela a operação.

### Atalhos de Teclado Diretos para Estações Favoritas

Cada estação da lista de favoritos é registada como um script separado na caixa de diálogo Definir Comandos do NVDA, na categoria **FreeRadio Stations**. Pode atribuir qualquer atalho de teclado a qualquer estação e premi-lo a partir de qualquer lugar — sem necessidade de abrir a janela do navegador.

Para atribuir um atalho:

1. Abra Menu NVDA → Preferências → Definir comandos.
2. Expanda a categoria **FreeRadio Stations**.
3. Encontre a estação pelo nome, selecione-a e prima **Adicionar**.
4. Prima a combinação de teclas pretendida e confirme.

O atalho inicia a estação imediatamente. Se a estação for removida dos favoritos, a sua entrada desaparece da categoria e qualquer atalho atribuído é automaticamente removido pelo NVDA. Quando uma nova estação é adicionada aos favoritos, aparece na categoria de imediato — não é necessário reabrir a caixa de diálogo Definir Comandos.

### Adicionar Estação Personalizada

Para adicionar uma estação que não esteja no Radio Browser, utilize o botão Adicionar Estação Personalizada. Na caixa de diálogo que aparece, introduza o nome da estação e o URL da transmissão para a adicionar diretamente aos favoritos. As estações personalizadas podem ser reproduzidas e reordenadas tal como qualquer outro favorito.

Estão disponíveis dois botões adicionais nesta caixa de diálogo:

- **Testar URL** — verifica o URL da transmissão introduzido antes de adicionar a estação e anuncia se está acessível. Útil para detetar um erro de escrita ou uma ligação inválida antes de esta ficar na sua lista de favoritos.
- **Adicionar ao diretório Radio Browser…** — abre a [página de submissão do Radio Browser](https://www.radio-browser.info/add) no navegador predefinido, para que possa partilhar a estação com a comunidade Radio Browser assim que confirmar que funciona. Consulte Adicionar uma Estação ao Radio Browser acima para saber o que o formulário de submissão espera.

### Perfil de Áudio da Estação

O separador Favoritos inclui dois botões para gerir as definições de áudio por estação:

**Guardar Perfil de Áudio para Esta Estação** — guarda o nível de volume atual, os efeitos ativos e os valores de ganho EQ como um perfil associado a essa estação específica. Sempre que essa estação iniciar a reprodução, o volume, efeitos e ganho guardados são automaticamente aplicados, substituindo as predefinições globais.

**Limpar Perfil de Áudio** — remove o perfil de áudio guardado da estação selecionada. Após limpar, a estação reverte para as definições globais de volume, efeitos e ganho EQ. Este botão só está ativo quando a estação selecionada já tem um perfil guardado.

Ambos os botões estão localizados abaixo da lista de favoritos e só estão ativos quando uma estação da lista está selecionada.

## Reconhecimento Musical

Premir `Ctrl+Win+I` três vezes ativa o reconhecimento musical baseado em Shazam para a transmissão em reprodução. O reconhecimento só inicia quando não existem metadados ICY (informações de faixa difundidas pela estação) disponíveis; se existirem metadados, estes são copiados para a área de transferência.

O reconhecimento funciona da seguinte forma: uma curta amostra de áudio é capturada da transmissão usando ffmpeg, o algoritmo de identificação Shazam é aplicado e o resultado é enviado para os servidores Shazam. Se o reconhecimento for bem-sucedido, o título da faixa, artista, álbum e ano de lançamento são anunciados pelo NVDA e copiados automaticamente para a área de transferência. Se a opção **Guardar músicas gostadas em ficheiro de texto** estiver ativa, o resultado do reconhecimento é também adicionado ao ficheiro `likedSongs.txt`.

**Feedback sonoro:** Dois sinais sonoros ascendentes indicam o início do reconhecimento e dois descendentes indicam o fim. Um sinal sonoro curto soa a cada 2 segundos enquanto o processo está em execução.

**Requisito:** É necessário `ffmpeg.exe`. Um `ffmpeg.exe` colocado na pasta do complemento é utilizado automaticamente; se estiver noutro local, o caminho pode ser definido nas Definições. Descarregue o ffmpeg em [ffmpeg.org](https://ffmpeg.org/download.html).

**Uma nota sobre estações que inserem anúncios:** algumas estações reproduzem um anúncio curto em cada nova ligação feita à sua transmissão, separado da emissão que já está a ouvir. O reconhecimento evita amostrar esse anúncio ao reutilizar a ligação de transmissão em segundo plano já existente do FreeRadio (a mesma utilizada para o Time-Shift) em vez de abrir uma nova, identificando assim o que está realmente a tocar em vez de um anúncio. Isto funciona automaticamente e não requer configuração.

## Espelho de Áudio

O atalho `Ctrl+Win+M` duplica a transmissão atual para um segundo dispositivo de saída de áudio em simultâneo.

Na primeira pressão, aparece uma caixa de diálogo de seleção com os dispositivos de saída disponíveis. Depois de escolher um dispositivo, o espelhamento inicia e a reprodução principal continua sem interrupção. Prima o atalho novamente para parar o espelhamento.

**Casos de utilização:**
- **Colunas + auscultadores** — Permita que um convidado acompanhe a mesma transmissão nos auscultadores enquanto ouve pelas colunas do computador.
- **Configuração de gravação** — Direcione a saída principal para colunas e a segunda saída para um gravador externo ou interface de áudio para captura externa.
- **Multi-divisão** — Reproduza através de um altifalante Bluetooth e do altifalante integrado em simultâneo; não é necessário software adicional para levar o áudio para outra divisão.
- **Monitorização remota** — Numa sessão de partilha de ecrã ou ambiente de trabalho remoto, tanto o lado local como o remoto podem ouvir a mesma transmissão em simultâneo.

> **Nota:** O espelho de áudio só está disponível quando o backend BASS está ativo. Se o volume for alterado enquanto o espelhamento está ativo, ambas as saídas são atualizadas em simultâneo.

## Modo de Música de Fundo (Obligato)

O atalho `Ctrl+Win+Shift+M` reproduz uma estação favorita discretamente em segundo plano, num motor de áudio completamente separado do leitor principal — como um fundo musical suave a tocar por baixo do que estiver realmente a fazer.

Na primeira pressão, abre-se uma caixa de diálogo com três controlos:

- **Estação de fundo** — uma lista das suas estações favoritas para escolher qual reproduzir em ciclo em segundo plano. Requer pelo menos um favorito; se a sua lista de favoritos estiver vazia, o FreeRadio pede-lhe para adicionar primeiro uma estação (`Ctrl+Win+V` enquanto uma estação está a tocar).
- **Saída de áudio** — o dispositivo através do qual a estação de fundo é reproduzida: **Igual à saída principal** (predefinição), **Predefinição do sistema**, ou qualquer dispositivo específico que o FreeRadio consiga detetar.
- **Volume de fundo** — a que volume a estação de fundo toca, como percentagem do volume atual do leitor principal (10%, 25%, 50%, 75%, 100%, 125% ou 150%). As suas escolhas são memorizadas para a próxima vez.

Depois de iniciado, a estação de fundo continua a tocar independentemente do leitor principal — mudar de estação, podcast ou audiolivro no leitor principal, ou pará-lo completamente, nunca interrompe o modo Obligato. Duas coisas permanecem automaticamente ligadas ao leitor principal:

- **Volume** — o volume de fundo é mantido continuamente na percentagem escolhida do volume atual do leitor principal, pelo que aumentar ou diminuir o volume principal (`Ctrl+Win+↑`/`↓`) ajusta a música de fundo na mesma proporção.
- **Pausa** — pausar o leitor principal (`Ctrl+Win+P`) também pausa a estação de fundo, e retomar o leitor principal também a retoma. Uma paragem completa do leitor principal não é considerada uma pausa, pelo que a estação de fundo continua a tocar.

Prima `Ctrl+Win+Shift+M` novamente a qualquer momento para parar o modo Obligato.

## Gravação

As gravações são guardadas por predefinição em `Documents\FreeRadio Recordings\`. O nome do ficheiro inclui o nome da estação e a hora de início da gravação. A pasta de gravações pode ser alterada em qualquer altura em Menu NVDA → Preferências → Definições → FreeRadio → **Pasta de gravações**. Uma vez que o motor de gravação se liga diretamente à transmissão, o áudio é escrito em disco tal como é recebido — sem processamento nem recodificação; a qualidade da gravação é idêntica à qualidade da emissão.

**Gravação instantânea:** Enquanto uma estação está a reproduzir, prima `Ctrl+Win+E`. Prima novamente para parar. A reprodução continua sem interrupção.

**Gravação de canção:** Prima `Ctrl+Win+E` **duas vezes** rapidamente enquanto uma estação que difunde metadados ICY está a reproduzir. A gravação inicia imediatamente e recebe o nome do título da faixa atual. Quando a faixa muda, a gravação para automaticamente e o NVDA anuncia o nome do ficheiro guardado. Se pretender terminar a gravação antes de a faixa terminar, prima `Ctrl+Win+E` duas vezes novamente. Se a estação atual não difundir metadados ICY, a gravação de canção não está disponível e o NVDA irá informá-lo.

**Gravação agendada:** Abra o separador Gravação no navegador. Selecione uma estação dos seus favoritos, introduza a hora de início no formato HH:MM e a duração em minutos, selecione um ou mais dias ativos e, em seguida, escolha o modo de repetição e o modo de gravação:

**Dias ativos:** Marque um ou mais dias da semana. No modo de gravação única, é criada uma entrada separada para cada dia selecionado, colocada na próxima ocorrência desse dia. No modo recorrente, a gravação repete-se apenas nos dias marcados. Se não forem selecionados dias, a gravação não está restrita a dias específicos.

**Modo de repetição:**
- **Gravar uma vez** — cria uma gravação única para cada dia selecionado. Cada entrada é colocada na próxima ocorrência desse dia; se a hora de hoje já tiver passado, a entrada é automaticamente transferida para a semana seguinte.
- **Repetir semanalmente** — repete-se todas as semanas nos dias ativos selecionados até ser removida da lista de agendamento.

**Modo de gravação:**
- **Gravar enquanto ouve** — reproduz e grava em simultâneo. É iniciado um backend de reprodução seguindo a ordem de prioridade BASS → VLC → PotPlayer → Windows Media Player.
- **Apenas gravar** — grava silenciosamente em segundo plano sem qualquer saída de áudio; o motor de gravação liga-se diretamente à transmissão.

O NVDA anuncia quando uma gravação inicia e quando termina. Se o NVDA for reiniciado enquanto uma gravação agendada estiver ativa, a gravação é retomada automaticamente no arranque.

Tal como o reconhecimento musical, a gravação instantânea e a gravação de faixa reutilizam a ligação de transmissão em segundo plano já existente do FreeRadio quando disponível, em vez de abrir uma nova, para que a gravação capture o que está realmente a ser emitido mesmo em estações que de outra forma reproduziriam um anúncio novo numa ligação recente. Isto não se aplica às gravações agendadas em modo **Apenas Gravar**, uma vez que nenhuma estação já está a reproduzir no momento em que estas começam.

## Time-Shift (Recuar na Rádio em Direto)

O time-shift permite recuar na estação que está a ouvir, como um DVR ou uma cassete — pause o momento, volte uns minutos atrás e recupere o direto quando quiser. A reprodução nunca precisa de parar: recuar e avançar acontecem instantaneamente no mesmo fluxo de áudio.

Esta funcionalidade está **desativada por defeito**. Ative-a em Menu NVDA → Preferências → Definições → FreeRadio → **Ativar buffer de time-shift (recuar na rádio em direto, ~10 minutos)**, ou ative-a instantaneamente a qualquer momento com `Ctrl+Win+T`.

> **Nota:** o FreeRadio mantém agora uma pequena captura em segundo plano da estação em reprodução em execução permanente — não apenas quando esta definição está ativada — porque tanto o Reconhecimento Musical como a Gravação dependem dela para o comportamento de evitar anúncios descrito nessas secções. Quando esta definição está **desativada**, essa captura em segundo plano mantém-se limitada a cerca dos últimos 45 segundos e `Ctrl+Win+J`/`Ctrl+Win+K` permanecem indisponíveis — apenas o tamanho do buffer muda, não se está ou não em execução. Ativar a definição amplia a mesma captura para o buffer completo de recuo de ~10 minutos descrito abaixo.

### Como funciona

Após ativação, o FreeRadio captura continuamente a estação em reprodução para um buffer local rotativo em segundo plano. O buffer contém aproximadamente os **últimos 10 minutos** de áudio; o áudio mais antigo é automaticamente descartado à frente à medida que o novo chega, de modo que o buffer representa sempre o "passado recente" relativamente à margem do direto.

- **`Ctrl+Win+J`** — Recuar 15 segundos. A primeira pressão passa da reprodução em direto para a reprodução com time-shift, começando 15 segundos atrás da margem do direto. Cada pressão adicional recua mais 15 segundos.
- **`Ctrl+Win+K`** — Avançar 15 segundos em modo time-shift. Ao atingir a margem do direto, a reprodução regressa automaticamente ao stream em direto e o NVDA anuncia «Voltar ao direto».
- **`Ctrl+Win+T`** — Liga ou desliga toda a funcionalidade. Desligá-la em modo time-shift regressa imediatamente ao direto e interrompe a captura em segundo plano da estação atual.

A captura em segundo plano continua a funcionar todo o tempo que está em time-shift, pelo que a margem do direto continua a avançar mesmo enquanto ouve algo de alguns minutos atrás — exatamente como um DVR real.

### Ativação e aquecimento do buffer

O buffer começa a preencher-se assim que uma estação começa a reproduzir (após ativar a funcionalidade) ou no momento em que ativa a funcionalidade enquanto já ouve uma estação. Por isso, recuar só é possível depois de alguns segundos de áudio terem sido realmente capturados — se premir `Ctrl+Win+J` imediatamente após mudar de estação, o NVDA avisará que ainda não há áudio suficiente no buffer. Aguarde alguns segundos e tente novamente.

Mudar para uma estação diferente reinicia sempre o buffer para a nova estação; o áudio da estação anterior é descartado.

### Streams suportados

O time-shift funciona com a mesma gama de streams que o FreeRadio já suporta:

- Streams HTTP/HTTPS simples (MP3, AAC, OGG, etc.), incluindo servidores de tipo Shoutcast/Icecast.
- **Streams HLS (`.m3u8`)** — O FreeRadio resolve a playlist principal da estação, segue a playlist de multimédia e transfere segmentos em segundo plano para manter o buffer preenchido.

No caso raro de a playlist de uma estação não poder ser lida de todo (por exemplo, um manifesto `.m3u8` danificado ou inacessível), o NVDA indicará que recuar não está disponível para essa estação em particular.

### Requisitos e limitações

- **Requer o backend BASS.** O time-shift não está disponível quando o BASS está desativado e a reprodução recorre ao VLC, PotPlayer ou Windows Media Player. A própria captura em segundo plano (e a prevenção de anúncios que esta fornece ao Reconhecimento Musical e à Gravação) também não está disponível nesse caso, uma vez que depende da mesma ligação baseada em BASS.
- O buffer tem aproximadamente 10 minutos; não é possível recuar além disso.
- O buffer é por estação: mudar de estação, parar a reprodução ou reiniciar o NVDA limpa-o e começa de novo.
- A reprodução com time-shift usa o seu próprio ficheiro de buffer local e não produz uma gravação guardada — se quiser conservar o áudio permanentemente, use também a Gravação instantânea (`Ctrl+Win+E`).

## Temporizador

Abra o separador Temporizador no navegador de estações (`Alt+4`). É possível adicionar dois tipos de temporizador:

**Alarme — iniciar rádio:** Inicia automaticamente a reprodução de uma estação selecionada dos seus favoritos à hora especificada. Escolha uma estação e introduza a hora no formato HH:MM.

**Suspensão — parar rádio:** Para a reprodução à hora especificada. Quando o temporizador dispara, o volume é reduzido gradualmente durante 60 segundos antes de parar a reprodução. Não é necessário selecionar uma estação; basta introduzir a hora.

Para ambos os tipos, se a hora introduzida já tiver passado, a ação é agendada para o dia seguinte. Se já existir um temporizador à mesma hora (independentemente do tipo), a adição de um novo é bloqueada; o utilizador é informado do conflito e solicitado a remover primeiro a entrada existente. Os temporizadores pendentes estão listados no separador; selecione um e prima o botão Remover Temporizador Selecionado para o cancelar.

## Podcasts

O FreeRadio inclui um leitor de podcasts completo. Pode subscrever qualquer feed de podcast RSS ou Atom, navegar por episódios, reproduzi-los, descarregá-los e retomar a reprodução onde ficou — tudo totalmente acessível.

### Aceder ao Separador Podcasts

Abra o navegador de estações com `Ctrl+Win+R` e mude para o separador **Podcasts** com `Ctrl+Tab` ou `Alt+6`. O separador está organizado em três áreas principais:

1. **Pesquisar e adicionar** — secção superior para descobrir novos podcasts, incluindo uma lista de pré-visualização que mostra os episódios do resultado de pesquisa atualmente selecionado.
2. **Subscrições** — lista dos seus feeds subscritos.
3. **Episódios** — lista de episódios do feed selecionado, com controlos de reprodução.

### Adicionar um Feed de Podcast

Pode adicionar um feed de podcast de duas formas:

**Por URL:**
- No campo **"Ou introduza o URL do podcast"**, cole o URL completo do feed RSS ou Atom (por exemplo, `https://example.com/feed.xml`).
- Prima Enter ou clique no botão **Adicionar Feed**.
- O FreeRadio obtém o feed, valida-o e adiciona-o às suas subscrições. Se o feed for válido, ouvirá uma confirmação com o título do feed. Se falhar, uma mensagem de erro explica o motivo.

**Por pesquisa:**
- No campo **Pesquisar**, escreva uma palavra-chave (título do podcast, tema ou nome do apresentador) e prima Enter.
- O FreeRadio pesquisa no diretório de podcasts da iTunes e apresenta os podcasts correspondentes na lista **Resultados da pesquisa**.
- Selecionar um resultado obtém esse feed em segundo plano e lista os seus episódios na lista **Episódios do resultado selecionado** logo abaixo, para que possa pré-visualizar o que o programa realmente contém antes de decidir subscrever — veja [Pré-visualizar Episódios Antes de Subscrever](#pré-visualizar-episódios-antes-de-subscrever) abaixo.
- Assim que estiver satisfeito com o que vê, selecione o resultado e prima `Enter`, ou abra o seu menu de contexto (tecla Aplicações / `Shift+F10`, ou clique com o botão direito) e escolha **Subscrever**, para o adicionar às suas subscrições. O feed é adicionado imediatamente e aparece na sua lista de subscrições. Não existe um botão separado "Adicionar Selecionado da Pesquisa" — `Enter` ou o menu de contexto é a única forma de subscrever a partir dos resultados de pesquisa, mantendo a interface limpa e acessível.

> **Dica:** Também pode escrever um URL de feed diretamente no campo de pesquisa — se parecer um URL válido, o complemento tentará adicioná-lo como feed sem pesquisar.

**Menu de contexto para resultados de pesquisa:** Clique com o botão direito num resultado de pesquisa, ou selecione-o e prima a tecla Aplicações / `Shift+F10`, para abrir um menu com uma única ação **Subscrever**, idêntica a premir `Enter` no resultado.

### Pré-visualizar Episódios Antes de Subscrever

Antes de se comprometer com uma subscrição, pode ouvir os episódios de um podcast diretamente a partir dos resultados de pesquisa. Sempre que seleciona um podcast na lista **Resultados da pesquisa**, o FreeRadio obtém esse feed e mostra os seus episódios — título e data de publicação — na lista **Episódios do resultado selecionado** por baixo.

- Selecione um episódio nessa lista de pré-visualização e prima `Enter`, ou abra o seu menu de contexto (tecla Aplicações / `Shift+F10`, ou clique com o botão direito) e escolha **Pré-visualizar**, para começar a reproduzi-lo através do leitor normal. Todos os controlos de reprodução habituais (pausa, volume, time-shift, etc.) funcionam nele exatamente como funcionariam em qualquer outra estação ou episódio.
- Enquanto um episódio está a ser pré-visualizado, o mesmo menu de contexto mostra **Parar Pré-visualização** no lugar de **Pré-visualizar** — escolha-o, ou prima `Enter` novamente nesse episódio, para parar.
- Pré-visualizar não o subscreve a nada; é puramente para ouvir antes de decidir. A própria lista de pré-visualização é temporária — é substituída assim que seleciona um resultado de pesquisa diferente, e não persiste em lado nenhum da forma como as suas subscrições reais persistem.

### Gerir Subscrições

Depois de adicionar alguns feeds, estes aparecem na lista **Subscrições**. Cada entrada mostra o título do feed e o número de episódios disponíveis.

- **Selecione um feed** para ver os seus episódios na lista inferior. A caixa de texto só de leitura **Detalhes do feed** por baixo da lista de subscrições mostra o título do feed, autor, descrição, número de episódios e URL.
- **Atualizar um feed** — selecione-o e prima o botão **Atualizar Feed** (disponível através do menu de contexto, veja abaixo) para obter os episódios mais recentes. Todos os feeds também são atualizados automaticamente em segundo plano quando abre o separador Podcasts, pelo que normalmente vê os episódios mais recentes sem intervenção manual.
- **Remover um feed** — selecione-o e prima `Delete` ou use o menu de contexto para o remover das suas subscrições. Ser-lhe-á pedida confirmação antes da remoção.

**Menu de contexto para feeds:** Clique com o botão direito num feed, ou selecione-o e prima a tecla Aplicações / `Shift+F10`, para abrir um menu com:
- **Atualizar Feed** — obtém novos episódios agora.
- **Guardar Perfil de Áudio para Este Podcast** / **Limpar Perfil de Áudio** — veja [Perfil de Áudio do Podcast](#perfil-de-áudio-do-podcast).
- **Remover Feed** — elimina a subscrição.
- **Copiar URL do Feed** — copia o URL do feed para a área de transferência.

### Navegar e Reproduzir Episódios

Selecione um feed na lista de subscrições; os seus episódios aparecem na lista **Episódios** abaixo. Cada episódio mostra:
- O seu número de episódio (1 = o episódio mais antigo no feed, contando até ao mais recente).
- A sua data de publicação (se disponível).
- O seu título.
- Um prefixo **"Ouvido"** se o episódio tiver sido reproduzido na totalidade.
- Um sufixo de duração, seja a duração total (se nunca reproduzido) ou o progresso decorrido/total (se reproduzido parcialmente).

**Reprodução:**
- Selecione um episódio e prima `Enter` ou `Espaço` para começar a reproduzi-lo. Se um episódio foi reproduzido parcialmente antes, retoma de onde ficou.
- A linha *não* é atualizada durante a reprodução do episódio — isto é intencional, para que o NVDA não reanuncie repetidamente a linha enquanto está nela. A sua marca "Ouvido" e duração são atualizadas imediatamente no momento em que pausa o episódio ou este termina de reproduzir, pelo que a apresentação é sempre exata precisamente quando importa; simplesmente não avança segundo a segundo durante a reprodução.
- Use `F3` / `F4` no separador Podcasts para se mover para o episódio anterior / seguinte e reproduzi-lo imediatamente. Também pode usar `←` / `→` enquanto a lista de episódios está em foco, ou `Ctrl+←` / `Ctrl+→` em qualquer parte do separador Podcasts — ambos funcionam de forma idêntica.
- Use `Shift+F3` / `Shift+F4` para se mover entre feeds sem reproduzir episódios.
- Prima `Espaço` enquanto um episódio está a tocar para pausar ou retomar a reprodução.

**Retomar a reprodução:** O FreeRadio guarda a sua posição em cada episódio de podcast automaticamente — imediatamente sempre que pausa ou o episódio termina, e a cada 15 segundos em segundo plano enquanto continua a ouvir, para que uma falha ou reinício inesperado não perca muito progresso. Se parar ou pausar a reprodução e voltar mais tarde, o episódio retoma a partir da posição guardada. Se reproduzir o episódio até ao fim (dentro dos últimos 3 segundos), é marcado como "Ouvido" e não retomará — começa do início da próxima vez, e o prefixo "Ouvido" aparece na lista.

**Menu de contexto para episódios:** Clique com o botão direito num episódio, ou selecione-o e prima a tecla Aplicações / `Shift+F10`, para abrir um menu com:
- **Reproduzir Episódio** — inicia a reprodução.
- **Descarregar Episódio** — descarrega o ficheiro do episódio para a sua pasta de gravações.
- **Guardar Perfil de Áudio para Este Podcast** / **Limpar Perfil de Áudio** — os mesmos comandos do menu de contexto do próprio feed, incluídos aqui por conveniência para não ter de voltar à lista de Subscrições. Continuam a guardar um perfil para todo o podcast, não um separado para este episódio — veja [Perfil de Áudio do Podcast](#perfil-de-áudio-do-podcast).
- **Copiar URL do Episódio** — copia o URL de áudio direto para a área de transferência.

### Descarregar Episódios

Selecione um episódio e clique no botão **Descarregar Episódio** (ou use o menu de contexto). O episódio é descarregado para a sua pasta de gravações (`Documentos\FreeRadio Recordings\` por predefinição). O nome do ficheiro baseia-se no título do episódio e na extensão de ficheiro detetada (`.mp3`, `.m4a`, `.ogg`, etc.). O NVDA anuncia quando o descarregamento começa e termina. Se o ficheiro já existir, é informado e o descarregamento é ignorado.

### Filtrar Episódios

Acima da lista de episódios está um campo **Filtro**. À medida que escreve, a lista de episódios é filtrada em tempo real para mostrar episódios cujo título contém o texto escrito, ou cujo número de episódio corresponde exatamente — pelo que escrever `47` salta diretamente para o episódio 47 mesmo que "47" não apareça em lado nenhum do seu título. O NVDA anuncia o número de episódios correspondentes após cada alteração. Prima a seta `Para Baixo` a partir do campo de filtro para mover o foco diretamente para a lista filtrada.

### Detalhes de Reprodução de Podcasts

Os episódios de podcast são reproduzidos usando o **motor BASS** (o mesmo motor usado para fluxos de rádio e, a partir desta versão, o único motor de reprodução que o FreeRadio usa). Como os episódios são descarregados progressivamente e são pesquisáveis, pode usar os atalhos de recuo/avanço de time-shift (`Ctrl+Win+J`/`Ctrl+Win+K`) enquanto reproduz um podcast para navegar dentro do episódio. A posição é guardada automaticamente para que possa retomar mais tarde.

**Navegação escalonada:** Ao contrário do recuo fixo de 15 segundos da rádio em direto, a navegação dentro de um podcast ou audiolivro escala consoante a forma como prime a tecla, para que possa fazer uma pequena correção ou saltar uma longa distância sem premir repetidamente:

- **Manter a tecla premida** (repetição automática) avança ou recua **5 segundos** por repetição — a mesma pequena quantidade que este atalho sempre usou para ficheiros.
- **Um toque deliberado** navega **12 segundos**.
- **Dois toques** em sucessão rápida navegam **1 minuto**.
- **Três ou mais toques** navegam **5 minutos**; toques adicionais na mesma sequência não aumentam mais.

Um toque deliberado é retido por um breve momento antes de realmente navegar, para o caso de vir mais um toque — só ocorre uma navegação por sequência de toques, dimensionada consoante quantos toques foram finalmente feitos, não a soma da quantidade de cada toque. Após uma navegação, o NVDA anuncia a posição decorrida/restante resultante no episódio em vez de apenas "X segundos à frente/atrás".

**Velocidade de reprodução:** Pode ajustar a velocidade de reprodução dos episódios de podcast usando `Ctrl+Win+Shift+K` (mais rápido) e `Ctrl+Win+Shift+J` (mais lento). A velocidade muda em incrementos de 0,1x, variando entre 0,5x e 2,0x, com o tom preservado. Isto requer a biblioteca opcional `bass_fx.dll` colocada na pasta do complemento. Se a biblioteca estiver em falta, o NVDA informa-o de que a funcionalidade não está disponível.

> **Nota:** O `bass_fx.dll` não é distribuído com o FreeRadio por predefinição. Pode descarregá-lo da [página do BASS FX](https://www.un4seen.com/bass-fx.html) e colocá-lo na pasta `bass/x64` do complemento (para NVDA de 64 bits) ou `bass` (para NVDA de 32 bits) para ativar esta funcionalidade.

**Efeito sonoro ao retomar:** Sempre que um episódio retoma de uma posição guardada, o FreeRadio reproduz brevemente um suave efeito sonoro de carregamento de cassete num canal separado enquanto navega de volta ao seu ponto guardado, em vez de deixar o áudio do próprio episódio tocar audivelmente a partir de 0:00 entretanto. Isto acontece automaticamente sempre que o motor BASS está ativo e é independente da definição **Transição ao mudar de estação** — essa definição afeta apenas a mudança entre estações de rádio em direto, não a retoma de podcasts ou audiolivros.

### Perfil de Áudio do Podcast

Clique com o botão direito num podcast na lista Subscrições, ou clique com o botão direito em qualquer um dos seus episódios, e escolha **Guardar Perfil de Áudio para Este Podcast** para guardar o volume, efeitos, ganhos de equalizador e/ou velocidade de reprodução atuais como um perfil associado a esse podcast. Sempre que qualquer episódio desse podcast toca, as definições guardadas são aplicadas automaticamente, substituindo as predefinições globais. Como o comando está disponível tanto no menu de contexto do feed como no do episódio, pode aceder-lhe sem ter de voltar à lista de Subscrições — de qualquer forma, guarda sempre um perfil para todo o podcast, não um separado por episódio.

Uma caixa de diálogo permite-lhe escolher exatamente o que guardar:
- **Apenas volume**
- **Apenas efeitos**
- **Volume e efeitos**
- **Volume e velocidade de reprodução**
- **Efeitos e velocidade de reprodução**
- **Apenas velocidade de reprodução**
- **Volume, efeitos e velocidade de reprodução**

Apenas as partes que escolher são escritas no perfil; o que for deixado de fora mantém o que já estava guardado. Por exemplo, escolher **Apenas velocidade de reprodução** num podcast que já tem um perfil de volume/efeitos guardado atualiza apenas a velocidade e deixa o resto intacto.

**Limpar Perfil de Áudio** remove o perfil guardado do podcast, a partir de qualquer um dos menus de contexto. Só está ativo quando o podcast tem atualmente um perfil guardado.

### Armazenamento de Dados de Podcasts

As suas subscrições são armazenadas em `freeradio_podcasts.json` na pasta de configuração de utilizador do NVDA. As posições dos episódios são armazenadas separadamente em `podcast_positions.json` no mesmo local. Ambos os ficheiros são JSON simples e podem ser copiados para backup ou transferidos para outro computador.

## Audiolivros (GETEM e LibriVox)

O FreeRadio inclui um leitor de audiolivros que pesquisa, reproduz e descarrega livros de duas fontes:

- **[GETEM](https://getem.boun.edu.tr/)** — a biblioteca digital gerida pelo Centro para Pessoas com Deficiência Visual da Universidade de Boğaziçi. Requer uma adesão gratuita para transmitir ou descarregar o áudio de um livro (a navegação não requer) — veja [Iniciar Sessão](#iniciar-sessão) abaixo.
- **[LibriVox](https://librivox.org/)** — o projeto de audiolivros de domínio público lidos por voluntários. Não é necessária conta ou início de sessão de qualquer tipo; todo o seu catálogo, incluindo os próprios ficheiros de áudio, é de domínio público e livremente acessível.

Os resultados de ambas as fontes aparecem juntos numa única lista fundida de **Resultados da pesquisa** e numa única lista fundida de **Biblioteca** — não existe um separador ou menu suspenso separado para alternar entre eles. A fonte de cada livro (GETEM ou LibriVox) é apresentada como uma etiqueta junto ao seu título, e nos seus detalhes, para que possa sempre saber qual está a ver. Pode pesquisar, pré-visualizar, adicionar, reproduzir e descarregar livros de qualquer uma das fontes exatamente da mesma forma; reproduzir obras de várias partes com retoma automática entre partes; e descarregar livros para ouvir offline — tudo totalmente acessível.

Qualquer uma das fontes pode ser desativada em **NVDA Menu → Preferências → Definições → FreeRadio** com a lista de verificação **Fontes de audiolivros**, se quiser pesquisar apenas uma delas. Ambas estão ativadas por predefinição.

> **Nota:** Ouvir um livro do GETEM requer uma adesão gratuita ao GETEM. Navegar no catálogo do GETEM não requer conta, mas resolver e reproduzir o áudio de um livro do GETEM requer — veja [Iniciar Sessão](#iniciar-sessão) abaixo. Os livros do LibriVox nunca requerem conta.

### Aceder ao Separador Audiolivros

Abra o navegador de estações com `Ctrl+Win+R` e mude para o separador **Audiolivros** com `Ctrl+Tab` ou `Alt+7`. O separador tem três áreas principais:

1. **Pesquisar** — um campo de texto para pesquisar ambos os catálogos ativados de uma vez, com uma lista de resultados que aparece assim que uma pesquisa é executada.
2. **Biblioteca** — a lista de livros que adicionou de qualquer uma das fontes, onde os reproduz, descarrega e gere.
3. **Detalhes** — uma caixa só de leitura que mostra a fonte, título, autor, narrador, editora, formato, número de partes, descrição e URL do catálogo do livro selecionado, em qualquer uma das listas.

### Iniciar Sessão

O GETEM requer ser um membro registado para transmitir ou descarregar o áudio real de um livro, embora o próprio catálogo possa ser pesquisado livremente. Introduza o seu nome de utilizador e palavra-passe do GETEM uma vez em **NVDA Menu → Preferências → Definições → FreeRadio**; são armazenados encriptados no disco (através da API Windows Data Protection, associada à sua conta de utilizador do Windows) e reutilizados automaticamente depois. Se tentar reproduzir ou descarregar um livro do GETEM antes de introduzir as credenciais, o FreeRadio diz-lhe para as adicionar primeiro nas Definições.

O LibriVox não precisa de nenhum passo de início de sessão — os seus resultados e áudio podem ser pesquisados, pré-visualizados, reproduzidos e descarregados imediatamente, sem credenciais a introduzir.

### Pesquisar Audiolivros

Escreva um termo de pesquisa no campo de pesquisa e prima `Enter`. O FreeRadio pesquisa nas fontes ativadas nas Definições e funde os resultados numa única lista:

- O **GETEM** é pesquisado por título, autor, narrador, assunto e editora ao mesmo tempo, uma vez que o próprio formulário de pesquisa do GETEM só suporta restringir por todos eles em conjunto, em vez de uma única pesquisa através de qualquer um deles. Só são mostradas obras realmente disponíveis em formato áudio (narração humana ou computorizada, audiodescrição, drama radiofónico, livros falados DAISY, etc.); braille, letra grande e outros formatos não sonoros são filtrados automaticamente.
- O **LibriVox** é pesquisado por título ou autor/leitor no seu catálogo de domínio público.

O NVDA anuncia quantos audiolivros foram encontrados no total.

Selecionar um resultado mostra os seus detalhes — autor, narrador, editora, formato e número de partes — na caixa de detalhes abaixo.

**Pré-visualização:** Selecione um resultado e prima `Espaço`, ou abra o seu menu de contexto (tecla Aplicações / `Shift+F10`, ou clique com o botão direito) e escolha **Pré-visualizar**, para começar a reproduzi-lo a partir da primeira parte sem o adicionar à sua biblioteca. Enquanto um livro está a ser pré-visualizado, o mesmo menu de contexto mostra **Parar Pré-visualização** no seu lugar — escolha-o, ou prima `Espaço` novamente, para parar. Pré-visualizar um livro não guarda a sua posição de escuta, uma vez que isso só é seguido para livros já na sua biblioteca.

**Adicionar à sua biblioteca:** Selecione um resultado e prima `Enter`, ou use o seu menu de contexto e escolha **Adicionar à Biblioteca**, para o adicionar. O FreeRadio diz-lhe se o livro já lá está.

### A Sua Biblioteca

Os livros que adicionou aparecem na lista **Biblioteca**, mostrando título, autor e formato. Selecionar um mostra os seus detalhes abaixo.

- Prima `Enter` ou `Espaço` para reproduzir o livro selecionado. Se nada estiver carregado, `Espaço` inicia-o; se algo já estiver a tocar, `Espaço` pausa-o, correspondendo ao resto do leitor.
- Use `F3` / `F4` no separador Audiolivros para se mover para o **livro** anterior / seguinte na sua biblioteca e começar a reproduzi-lo. `Ctrl+←` / `Ctrl+→` fazem o mesmo enquanto a lista da biblioteca está em foco.
- Use `Shift+F3` / `Shift+F4` para se mover entre **partes** do livro atualmente a tocar — o inverso do separador Podcasts, onde F3/F4 se movem entre episódios e Shift+F3/F4 entre feeds. Isto porque um livro é uma única entrada da biblioteca mesmo quando tem várias partes, pelo que a navegação mais detalhada "por parte" fica aqui nas teclas modificadas com Shift.

**Menu de contexto para entradas da biblioteca:** Clique com o botão direito num livro, ou selecione-o e prima a tecla Aplicações / `Shift+F10`, para abrir um menu com:
- **Reproduzir Média** — inicia a reprodução, o mesmo que `Enter`.
- **Descarregar Livro** — descarrega todas as partes do livro; veja [Descarregar Audiolivros](#descarregar-audiolivros) abaixo.
- **Copiar o URL** — copia o URL da página do catálogo do livro para a área de transferência (a página do catálogo GETEM para um livro do GETEM, ou a página de detalhes do archive.org para um livro do LibriVox).
- **Guardar Perfil de Áudio para Este Livro** / **Limpar Perfil de Áudio** — veja [Perfil de Áudio do Audiolivro](#perfil-de-áudio-do-audiolivro) abaixo.
- **Remover da Biblioteca** — elimina o livro da sua biblioteca.

### Reprodução e Retoma

Uma obra de várias partes é tratada como um único item no leitor, não uma linha por parte — da mesma forma que um episódio de podcast é um único item independentemente de como é entregue. O FreeRadio lembra-se de qual parte ouviu por último e retoma aí automaticamente da próxima vez que reproduzir esse livro, mesmo após um reinício do NVDA.

Quando uma parte termina, o FreeRadio inicia automaticamente a parte seguinte do mesmo livro — não precisa de a selecionar manualmente. Isto acontece mesmo que a janela do Navegador de Estações esteja fechada nessa altura; a parte "a tocar agora" mostrada na lista Biblioteca é ressincronizada automaticamente da próxima vez que a janela é aberta.

A reprodução é transmitida através de um pequeno relé local em vez de descarregar toda a parte primeiro, pelo que a escuta começa assim que os primeiros bytes chegam — o mesmo comportamento de início imediato que os podcasts usam. Todos os controlos habituais do leitor (pausa, volume, time-shift, velocidade de reprodução, dispositivo de saída, etc.) funcionam num audiolivro exatamente como funcionariam numa estação ou episódio de podcast.

Tal como os podcasts, retomar um livro da sua posição guardada reproduz um breve efeito sonoro de carregamento de cassete enquanto o FreeRadio navega até ao seu ponto guardado — veja a nota **Efeito sonoro ao retomar** em [Detalhes de Reprodução de Podcasts](#detalhes-de-reprodução-de-podcasts).

### Perfil de Áudio do Audiolivro

Clique com o botão direito num livro na sua lista Biblioteca e escolha **Guardar Perfil de Áudio para Este Livro** para guardar o volume, efeitos, ganhos de equalizador e/ou velocidade de reprodução atuais como um perfil associado a esse livro. Sempre que o livro (ou qualquer uma das suas partes) toca, as definições guardadas são aplicadas automaticamente, substituindo as predefinições globais. Isto funciona exatamente da mesma forma que o [Perfil de Áudio do Podcast](#perfil-de-áudio-do-podcast) acima, incluindo o mesmo conjunto de opções de guardar (volume, efeitos e/ou velocidade de reprodução, em qualquer combinação) e o mesmo comportamento de atualização parcial.

**Limpar Perfil de Áudio** remove o perfil guardado do livro; só está ativo quando o livro tem atualmente um perfil guardado.

### Descarregar Audiolivros

Selecione um livro na sua biblioteca e escolha **Descarregar Livro** no seu menu de contexto para guardar cada parte na sua própria pasta (com o nome do livro) dentro da sua pasta de gravações (`Documentos\FreeRadio Recordings\` por predefinição). Os ficheiros são numerados para que as partes fiquem sempre ordenadas pela ordem de escuta, independentemente de como o próprio GETEM as designa. O NVDA anuncia quantas partes foram guardadas assim que o descarregamento termina; se uma parte falhar, o último erro é reportado juntamente com a contagem.

### Armazenamento de Dados de Audiolivros

Cada fonte mantém o seu próprio ficheiro de biblioteca, apesar de serem apresentadas fundidas no separador Audiolivros. A sua biblioteca GETEM (livros adicionados e o seu progresso de escuta) é armazenada em `freeradio_getem_library.json`, e a sua biblioteca LibriVox é armazenada separadamente em `freeradio_librivox_library.json`, ambas na pasta de configuração de utilizador do NVDA. As suas credenciais GETEM encriptadas são armazenadas separadamente em `freeradio_getem_credentials.bin` no mesmo local, e só podem ser desencriptadas pela mesma conta de utilizador do Windows que as guardou. O LibriVox não tem ficheiro de credenciais, uma vez que não requer conta.

## Definições

As seguintes opções podem ser configuradas em Menu NVDA → Preferências → Definições → FreeRadio:

| Opção | Descrição |
|---|---|
| Dispositivo de saída de áudio (backend BASS) | Define o dispositivo de saída de áudio para reprodução de rádio. A lista inclui todos os dispositivos compatíveis com BASS no sistema, mais uma opção "Predefinição do sistema". As alterações são aplicadas imediatamente ao guardar; se o dispositivo selecionado for desligado, o complemento reverte automaticamente para a predefinição do sistema e anuncia a alteração. Só ativo quando o backend BASS está em uso. |
| Volume | Define o volume inicial do complemento (0–200). As alterações feitas durante a reprodução com `Ctrl+Win+↑` / `Ctrl+Win+↓` também são refletidas aqui. |
| Efeito de áudio predefinido | Define o efeito de áudio aplicado quando o NVDA inicia ou uma estação começa a reproduzir. O efeito selecionado corresponde à lista de Efeitos no Navegador de Estações. Só ativo quando o backend BASS está em uso. |
| Ganho EQ (graves / agudos / vocal) | Define o nível de ganho em dB para cada banda EQ (de −15 a +15). O controlo aparece automaticamente quando o efeito EQ correspondente está ativo e oculta-se quando é desativado. Os valores são guardados globalmente; podem ser substituídos por estação através do botão **Guardar Perfil de Áudio** no separador Favoritos. Só ativo quando o backend BASS está em uso. |
| Transição entre estações (backend BASS) | Controla o comportamento de transição ao mudar de estação. **Corte imediato** (predefinição) para a estação anterior imediatamente antes de a nova começar. **Transição curta (1 segundo)** e **Transição normal (2 segundos)** iniciam a nova estação sem pausa, desvanecendo gradualmente a anterior em segundo plano assim que o novo fluxo é confirmado. **Efeito sonoro de sintonização de estação** para a estação anterior imediatamente e reproduz um efeito sonoro de sintonização antes de a nova começar. Não tem efeito nem impacto no desempenho quando definido como Corte imediato. Só disponível com o backend BASS. |
| Retomar última estação ao iniciar o NVDA | Quando ativado, a última estação reproduzida reinicia automaticamente sempre que o NVDA inicia. |
| Anunciar automaticamente mudanças de faixa (metadados ICY) | Quando ativado, o NVDA lê automaticamente o novo nome da faixa sempre que muda numa estação que difunde metadados ICY. A primeira faixa também é anunciada imediatamente ao mudar para uma nova estação. Desativado por predefinição. |
| Silenciar notificações (mudanças de estação, reprodução, gravação) | Quando ativado, o NVDA deixa de anunciar mudanças de estação, alterações do estado de reprodução (reproduzir, pausar, parar) e eventos de gravação (iniciada, parada, concluída). Mensagens de erro, feedback de favoritos, resultados do reconhecimento musical e notificações de atualização não são afetados. Pode também ser alternado em tempo real através de um gesto de entrada não atribuído. Desativado por predefinição. |
| Ativar buffer de time-shift (recuar na rádio em direto, ~10 minutos) | Ativa ou desativa os controlos de recuo (`Ctrl+Win+J`/`Ctrl+Win+K`) e amplia a captura em segundo plano de ~45 segundos até ~10 minutos. Uma pequena captura em segundo plano da estação em reprodução está sempre em execução, mesmo quando esta definição está desativada — ver a nota na secção **Time-Shift** abaixo. Também pode ser alternada instantaneamente com `Ctrl+Win+T`. Requer o backend BASS. Desativada por defeito — consulte a secção **Time-Shift** abaixo para todos os detalhes. |
| Guardar músicas gostadas em ficheiro de texto | Quando ativado, as informações de faixa copiadas para a área de transferência ao premir `Ctrl+Win+I` três vezes são também adicionadas a `Documents\FreeRadio Recordings\likedSongs.txt`. Se não existirem metadados ICY, o resultado do reconhecimento Shazam é guardado no mesmo ficheiro. Desativado por predefinição. |
| Quando Ctrl+Win+P é premido sem reprodução ativa | Determina o que acontece quando este atalho é premido e nada está a reproduzir: iniciar a última estação ou abrir a lista de favoritos. |
| Quando Ctrl+Win+P é premido duas vezes | Seleciona o que acontece quando o atalho é premido duas vezes rapidamente: não fazer nada, abrir a lista de favoritos, abrir o separador de gravação ou abrir o separador do temporizador. Quando "não fazer nada" está selecionado, a primeira pressão responde instantaneamente sem atraso. |
| Quando Ctrl+Win+P é premido três vezes | Seleciona o que acontece quando o atalho é premido três vezes rapidamente: não fazer nada, abrir a lista de favoritos, abrir o separador de pesquisa, abrir o separador de gravação ou abrir o separador do temporizador. |
| Caminho do ffmpeg.exe | Caminho para o ffmpeg.exe utilizado no reconhecimento musical. Se deixado em branco, é utilizado automaticamente um ffmpeg.exe na pasta do complemento. |
| Caminho do VLC | Se o VLC não estiver instalado ou estiver numa localização não padrão, pode ser introduzido aqui o caminho completo para o executável. |
| Caminho do wmplayer.exe | Introduza aqui o caminho para o Windows Media Player, se necessário. |
| Caminho do PotPlayer | Se o PotPlayer estiver numa localização não padrão, o seu caminho pode ser introduzido aqui. |
| Pasta de gravações | Define a pasta onde os ficheiros gravados são guardados. Se deixado em branco, é utilizada a localização predefinida `Documents\FreeRadio Recordings\`. Um botão Procurar permite selecionar a pasta de forma interativa. As alterações têm efeito imediatamente após guardar. |
| Verificar atualizações automaticamente | Quando ativado, é efetuada uma verificação de atualizações em segundo plano sempre que o NVDA inicia; é emitida uma notificação se for encontrada uma nova versão. Quando desativado, as verificações automáticas são interrompidas mas as verificações manuais continuam disponíveis. |
| Desativar verificação de conectividade à Internet antes de reproduzir | Recomendado para utilizadores que experimentam um atraso antes de uma estação começar a reproduzir. Também útil quando o DNS está bloqueado. |

## Silenciamento de Notificações

Quando a opção **Silenciar notificações** está ativada nas Definições, o NVDA suprime os seguintes anúncios automáticos:

- Nome da estação quando uma nova estação começa a reproduzir
- Alterações do estado de reprodução: reproduzir, pausar, parar
- Modo Obligato: iniciado / parado
- Eventos de gravação: iniciada, parada, concluída (gravações instantâneas, de canção e agendadas)
- Anúncios de mudança de faixa, mesmo quando **Anunciar automaticamente mudanças de faixa** também está ativo

Os seguintes anúncios **não** são afetados intencionalmente: mensagens de erro, feedback de favoritos (adicionado / já na lista), resultados do reconhecimento musical e notificações de atualização.

A definição pode ser alternada em Menu NVDA → Preferências → Definições → FreeRadio, ou em tempo real através de um gesto de entrada não atribuído (atribua um em Menu NVDA → Preferências → Definir comandos → FreeRadio). Quando alternada, o NVDA anuncia uma vez "Notificações silenciadas" ou "Notificações reativadas" para confirmar a alteração.

## Anúncio Automático de Mudanças de Faixa

Quando a opção **Anunciar automaticamente mudanças de faixa** está ativada nas Definições, o FreeRadio verifica os metadados ICY da estação ativa em segundo plano aproximadamente a cada 5 segundos. Quando a faixa muda, o novo título é automaticamente lido pelo NVDA — sem necessidade de premir qualquer tecla.

Ao mudar para uma nova estação, as primeiras informações de faixa são anunciadas assim que a ligação é estabelecida. Se mudar para uma estação que não difunde metadados ICY, o sistema permanece silencioso e as informações da faixa anterior não são repetidas.

Esta funcionalidade está desativada por predefinição e pode ser ativada em Menu NVDA → Preferências → Definições → FreeRadio.

## Músicas Gostadas

Quando a opção **Guardar músicas gostadas em ficheiro de texto** está ativada, as informações de faixa copiadas para a área de transferência ao premir `Ctrl+Win+I` três vezes são também adicionadas linha a linha a `Documents\FreeRadio Recordings\likedSongs.txt`.

Nas estações que difundem metadados ICY, o título e o artista da faixa são guardados diretamente. Nas estações sem metadados ICY, o resultado do reconhecimento Shazam é guardado no mesmo ficheiro — ambas as fontes partilham a mesma lista. O ficheiro é criado automaticamente se não existir; cada entrada é adicionada ao fim do ficheiro e as entradas anteriores nunca são eliminadas.

## Separador Músicas Gostadas

O separador **Músicas Gostadas** no navegador de estações exibe todas as faixas guardadas em `likedSongs.txt`. A lista é automaticamente recarregada a partir do ficheiro sempre que o separador é aberto.

Um campo de **Filtro** acima da lista permite restringir as faixas apresentadas em tempo real. Escreva qualquer parte de um título de canção ou nome de artista e a lista atualiza-se instantaneamente a cada tecla pressionada. O NVDA anuncia o número de resultados correspondentes após cada alteração. Prima a seta `Para baixo` a partir do campo de filtro para mover o foco diretamente para a lista.

Selecionar uma faixa da lista ativa as seguintes ações:

- **Reproduzir no Spotify:** Tenta abrir diretamente a aplicação de ambiente de trabalho do Spotify. Se a aplicação não estiver instalada, recorre ao site do Spotify e reproduz automaticamente o primeiro resultado.
- **Reproduzir no YouTube (`Alt+O`):** Procura a faixa selecionada no YouTube e abre os resultados no navegador predefinido.
- **Mostrar letra:** Obtém e apresenta a letra da faixa selecionada. As letras são obtidas de [lrclib.net](https://lrclib.net) (gratuito, sem conta necessária). É anunciada uma breve mensagem "A obter letra…" enquanto a pesquisa decorre em segundo plano. Se forem encontradas letras, abrem-se numa caixa de diálogo só de leitura onde pode lê-las com o NVDA e copiá-las para a área de transferência. Se não forem encontradas letras, o NVDA anuncia-o. O botão é temporariamente desativado enquanto uma obtenção está em curso para evitar pedidos duplicados.
- **Remover (`Alt+M`):** Elimina a faixa selecionada de `likedSongs.txt` e atualiza a lista. A tecla `Delete` também aciona este botão quando a lista está em foco.
- **Atualizar (`Alt+E`):** Recarrega a lista a partir do ficheiro.

Os botões Spotify, YouTube, Mostrar letra e Remover só estão ativos quando uma faixa real é selecionada na lista.

### Serviço de letras

O FreeRadio utiliza o [lrclib.net](https://lrclib.net) para obter letras — uma base de dados gratuita e aberta que não requer chave de API nem conta. O processo de pesquisa analisa a cadeia de faixas armazenada em `likedSongs.txt` e tenta consultas progressivamente mais amplas até encontrar letras:

1. Correspondência exata com o nome completo do artista e o título limpo (sufixos de ruído como "Remastered", "Live" ou etiquetas de ano são removidos antes da pesquisa).
2. Correspondência exata com o nome completo do artista e o título original (se a limpeza o alterou).
3. Correspondência exata com apenas o primeiro nome de artista e o título limpo (para cadeias com múltiplos artistas, como "Artista A & Artista B").
4. Pesquisa difusa com o primeiro nome de artista e o título limpo.
5. Pesquisa difusa com a cadeia de faixa bruta como último recurso.

Quando há letras em texto simples disponíveis, são apresentadas tal como estão. Quando apenas estão disponíveis letras LRC sincronizadas temporalmente, os carimbos de tempo são removidos e o texto simples é apresentado. As faixas instrumentais são reportadas como não encontradas.


## Reprodução

Ordem de prioridade dos backends:

1. **BASS** — o backend principal e predefinido. Não é necessária instalação separada; está incluído no complemento. O BASS envia o áudio diretamente para a pilha de áudio do Windows e aparece no misturador de volume do Windows como uma fonte de áudio independente com o nome "pythonw.exe", separada do NVDA. Isto significa que o áudio do FreeRadio circula num canal completamente separado do sintetizador de voz do NVDA: o rádio não é interrompido, não se mistura nem é afetado pelas definições de áudio do NVDA enquanto este fala. O utilizador pode ajustar o volume do rádio independentemente do NVDA no Misturador de Volume do Windows. Suporta HTTP, HTTPS e a maioria dos formatos de transmissão incorporados. O espelho de áudio só está disponível com este backend.
2. **VLC** — assume o controlo se o BASS falhar. Pesquisado automaticamente nas localizações de instalação comuns, pastas de perfil de utilizador e no PATH do sistema.
3. **PotPlayer** — tentado se o VLC não for encontrado. Pesquisado automaticamente nas localizações de instalação comuns.
4. **Windows Media Player** — utilizado como último recurso; requer que o componente WMP esteja instalado no sistema.

## Verificação de Atualizações

O FreeRadio verifica automaticamente a existência de novas versões através do GitHub.

**Verificação automática:** É executada silenciosamente em segundo plano 15 segundos após o NVDA iniciar. Se for encontrada uma nova versão, é emitida uma notificação; se não for encontrada nenhuma, não é apresentada qualquer mensagem.

**Verificação manual:** Pode ser acionada em qualquer altura em Ferramentas NVDA → FreeRadio → **Verificar Atualizações…**. Quando iniciada desta forma, o resultado é anunciado mesmo que a versão esteja atualizada.

**Quando é encontrada uma atualização:** Abre-se uma caixa de diálogo com o número da versão e a sua versão instalada.

- Se estiver disponível um ficheiro `.nvda-addon` diretamente descarregável na versão do GitHub, é apresentado o botão **Descarregar e Instalar**. Após confirmação, o ficheiro é descarregado em segundo plano, o NVDA anuncia quando o descarregamento inicia e o ecrã de instalação do NVDA abre automaticamente.
- Se não estiver disponível uma ligação de descarregamento direto, é apresentado o botão **Abrir Página** e a página da versão do GitHub abre no browser predefinido.

**Para desativar as verificações automáticas:** Desative a opção **Verificar atualizações automaticamente** em Menu NVDA → Preferências → Definições → FreeRadio.

## Agradecimentos e Créditos

* **Base e Conceitos Originais:** Um sincero agradecimento a **Gary Mp** ([GaryMp/freeradio](https://github.com/GaryMp/freeradio)) pelos conceitos originais do complemento de rádio e pelas estruturas centrais de gestão de favoritos que serviram de base fundacional para este projeto.
* **Ferramentas de IA e LLM:** Reconhecimento grato às ferramentas modernas de Modelos de Linguagem de Grande Escala (LLM) (incluindo Claude, ChatGPT e Gemini) pela assistência durante as fases de desenvolvimento, refatoração de código e implementação de funcionalidades.
* **Serviço de Diretório:** O diretório de estações é fornecido pela [Radio Browser API](https://www.radio-browser.info/).
* **Comunidade:** Um sincero agradecimento a todos os membros da comunidade NVDA e tradutores pelo seu apoio contínuo, feedback e contribuições de localização.

## Licença

GPL v2