import socket
import time
import random

# Arquitetura --> Gerencia a entrada de novos peers e o papel inicial 
# do anfitrião/coordenador no momento de formar a partida.
class GerenciadorDeLobby:
    def __init__(self, ip_local="127.0.0.1", porta_padrao=5000):
        self.ip_local = ip_local
        self.porta_padrao = porta_padrao

    def existe_anfitriao(self):
        teste = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        teste.settimeout(0.5)
        try:
            teste.connect((self.ip_local, self.porta_padrao))
            teste.close()
            return True
        except Exception:
            return False

    def criar_sala(self, jogador, rede):
        while True:
            try:
                total_jogadores = int(input("[Anfitriao] Quantos jogadores terao na partida (minimo 6)? ").strip())
                if total_jogadores >= 6:
                    break
                else:
                    print("> O jogo exige no minimo 6 jogadores para balanceamento de papeis!")
            except ValueError:
                print("> Entrada invalida! Digite um numero inteiro.")

        print(f"[SISTEMA] Voce e o Lider (ID 0). Aguardando {total_jogadores - 1} jogadores...")
        
        jogador.tabela_peers[0] = {"ip": self.ip_local, "porta": self.porta_padrao, "status": "VIVO"}
        
        while len(jogador.tabela_peers) < total_jogadores:
            time.sleep(1)
            
        print("[SISTEMA] Todos conectados! Distribuindo papeis e iniciando...")
        
        papeis_base = ["Zumbi", "Zumbi", "Zumbi", "Caçador", "Médico", "Civil"]
        if total_jogadores > 6:
            papeis_extras = [random.choice(["Zumbi", "Caçador", "Médico", "Civil"]) for _ in range(total_jogadores - 6)]
            todos_papeis = papeis_base + papeis_extras
        else:
            todos_papeis = list(papeis_base)
            
        random.shuffle(todos_papeis)
        ids_ordenados = sorted(jogador.tabela_peers.keys())
        
        for index, pid in enumerate(ids_ordenados):
            papel_atribuido = todos_papeis[index]
            dados = jogador.tabela_peers[pid]
            dados["papel_secreto"] = papel_atribuido
            dados["papel_conhecido"] = papel_atribuido
            
        jogador.definir_papel(jogador.tabela_peers[0]["papel_secreto"])
        jogador.tabela_peers[0]["hash_papel"] = jogador.hash_do_papel

        for pid, dados in jogador.tabela_peers.items():
            msg = {
                "tipo": "INICIAR_PARTIDA", 
                "seu_id": pid, 
                "tabela": jogador.tabela_peers,
                "papel_atribuido": dados["papel_secreto"]
            }
            if pid == 0:
                rede.rotear_evento(msg)
            else:
                rede.enviar_json(dados["ip"], dados["porta"], msg)

    def entrar_na_sala(self, jogador, rede):
        print("[SISTEMA] Conectando ao Lobby e aguardando papeis...")
        while jogador.id is None or jogador.papel_secreto is None:
            rede.enviar_json(
                self.ip_local, 
                self.porta_padrao, 
                {"tipo": "ENTRAR_LOBBY", "ip": self.ip_local, "porta": jogador.porta, "hash_papel": jogador.hash_do_papel}
            )
            time.sleep(1)