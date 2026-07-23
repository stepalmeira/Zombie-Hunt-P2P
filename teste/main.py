import sys
import time
import socket
import random
from jogador import Jogador
from rede import GerenciadorDeRede
from jogo import MotorDoJogo

IP_LOCAL = "127.0.0.1"
PORTA_PADRAO_LOBBY = 5000

def verificar_se_existe_anfitriao():
    teste = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    teste.settimeout(0.5)
    try:
        teste.connect((IP_LOCAL, PORTA_PADRAO_LOBBY))
        teste.close()
        return True
    except: return False

def iniciar_eleicao(jogador, rede):
    print("\n[SISTEMA] Lider caiu. Iniciando eleicao...")
    if jogador.id_lider in jogador.tabela_peers:
        jogador.tabela_peers[jogador.id_lider]["status"] = "ELIMINADO"
        
    vivos = [pid for pid, d in jogador.tabela_peers.items() if d["status"] == "VIVO"]
    if jogador.status == "VIVO": vivos.append(jogador.id)
    if not vivos: sys.exit()
        
    novo_lider = min(vivos)
    jogador.id_lider = novo_lider
    print(f"[ELEICAO] Novo lider eleito: ID {novo_lider}")



def executar_rodada(jogador, rede, rodada):
    print(f"\n--- RODADA {rodada} --- Suas Cartas: {jogador.deck}")
    
    # 1. LÍDER FORMA AS DUPLAS
    if jogador.id == jogador.id_lider:
        tabela_temp = dict(jogador.tabela_peers)
        tabela_temp[jogador.id] = {"ip": IP_LOCAL, "porta": jogador.porta, "status": jogador.status}
        duplas, folga = MotorDoJogo.formar_duplas(tabela_temp)
        
        # Adiciona o número da rodada na mensagem para validação
        msg_ordem = {"tipo": "ORDEM_RODADA", "rodada": rodada, "duplas": duplas, "folga": folga}
        rede.ordem_rodada = msg_ordem 
        
        for pid, d in jogador.tabela_peers.items():
            if pid != jogador.id and d["status"] == "VIVO":
                rede.enviar_json(d["ip"], d["porta"], msg_ordem)
                
    # 2. TODOS AGUARDAM A ORDEM DO LÍDER PARA A RODADA ATUAL
    while rede.ordem_rodada is None or rede.ordem_rodada.get("rodada") != rodada:
        if jogador.id_lider in jogador.tabela_peers:
            lider = jogador.tabela_peers[jogador.id_lider]
            if not rede.esta_vivo(lider["ip"], lider["porta"]):
                iniciar_eleicao(jogador, rede)
                return executar_rodada(jogador, rede, rodada)
        time.sleep(0.5)
        
    ordem = rede.ordem_rodada
    rede.ordem_rodada = None # Zera a ordem somente APÓS consumir
    
    meu_adv = None
    for p1, p2 in ordem["duplas"]:
        if p1 == jogador.id: meu_adv = p2
        elif p2 == jogador.id: meu_adv = p1
        
    # 3. DUELO P2P
    if jogador.id == ordem["folga"] or jogador.status != "VIVO" or meu_adv is None:
        print("> Relaxa! Voce esta de folga nesta rodada")
    else:
        adv_dados = jogador.tabela_peers[meu_adv] if meu_adv != jogador.id else {"ip": IP_LOCAL, "porta": jogador.porta}
        print(f"> DUELO: Voce (ID {jogador.id}) vs ID {meu_adv}")
        
        while True:
            try:
                escolha = int(input("Escolha uma carta: "))
                if escolha in jogador.deck:
                    minha_carta = escolha
                    jogador.deck.remove(escolha)
                    break
                else:
                    print("> Carta invalida! Escolha uma carta presente no seu deck.")
            except ValueError:
                print("> Entrada invalida! Digite apenas o numero de uma carta.")
            except (KeyboardInterrupt, EOFError):
                print("\n\n[SISTEMA] Peer desconectado forçadamente (Ctrl + C).")
                import os
                os._exit(0)
                
        # Checa se o adversário ainda está vivo antes de trocar mensagens
        if not rede.esta_vivo(adv_dados["ip"], adv_dados["porta"]):
            print(f"\n[SISTEMA] Oponente (ID {meu_adv}) desconectou! VITORIA POR W.O.!")
            jogador.tabela_peers[meu_adv]["status"] = "ELIMINADO"
        else:
            # Tenta enviar o COMMIT
            hash_jogada, salt = jogador.gerar_commit_jogada(minha_carta)
            rede.enviar_json(adv_dados["ip"], adv_dados["porta"], {
                "tipo": "COMMIT",
                "rodada": rodada,
                "id_remetente": jogador.id,
                "hash_jogada": hash_jogada
            })
            
            # Aguarda COMMIT do oponente
            chave = (rodada, meu_adv)
            while chave not in rede.commits_recebidos:
                if not rede.esta_vivo(adv_dados["ip"], adv_dados["porta"]):
                    break
                time.sleep(0.5)
                
            if rede.commits_recebidos is None:
                print(f"\n[SISTEMA] Oponente (ID {meu_adv}) desconectou! VITORIA POR W.O.!")
                jogador.tabela_peers[meu_adv]["status"] = "ELIMINADO"
            else:
                # Tenta enviar o REVEAL
                rede.enviar_json(adv_dados["ip"], adv_dados["porta"], {
                    "tipo": "REVEAL",
                    "rodada": rodada,
                    "id_remetente": jogador.id,
                    "carta": minha_carta,
                    "salt": salt,
                    "papel": jogador.papel_secreto
                })
                
                while chave not in rede.reveals_recebidos:
                    if not rede.esta_vivo(adv_dados["ip"], adv_dados["porta"]):
                        break
                    time.sleep(0.5)

            if chave not in rede.reveals_recebidos:
                print(f"\n[SISTEMA] Oponente (ID {meu_adv}) desconectou! VITORIA POR W.O.!")
                jogador.tabela_peers[meu_adv]["status"] = "ELIMINADO"

            else:
                adv_reveal = rede.reveals_recebidos.pop(chave)
                    
                res, consq = MotorDoJogo.resolver_combate(jogador.papel_secreto,adv_reveal["papel"],minha_carta,adv_reveal["carta"])
    
                # Constrói mensagem de texto amigável baseada na consequência
                msg_consequencia = ""
                if res == "PERDEU":
                    if consq == "MORRER": 
                        jogador.status = "ELIMINADO"
                        msg_consequencia = "Voce foi eliminado da partida!"
                    elif consq == "VIRAR_ZUMBI": 
                        jogador.papel_secreto = "Zumbi"
                        msg_consequencia = "Voce foi infectado e agora e um Zumbi! 🧟"
                    elif consq == "VIRAR_CIVIL": 
                        jogador.papel_secreto = "Civil"
                        msg_consequencia = "Acorda, cara!! Voce foi curado pelo medico e agora e um civil! 🧍"
                    else:
                        msg_consequencia = "Mas nao se preocupe, voce continua vivo e nao foi afetado."
                elif res == "VENCEU":
                    if consq == "MORRER":
                        msg_consequencia = "Arrasou! Voce atacou um Zumbi e ele foi eliminado"
                    elif consq == "VIRAR_ZUMBI":
                        msg_consequencia = "Voce infectou o oponente! Agora ele virou zumbi! 🧟"
                    elif consq == "VIRAR_CIVIL":
                        msg_consequencia = "Arrasou! Voce curou um zumbi! Agora ele eh um civil! 🧍"
                    else:
                        msg_consequencia = "Voce venceu e continua no seu papel"
                else:  # EMPATOU
                    msg_consequencia = "Cartas iguais! Nada mudou nesta rodada."
                    
                print(f"\n> RESULTADO: Voce {res} o duelo! (Sua: {minha_carta} | Oponente: {adv_reveal['carta']})")
                print(f"> {msg_consequencia}")
                    
    # 4. SINCRONIZAÇÃO DE BARREIRA
    resultado_parcial = {"id": jogador.id, "status": jogador.status, "papel": jogador.papel_secreto}
    if jogador.id == jogador.id_lider:
        rede.resultados_rodada.append(resultado_parcial)
    else:
        lider_dados = jogador.tabela_peers.get(jogador.id_lider)
        if not lider_dados or not rede.enviar_json(lider_dados["ip"], lider_dados["porta"], {"tipo": "RESULTADO_DUELO", **resultado_parcial}, timeout=2):
            iniciar_eleicao(jogador, rede)
            lider_dados = jogador.tabela_peers[jogador.id_lider]
            rede.enviar_json(lider_dados["ip"], lider_dados["porta"], {"tipo": "RESULTADO_DUELO", **resultado_parcial})

    if jogador.id == jogador.id_lider:
        vivos = [pid for pid, d in jogador.tabela_peers.items() if d["status"] == "VIVO"]
        if jogador.status == "VIVO" and jogador.id not in vivos: 
            vivos.append(jogador.id)
        
        while True:
            ids_recebidos = {r["id"] for r in rede.resultados_rodada}
            faltantes = [pid for pid in vivos if pid not in ids_recebidos]
            
            if not faltantes:
                break # Todos responderam!
                
            for pid in faltantes:
                d = jogador.tabela_peers[pid]
                if not rede.esta_vivo(d["ip"], d["porta"]):
                    print(f"\n[LIDER] Peer ID {pid} desconectou. Marcando como ELIMINADO.")
                    jogador.tabela_peers[pid]["status"] = "ELIMINADO"
                    rede.resultados_rodada.append({"id": pid, "status": "ELIMINADO", "papel": d.get("papel_conhecido", "Civil")})
            
            vivos = [pid for pid, d in jogador.tabela_peers.items() if d["status"] == "VIVO"]
            time.sleep(0.5)
            
        for res in rede.resultados_rodada:
            if res["id"] in jogador.tabela_peers:
                jogador.tabela_peers[res["id"]]["status"] = res["status"]
                jogador.tabela_peers[res["id"]]["papel_conhecido"] = res["papel"]
        rede.resultados_rodada.clear()
        
        msg_sync = {"tipo": "ATUALIZAR_TABELA", "tabela": jogador.tabela_peers}
        for pid, d in jogador.tabela_peers.items():
            if pid != jogador.id and d["status"] == "VIVO":
                rede.enviar_json(d["ip"], d["porta"], msg_sync)
    else:
        while not rede.tabela_atualizada:
            if not rede.esta_vivo(jogador.tabela_peers[jogador.id_lider]["ip"], jogador.tabela_peers[jogador.id_lider]["porta"]):
                iniciar_eleicao(jogador, rede)
                break
            time.sleep(0.5)
        rede.tabela_atualizada = False
        

def main():
    print("--- ZOMBIE HUNT P2P ---")
    if not verificar_se_existe_anfitriao():
        # Valida o mínimo de 6 jogadores
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
        
        jogador = Jogador(IP_LOCAL, PORTA_PADRAO_LOBBY, eh_anfitriao=True)
        rede = GerenciadorDeRede(jogador)
        jogador.tabela_peers[0] = {"ip": IP_LOCAL, "porta": PORTA_PADRAO_LOBBY, "status": "VIVO"}
        
        while len(jogador.tabela_peers) < total_jogadores:
            time.sleep(1)
            
        print("[SISTEMA] Todos conectados! Distribuindo papeis e iniciando...")
        
        # PROPORÇÃO BALANCEADA PARA 6+ JOGADORES:
        # Metade Zumbis (3) e Metade Humanos (1 Caçador, 1 Médico, 1 Civil)
        papeis_base = ["Zumbi", "Zumbi", "Zumbi", "Caçador", "Médico", "Civil"]
        
        if total_jogadores > 6:
            papeis_extras = [random.choice(["Zumbi", "Caçador", "Médico", "Civil"]) for _ in range(total_jogadores - 6)]
            todos_papeis = papeis_base + papeis_extras
        else:
            todos_papeis = list(papeis_base)
            
        random.shuffle(todos_papeis)
        
        # Atribui ordenadamente para cada ID sequencial (0, 1, 2, 3...)
        ids_ordenados = sorted(jogador.tabela_peers.keys())
        
        for index, pid in enumerate(ids_ordenados):
            papel_atribuido = todos_papeis[index]
            dados = jogador.tabela_peers[pid]
            dados["papel_secreto"] = papel_atribuido
            dados["papel_conhecido"] = papel_atribuido
            
        # Configura o próprio líder (ID 0)
        jogador.definir_papel(jogador.tabela_peers[0]["papel_secreto"])
        jogador.tabela_peers[0]["hash_papel"] = jogador.hash_do_papel

        # Dispara o início para todos
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
    else:
        temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp.bind((IP_LOCAL, 0))
        sua_porta = temp.getsockname()[1]
        temp.close()
        
        jogador = Jogador(IP_LOCAL, sua_porta, eh_anfitriao=False)
        rede = GerenciadorDeRede(jogador)
        
        print("[SISTEMA] Conectando ao Lobby e aguardando papeis...")
        while jogador.id is None or jogador.papel_secreto is None:
            rede.enviar_json(IP_LOCAL, PORTA_PADRAO_LOBBY, {"tipo": "ENTRAR_LOBBY", "ip": IP_LOCAL, "porta": sua_porta, "hash_papel": jogador.hash_do_papel})
            time.sleep(1)

    for rodada in range(1, 11):
        executar_rodada(jogador, rede, rodada)
        fim, msg_fim = MotorDoJogo.verificar_fim_de_jogo(jogador.tabela_peers, jogador.id, jogador.status, jogador.papel_secreto, rodada)
        print(f"\n------------------------------------------------")
        print(f"[PLACAR] {msg_fim}")
        print(f"------------------------------------------------")

        if fim: break
            
    print("[SISTEMA] Partida encerrada.")
    sys.exit()

if __name__ == "__main__":
    main()