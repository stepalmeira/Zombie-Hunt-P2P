import socket
import threading
import json
import time

class GerenciadorDeRede:
    def __init__(self, jogador):
        self.jogador = jogador # Recebe a instância do Jogador

        # CAIXAS DE CORREIO TEMPORÁRIAS PARA OS DUELOS
        self.commit_recebido = None  # Guarda o hash recebido do oponente
        self.reveal_recebido = None  # Guarda a carta e senha recebidas do oponente
        self.rodada_finalizada_peers = set() # Barreira: guarda IDs de quem já acabou a rodada
        
        # Configura o Servidor TCP para escutar
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.bind((self.jogador.ip, self.jogador.porta))
        self.servidor.listen(10)
        
        # Thread de escuta em segundo plano
        threading.Thread(target=self._escutar, daemon=True).start()

    def _escutar(self):
        while True:
            try:
                conexao, _ = self.servidor.accept()
                threading.Thread(target=self._tratar_mensagem, args=(conexao,), daemon=True).start()
            except Exception:
                break

    def _tratar_mensagem(self, conexao):
        try:
            dados = b""
            while not dados.endswith(b"\n"):
                parte = conexao.recv(1024)
                if not parte: break
                dados += parte
                
            if dados:
                msg = json.loads(dados.decode('utf-8').strip())
                self.rotear_evento(msg)
        except Exception as e:
            print(f"❌ Erro na rede: {e}")
        finally:
            conexao.close()

    # Envia mensagem TCP com TIMEOUT de segurança contra falhas
    def enviar_json(self, ip, porta, dados_dict, timeout=5):
        """Envia mensagem TCP com TIMEOUT de segurança contra falhas"""
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.settimeout(timeout) # 🛡️ Aplicação da nossa regra de Tolerância a Falhas!
            cliente.connect((ip, int(porta)))
            
            msg = json.dumps(dados_dict) + "\n"
            cliente.sendall(msg.encode('utf-8'))
            cliente.close()
            return True
        except socket.timeout:
            print(f"⏰ TIMEOUT: O peer {ip}:{porta} demorou demais para responder!")
            return False
        except Exception:
            return False

    # Recebe o JSON e roteia para a ação correta
    def rotear_evento(self, msg):
        """Recebe o JSON e roteia para a ação correta"""
        tipo = msg.get("tipo")
        
        if tipo == "ENTRAR_LOBBY" and self.jogador.eh_anfitriao:
            novo_id = len(self.jogador.tabela_peers) + 1
            print(f"\n> Novo peer conectado! ID atribuído: {novo_id}")
            self.jogador.tabela_peers[novo_id] = {
                "ip": msg["ip"],
                "porta": msg["porta"],
                "status": "VIVO",
                "hash_papel": msg["hash_papel"]
            }
            
        elif tipo == "INICIAR_PARTIDA":
            self.jogador.tabela_peers = {int(k): v for k, v in msg["tabela"].items()}
            self.jogador.id = msg["seu_id"]
            print(f"\n🎮 PARTIDA INICIADA! Seu ID é {self.jogador.id} e seu papel secreto é {self.jogador.papel_secreto}!")


        # === MENSAGENS DE DUELO (COMMIT-REVEAL) ===
        elif tipo == "COMMIT":
            # O adversário enviou o envelope lacrado!
            self.commit_recebido = msg["hash_jogada"]
            
        elif tipo == "REVEAL":
            # O adversário abriu o envelope!
            self.reveal_recebido = {
                "carta": msg["carta"],
                "salt": msg["salt"],
                "papel": msg["papel"],
                "senha_papel": msg["senha_papel"]
            }
            
        elif tipo == "ATUALIZAR_ESTADO":
            # Um jogador morreu ou se transformou no final do duelo
            id_alvo = msg["id"]
            self.jogador.tabela_peers[id_alvo]["status"] = msg["novo_status"]
            if "novo_papel" in msg:
                self.jogador.tabela_peers[id_alvo]["papel_conhecido"] = msg["novo_papel"]
                
        elif tipo == "FIM_RODADA_PEER":
            # Sincronização de Barreira: um peer avisou que terminou a rodada dele
            self.rodada_finalizada_peers.add(msg["id"])