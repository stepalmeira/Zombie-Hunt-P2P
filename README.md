# 🧟 Zombie Hunt (P2P)
Repositório do projeto desenvolvido na disciplina Desenvolvimento de Sistemas de Informação Distribuídos | EACH USP (2026). O projeto trata-se de um jogo multiplayer inspirado no jogo “Zombie Hunt” da série Alice in Borderland, implementado em arquitetura peer-to-peer, no qual os jogadores se conectam diretamente sem servidor central.

## 🃏 Dinâmica do Jogo
Nosso projeto se baseia nas regras do jogo Zombie Hunt, como explicadas no episódio 2 da 3ª terporada de Alice in Borderland.

[![Vídeo regras do Jogo Zombie Hunt | YouTube](assets/thumbnail.png)](https://www.youtube.com/watch?v=p1aUgwMgKhU)

Um número N de participantes se conectam simultaneamente. Para cada participante é sorteado um papel no início do jogo: **Zumbi**, **Caçador**, **Médico** ou **Civil**, que deve ser mantido em segredo. Cada jogador inicia com um deck de cartas numeradas de 1 a 10. A cada rodada, uma dupla de jogadores é sorteada para batalharem entre si. A batalha consiste na escolha de uma carta de seu deck, vence o jogador que lançar a carta de maior valor. As possibilidades de ataque são:

- **Zumbi vence de Humano (Caçador/Médico/Civil)** → O Humano se torna um zumbi.
- **Caçador vence de Zumbi** → O zumbi morre.
- **Médico vence de Zumbi** → O zumbi se torna humano.
- **Civil vence qualquer um (Zumbi/Médico/Caçador/Civil)** → Nada acontece, ambos permanecem vivos.
- **Caçador vence outro Humano (Médico/Civil)** → O Médico/Civil morre.
- **Médico vence outro Humano (Civil/Caçador)** → Nada acontece, ambos permanecem vivos.

Caso ambos joguem cartas do mesmo valor, ninguém vence a rodada, apenas perdem do deck a carta lançada. Ao final de cada rodada, é revelado a todos o número de zumbis e humanos vivos. A partida termina quando um time tiver dizimado completamente o outro ou ao final de 10 rodadas, quando todos os jogadores já usaram todas as suas cartas. O time que tiver mais sobreviventes (Humanos vs. Zumbis), vence.

---

## 🏗️ Arquitetura
- **Arquitetura:** O sistema seguirá o modelo peer-to-peer (P2P), ou seja, sem servidor central. Cada jogador atua como cliente e servidor ao mesmo tempo. Usaremos uma arquitetura **P2P não-estruturada** com uma topologia de rede de **Full mesh/malha completa**, ou seja, durante o jogo todos os peers se conectam diretamente com todos.
- **Arquitetura de Software:** Dividiremos em módulos:
    - **Jogador** → Classe contendo atributos e métodos do jogador (id, papel, deck de cartas, etc)  
    - **Jogo** → Lógica do jogo
    - **Rede** → Logica de conexão e comunicação entre peers


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
- Usaremos um **algoritmo de consenso decentralizado baseado em semente**: Cada peer gera um valor aleatório que é somado e, do valor resultante (a semente), é calculado o módulo, que garantidamente será um valor entre 0 e N-1 (sendo N o número de jogadores da partida), permitindo selecionar um jogador de forma aleatória e confiável.


## ☝️ Nomeação
- Os **nós (jogadores)** devem ser nomeados. Usaremos **nomeação plana**, identificando os jogadores com um **ID** associado a seu **endereço de IP e porta**.
- Para resolução de nomes, como a rede é pequena e Full Mesh (todos conhecem todos), usaremos uma tabela simples para associar ID e endereço do peer.

## 👬 Replicação e Consistência
- O estado do jogo é **completamente replicado** em todos os nós, ou seja, todos têm uma copia exata do estado do jogo.
- Para garantir a **consistência**, ao final de cada rodada, todos os peers trocam informações de quem morreu ou está vivo. Todos devem atualizar suas informações antes da próxima rodada começar.

## 🚧 Tolerância a falhas
- Em caso de **crash** (peer desconectar no meio da partida), o sistema marca o jogador como “Eliminado” se der timeout.

<!--

## 📦 Dependências de software

#### Backend
- Python

#### Frontend
- [...]

-->
---

## 👨‍💻 Autores
 
- [Stefanie Santos](https://github.com/stepalmeira)
- [Pedro Nunes](https://github.com/pedr0nunes)