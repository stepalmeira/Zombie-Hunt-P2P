import os
import time
from jogo import MotorDoJogo

# Arquitetura --> Executa as interações P2P diretas (duelos entre dois jogadores) 
# e recorre ao Líder para a coordenação geral da rodada.
class GerenciadorDeRodada:
    def __init__(self, ip_local="127.0.0.1", gerenciador_eleicao=None):
        self.ip_local = ip_local
        self.gerenciador_eleicao = gerenciador_eleicao

    def executar(self, jogador, rede, rodada):
        print(f"\n--- RODADA {rodada} --- Suas Cartas: {jogador.deck}")
        
        # 1. LÍDER FORMA AS DUPLAS
        if jogador.id == jogador.id_lider:
            tabela_temp = dict(jogador.tabela_peers)
            tabela_temp[jogador.id] = {"ip": self.ip_local, "porta": jogador.porta, "status": jogador.status}
            duplas, folga = MotorDoJogo.formar_duplas(tabela_temp)
            
            msg_ordem = {"tipo": "ORDEM_RODADA", "rodada": rodada, "duplas": duplas, "folga": folga}
            rede.ordem_rodada = msg_ordem 
            
            for pid, d in jogador.tabela_peers.items():
                if pid != jogador.id and d["status"] == "VIVO":
                    rede.enviar_json(d["ip"], d["porta"], msg_ordem)
                    
        # 2. AGUARDA A ORDEM DA RODADA
        while rede.ordem_rodada is None or rede.ordem_rodada.get("rodada") != rodada:
            if jogador.id == jogador.id_lider:
                tabela_temp = dict(jogador.tabela_peers)
                tabela_temp[jogador.id] = {"ip": self.ip_local, "porta": jogador.porta, "status": jogador.status}
                duplas, folga = MotorDoJogo.formar_duplas(tabela_temp)
                
                msg_ordem = {"tipo": "ORDEM_RODADA", "rodada": rodada, "duplas": duplas, "folga": folga}
                rede.ordem_rodada = msg_ordem 
                
                for pid, d in jogador.tabela_peers.items():
                    if pid != jogador.id and d["status"] == "VIVO":
                        rede.enviar_json(d["ip"], d["porta"], msg_ordem)
                break

            lider_id = jogador.id_lider
            lider_dados = jogador.tabela_peers.get(lider_id)
            if not lider_dados or not rede.esta_vivo(lider_dados["ip"], lider_dados["porta"]):
                self.gerenciador_eleicao.iniciar_eleicao(jogador, rede)
                continue
            time.sleep(0.5)
            
        ordem = rede.ordem_rodada
        rede.ordem_rodada = None
        
        meu_adv = None
        for p1, p2 in ordem["duplas"]:
            if p1 == jogador.id: meu_adv = p2
            elif p2 == jogador.id: meu_adv = p1
            
        # 3. DUELO P2P
        # Coordenação --> Orquestra o protocolo Commit-Reveal, onde ambos os oponentes primeiro trocam os hashes 
        # para garantir a honestidade e só revelam as cartas reais após ambos confirmarem o recebimento dos commits.
        if jogador.id == ordem["folga"] or jogador.status != "VIVO" or meu_adv is None:
            print("> Voce esta de folga nesta rodada.")
        else:
            adv_dados = jogador.tabela_peers[meu_adv] if meu_adv != jogador.id else {"ip": self.ip_local, "porta": jogador.porta}
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
                    os._exit(0)
            
            # Tolerância a Falhas --> Em Duelos P2P, é detectada a falta de resposta do oponente durante o 
            # duelo e concede Vitória por W.O. ao peer remanescente.
            if not rede.esta_vivo(adv_dados["ip"], adv_dados["porta"]):
                print(f"\n[SISTEMA] Oponente (ID {meu_adv}) desconectou! VITORIA POR W.O.!")
                jogador.tabela_peers[meu_adv]["status"] = "ELIMINADO"
            else:
                hash_jogada, salt = jogador.gerar_commit_jogada(minha_carta)
                rede.enviar_json(adv_dados["ip"], adv_dados["porta"], {
                    "tipo": "COMMIT",
                    "rodada": rodada,
                    "id_remetente": jogador.id,
                    "hash_jogada": hash_jogada
                })
                
                chave = (rodada, meu_adv)
                while chave not in rede.commits_recebidos:
                    if not rede.esta_vivo(adv_dados["ip"], adv_dados["porta"]):
                        break
                    time.sleep(0.5)
                    
                if chave not in rede.commits_recebidos:
                    print(f"\n[SISTEMA] Oponente (ID {meu_adv}) desconectou! VITORIA POR W.O.!")
                    jogador.tabela_peers[meu_adv]["status"] = "ELIMINADO"
                else:
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
                        res, consq = MotorDoJogo.resolver_combate(jogador.papel_secreto, adv_reveal["papel"], minha_carta, adv_reveal["carta"])

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
                                msg_consequencia = "Arrasou! Voce atacou um Zumbi e ele foi eliminado!"
                            elif consq == "VIRAR_ZUMBI":
                                msg_consequencia = "Voce infectou o oponente! Agora ele virou zumbi! 🧟"
                            elif consq == "VIRAR_CIVIL":
                                msg_consequencia = "Arrasou! Voce curou um zumbi! Agora ele eh um civil! 🧍"
                            else:
                                msg_consequencia = "Sua vitoria foi limpa e sem alteracoes de papéis."
                        else:
                            msg_consequencia = "Cartas iguais! Nada mudou nesta rodada."

                        print(f"\n> RESULTADO: Voce {res} o duelo! (Sua: {minha_carta} | Oponente: {adv_reveal['carta']})")
                        print(f"> {msg_consequencia}")
                    
        # 4. SINCRONIZAÇÃO DE BARREIRA REENTRANTE
        resultado_parcial = {"id": jogador.id, "status": jogador.status, "papel": jogador.papel_secreto}
        
        while True:
            if jogador.id == jogador.id_lider:
                if not any(r["id"] == jogador.id for r in rede.resultados_rodada):
                    rede.resultados_rodada.append(resultado_parcial)
                
                vivos = [pid for pid, d in jogador.tabela_peers.items() if d["status"] == "VIVO"]
                if jogador.status == "VIVO" and jogador.id not in vivos: 
                    vivos.append(jogador.id)
                
                while True:
                    ids_recebidos = {r["id"] for r in rede.resultados_rodada}
                    faltantes = [pid for pid in vivos if pid not in ids_recebidos]
                    
                    if not faltantes:
                        break
                        
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
                
                # Replicação e Consistência --> Na fase final da rodada, todos os sobreviventes enviam seus resultados para o líder. 
                # O líder aguarda todos responderem (barreira de sincronização) e realiza um broadcast ATUALIZAR_TABELA, garantindo 
                # consistência forte e simultânea em toda a rede ao fim de cada ciclo.
                msg_sync = {"tipo": "ATUALIZAR_TABELA", "tabela": jogador.tabela_peers}
                for pid, d in jogador.tabela_peers.items():
                    if pid != jogador.id and d["status"] == "VIVO":
                        rede.enviar_json(d["ip"], d["porta"], msg_sync)
                break
            else:
                lider_id_atual = jogador.id_lider
                lider_dados = jogador.tabela_peers.get(lider_id_atual)
                
                if lider_dados and rede.esta_vivo(lider_dados["ip"], lider_dados["porta"]):
                    rede.enviar_json(lider_dados["ip"], lider_dados["porta"], {"tipo": "RESULTADO_DUELO", **resultado_parcial})
                else:
                    self.gerenciador_eleicao.iniciar_eleicao(jogador, rede)
                    continue
                
                # Tolerância a Falhas --> Durante a mudança de líder: Se o líder cai no meio de uma rodada, elege o novo líder sem perder a 
                # rodada atual e re-executa a distribuição de ordens ou a barreira de resultados perfeitamente.
                while not rede.tabela_atualizada:
                    if jogador.id_lider != lider_id_atual or not rede.esta_vivo(jogador.tabela_peers[jogador.id_lider]["ip"], jogador.tabela_peers[jogador.id_lider]["porta"]):
                        self.gerenciador_eleicao.iniciar_eleicao(jogador, rede)
                        break
                    time.sleep(0.5)
                    
                if rede.tabela_atualizada:
                    rede.tabela_atualizada = False
                    break