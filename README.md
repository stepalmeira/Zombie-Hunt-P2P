# 🧟 Zombie Hunt (P2P)
Repositório do projeto desenvolvido na disciplina Desenvolvimento de Sistemas de Informação Distribuídos | EACH USP (2026). O projeto trata-se de um jogo multiplayer inspirado no jogo “Zombie Hunt” da série Alice in Borderland, implementado em arquitetura peer-to-peer, no qual os jogadores se conectam diretamente sem servidor central.

## 🃏 Dinâmica do Jogo
Um número par de jogadores se conectam ao jogo. No início do jogo, são distribuídas 7 cartas numéricas (cartas de baralho, de Às a Reis) e 1 carta especial obrigatória para cada jogador. Essa carta especial pode ser de três tipos: 
- Zumbi
- Vacina
- Escopeta

Aos jogadores que receberam a carta de Zumbi, é atribuído o estado de **infectado**. Os demais jogadores desconhecem o estado inicial dos oponentes.

O jogo se divide em **rodadas** nas quais os jogadores batalham em duplas escolhidas aleatoriamente. A cada batalha, cada um dos jogadores deve jogar uma carta contra o seu oponente. As possibilidades de jogadas dentro de uma batalha são:
1. **Ambos os jogadores jogam uma carta numérica contra o oponente**: Vence quem jogar a carta de número maior, tomando pra si a carta do perdedor. No caso das cartas possuirem o mesmo número, ninguém vence a rodada, ambos perdem suas cartas.
2. **Ambos os jogadores jogam cartas especiais**:
    - ***Vacina cura Zumbi**: Estado do jogador muda de infectado para humano. Ambos os jogadores perdem suas cartas especiais.
    - **Escopeta mata Zumbi**: O jogador que morreu é desconectado do jogo, diminuindo a população de zumbis. O jogador que jogou a escopeta, perde essa carta.
    - **Vacina com escopeta**: Nada acontece. Ambos perdem suas cartas.

3. **Carta especial contra carta numérica:**
    - Um jogador joga uma carta Zumbi e o oponente joga um carta numérica: Nesse caso, o jogador Zumbi infecta o oponente e, a partir de então, ele ganha uma carta Zumbi e passa a ter o poder de infectar outros.
    - Escopeta ou vacina contra carta numérica: O jogador que jogou a carta especial apenas perde a carta. Nada acontece.



---

## 🏗️ Arquitetura
[...]

## 🗣️ Comunicação
[...]

## ☝️ Nomeação
[...]

## 🕑️ Coordenação
[...]

## 🕑️ Processos
[...]


<!--

## 📦 Dependências de software

#### Backend
- Python

#### Frontend
- [...]

-->
---
## ❓️ Dúvidas e Ajuda

Ficou interessado pelo projeto e está com alguma dúvida? Ficou perdido ou confuso? Ou quer sugerir alguma melhoria ao projeto?

Incentivamos que você nos procure. **Abra uma Issue** na página de Issues contando seu problema/sugestão.

## 👨‍💻 Autores
 
- [Stefanie Palmeira](https://github.com/stepalmeira)
- [Pedro Nunes](https://github.com/pedr0nunes)