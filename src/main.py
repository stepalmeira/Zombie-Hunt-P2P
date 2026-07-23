import sys
import socket
from jogador import Jogador
from rede import GerenciadorDeRede
from jogo import MotorDoJogo
from eleicao import GerenciadorDeEleicao
from lobby import GerenciadorDeLobby
from rodada import GerenciadorDeRodada

IP_LOCAL = "127.0.0.1"
PORTA_PADRAO_LOBBY = 5000

def main():
    print("--- ZOMBIE HUNT P2P ---")
    
    # 1. Instancia os gerenciadores de serviço
    eleicao = GerenciadorDeEleicao()
    lobby = GerenciadorDeLobby(IP_LOCAL, PORTA_PADRAO_LOBBY)
    rodada_exec = GerenciadorDeRodada(IP_LOCAL, eleicao)

    # 2. Inicialização de Jogador e Rede
    if not lobby.existe_anfitriao():
        jogador = Jogador(IP_LOCAL, PORTA_PADRAO_LOBBY, eh_anfitriao=True)
        rede = GerenciadorDeRede(jogador)
        lobby.criar_sala(jogador, rede)
    else:
        # Descobre uma porta livre aleatória para o peer cliente
        temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp.bind((IP_LOCAL, 0))
        sua_porta = temp.getsockname()[1]
        temp.close()
        
        jogador = Jogador(IP_LOCAL, sua_porta, eh_anfitriao=False)
        rede = GerenciadorDeRede(jogador)
        lobby.entrar_na_sala(jogador, rede)

    # 3. Loop principal do jogo
    for num_rodada in range(1, 11):
        rodada_exec.executar(jogador, rede, num_rodada)
        
        fim, msg_fim = MotorDoJogo.verificar_fim_de_jogo(
            jogador.tabela_peers, jogador.id, jogador.status, jogador.papel_secreto, num_rodada
        )
        print(f"\n------------------------------------------------")
        print(f"[PLACAR] {msg_fim}")
        print(f"------------------------------------------------")

        if fim: 
            break
            
    print("[SISTEMA] Partida encerrada.")
    sys.exit()

if __name__ == "__main__":
    main()