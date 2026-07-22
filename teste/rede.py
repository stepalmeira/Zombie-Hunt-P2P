import socket
import threading
import json

class GerenciadorDeRede:
    def __init__(self, jogador):
        self.jogador = jogador
        self.commits_recebidos = {}
        self.reveals_recebidos = {}
        self.ordem_rodada = None
        self.resultados_rodada = []
        self.tabela_atualizada = False
        
        # [Conceito: Sockets / Mensagens Transientes] Abstração da camada de transporte
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.bind((self.jogador.ip, self.jogador.porta))
        self.servidor.listen(10)
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
        except Exception: pass
        finally: conexao.close()

    def enviar_json(self, ip, porta, dados_dict, timeout=4):
        # [Conceito: Detecção de Falhas] Timeout configurado para evitar travamentos
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.settimeout(timeout)
            cliente.connect((ip, int(porta)))
            msg = json.dumps(dados_dict) + "\n"
            cliente.sendall(msg.encode('utf-8'))
            cliente.close()
            return True
        except Exception:
            return False

    def rotear_evento(self, msg):
        tipo = msg.get("tipo")
        if tipo == "ENTRAR_LOBBY":
            # Verifica se essa combinação de IP e Porta já foi cadastrada
            ja_cadastrado = any(
                p["ip"] == msg["ip"] and p["porta"] == msg["porta"]
                for p in self.jogador.tabela_peers.values()
            )
            
            # Só cadastra se for uma nova conexão de fato
            if not ja_cadastrado:
                novo_id = max(self.jogador.tabela_peers.keys()) + 1 if self.jogador.tabela_peers else 1
                print(f"> Novo jogador conectado (ID: {novo_id})")
                self.jogador.tabela_peers[novo_id] = {
                    "ip": msg["ip"], "porta": msg["porta"],
                    "status": "VIVO", "hash_papel": msg["hash_papel"]
                }

        elif tipo == "INICIAR_PARTIDA":
            self.jogador.tabela_peers = {int(k): v for k, v in msg["tabela"].items()}
            self.jogador.id = msg["seu_id"]
            self.jogador.id_lider = 0
            self.jogador.definir_papel(msg["papel_atribuido"])

            # Dicionário mapeando cada papel ao seu respectivo emoji
            emojis = {  
                "Zumbi": "🧟",
                "Civil": "🧍",
                "Caçador": "🏹",
                "Médico": "🩺"
            }
            emoji_papel = emojis.get(self.jogador.papel_secreto, "")

            print(f"\n=================================================")
            print(f"> Partida iniciada. Seu ID: {self.jogador.id} | Papel: {self.jogador.papel_secreto} {emoji_papel}")
            print(f"=================================================")

        elif tipo == "ORDEM_RODADA":
            self.ordem_rodada = msg
        elif tipo == "PING":
            pass # Só de o nó receber e aceitar a conexão prova que ele está vivo
        elif tipo == "COMMIT":
            chave = (msg["rodada"], msg["id_remetente"])
            self.commits_recebidos[chave] = msg["hash_jogada"]
        elif tipo == "REVEAL":
            chave = (msg["rodada"], msg["id_remetente"])
            self.reveals_recebidos[chave] = msg
        elif tipo == "RESULTADO_DUELO":
            self.resultados_rodada.append(msg)
        elif tipo == "ATUALIZAR_TABELA":
            self.jogador.tabela_peers = {int(k): v for k, v in msg["tabela"].items()}
            self.tabela_atualizada = True
        elif tipo == "NOVO_LIDER":
            self.jogador.id_lider = msg["novo_lider"]
            print(f"> Jogador ID {msg['novo_lider']} assumiu como novo Lider.")


    # Tenta enviar um PING direto para checar se o peer está respondendo
    def esta_vivo(self, ip, porta):
        return self.enviar_json(ip, porta, {"tipo": "PING"}, timeout=1.5)  