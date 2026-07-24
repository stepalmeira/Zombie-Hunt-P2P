# 🧟 Zombie Hunt (P2P)
Repositório do projeto desenvolvido na disciplina Desenvolvimento de Sistemas de Informação Distribuídos | EACH USP (2026). O projeto trata-se de um jogo multiplayer inspirado no jogo “Zombie Hunt” da série Alice in Borderland, implementado em arquitetura peer-to-peer, no qual os jogadores se conectam diretamente sem servidor central.

## 🃏 Dinâmica do Jogo
Nosso projeto se baseia nas regras do jogo Zombie Hunt, como explicadas no episódio 2 da 3ª terporada de Alice in Borderland.

[![Vídeo regras do Jogo Zombie Hunt | YouTube](assets/thumbnail.png)](https://www.youtube.com/watch?v=p1aUgwMgKhU)


Um número N de participantes se conectam simultaneamente. Para cada participante é sorteado um papel no início do jogo: **Zumbi**, **Caçador**, **Médico** ou **Civil**, que deve ser mantido em segredo. Cada jogador inicia com um deck de cartas numeradas de 1 a 10. A cada rodada, uma dupla de jogadores é sorteada para batalharem entre si. A batalha consiste na escolha de uma carta de seu deck, vence o jogador que lançar a carta de maior valor. As possibilidades de ataque são:

- **Zumbi vence de Humano (Caçador/Médico/Civil)** → O Humano se torna um zumbi.
- **Caçador vence de Zumbi** → O zumbi morre.
- **Médico vence de Zumbi** → O zumbi se torna Civil.
- **Civil vence qualquer um (Zumbi/Médico/Caçador/Civil)** → Nada acontece, ambos permanecem vivos.
- **Caçador vence outro Humano (Médico/Civil)** → O Médico/Civil morre.
- **Médico vence outro Humano (Civil/Caçador)** → Nada acontece, ambos permanecem vivos.
- **Dois jogadores do mesmo papel se enfrentam** → O perdedor perde apenas a carta jogada. (exemplo: Zumbi vs Zumbi ou Caçador vs Caçador resulta apenas em perda de carta).

Caso ambos joguem cartas do mesmo valor, ninguém vence a rodada, apenas perdem do deck a carta lançada. Ao final de cada rodada, é revelado a todos o número de zumbis e humanos vivos. A partida termina quando um time tiver dizimado completamente o outro ou ao final de 10 rodadas, quando todos os jogadores já usaram todas as suas cartas. O time que tiver mais sobreviventes (Humanos vs. Zumbis), vence.

<p align="center">
  <img src="assets/personagens.png" alt="Alt text" width="500">
</p>


---

## 🏗️ Arquitetura
- **Arquitetura:** O sistema seguirá o modelo peer-to-peer (P2P), ou seja, sem servidor central. Cada jogador atua como cliente e servidor ao mesmo tempo. Usaremos uma arquitetura **P2P não-estruturada** com uma topologia de rede de **Full mesh/malha completa**, ou seja, durante o jogo todos os peers se conectam diretamente com todos. Para implementar isso usaremos uma tabela para guardar os dados e status dos outros peers da rede.
- **Arquitetura de Software:** O sistema é estruturado em **4 camadas** distribuídas em **7 módulos principais**:

  - **1. Aplicação & Orquestração**
    - `main.py` → Entrypoint do programa. Inicializa os serviços, define a porta de execução (anfitrião ou cliente) e orquestra o loop principal das rodadas e encerramento.

  - **2. Lógica de Jogo**
    - `rodada.py` (GerenciadorDeRodada) → Controla a dinâmica, a sincronização de fases e a sequência de ações a cada rodada da partida.
    - `jogo.py` (MotorDoJogo) → Regras puras da partida, incluindo a validação de regras e verificação das condições de vitória/fim de jogo.

  - **3. Infraestrutura & Comunicação P2P**
    - `lobby.py` (GerenciadorDeLobby) → Responsável pela descoberta da rede, verificação de anfitrião existente e entrada de novos peers na sala.
    - `eleicao.py` (GerenciadorDeEleicao) → Implementa o algoritmo de consenso distribuído para votações secretas e reeleição do coordenador em caso de falhas.
    - `rede.py` (GerenciadorDeRede) → Camada de baixo nível responsável por sockets TCP, concorrência com threads, envio/recebimento de JSON e controle de timeouts.

  - **4. Modelo de Estado**
    - `jogador.py` (Jogador) → Entidade principal do nó local. Armazena a identidade do jogador (IP, porta, ID), status (vivo/morto), papel secreto e a tabela de peers.

## 🗣️ Comunicação
- **Tipo de comunicação:** TCP para garantir a entrega das mensagens.
- Envio das mensagens pela rede será **assíncrono**, ou seja, não bloqueante.
- Usaremos **conexões duradouras** entre os nós durante toda a partida.
- O **formato de mensagens** entre os peers (estado do jogo, ataque, etc) será **JSON**.



## 🧵 Processos
- Usaremos **threads** no módulo de rede para ficar escutando todas as mensagens enviadas pela rede.
- Servidores (os peers) serão **stateful**, ou seja, guardam memória sobre as conexões e estado do jogo.


## 🕑️ Coordenação
- Vamos usar o método de **sincronização de barreira** para **sincronizar** os resultados das batalhas ao final de cada rodada, garantindo que o jogo só passa pra rodada 2 depois que todos terminarem os duelos da rodada 1.


## ☝️ Nomeação
- Os **nós (jogadores)** devem ser nomeados. Usaremos **nomeação plana**, identificando os jogadores com um **ID** associado a seu **endereço de IP e porta**.
- Para resolução de nomes, como a rede é pequena e Full Mesh (todos conhecem todos), usaremos uma tabela simples para associar ID e endereço do peer.
- **Descoberta de Peers**: Para a inicialização da rede, utilizaremos o modelo de **nó anfitrião**. Um dos jogadores inicia como anfitrião recebendo as conexões iniciais, ele será o ID 0. Os outros jogadores se conectam inicialmente apenas ao IP do anfitrião. Ao iniciar a partia, o anfitrião envia um JSON para todos contendo a tabela com a lista completa de IPs, portas e IDs de todos os conectados. A partir daí, os nós usam a lista para abrir conexões TCP diretas entre si, formando a malha P2P e dispensando o anfitrião de qualquer papel especial no jogo.

## 👬 Replicação e Consistência
- O estado do jogo é **completamente replicado** em todos os nós, ou seja, todos têm uma copia exata do estado do jogo.
- Para manter os **papéis em segredo sem violar a replicação**, cada peer criptografa seu papel inicial com uma palavra secreta (senha) e distribui o dado criptografado para a rede. *O estado é replicado para todos, mas só é descriptografado localmente pelos outros peers quando um jogador morre, se transforma, ou precisa revelar seu papel durante a resolução de uma batalha.*
- Para garantir a **consistência**, ao final de cada rodada, todos os peers trocam informações de quem morreu ou está vivo. Todos devem atualizar suas informações antes da próxima rodada começar.

## 🚧 Tolerância a falhas
- **Falhas de crash**
  - **Queda de oponente →** Se o adversário cai durante o duelo, o peer sobrevivente vence automaticamente por W.O.
  - **Queda do Líder →** Eleição automática transfere as responsabilidades ao próximo menor ID ativo (algoritmo de bully) 

- **Falhas bizantinas (Commit-Reveal Scheme):**
  - **Commit:** Envio do hash SHA-256(carta + salt) para lacrar a escolha
  - **Reveal:** Envio da carta original, salt e papel secreto para verificação

---

## 👨‍💻 Autores
 
- [Stefanie Santos](https://github.com/stepalmeira)
- [Pedro Nunes](https://github.com/pedr0nunes)