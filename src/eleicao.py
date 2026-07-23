import sys
import time

# Coordenação --> mplementa uma variação determinística do algoritmo Bully. Quando o líder cai, o sistema varre os 
# IDs do menor para o maior e valida ativamente a vivacidade de cada peer via PING. 
# O primeiro nó realmente ativo é aclamado Líder e envia um broadcast
class GerenciadorDeEleicao:
    @staticmethod
    def iniciar_eleicao(jogador, rede):
        print("\n[SISTEMA] Lider ausente/inativo. Iniciando eleicao...")
        
        todos_ids = sorted(list(jogador.tabela_peers.keys()))
        novo_lider = None
        
        # Testa deterministicamente do menor ID ao maior ID
        for pid in todos_ids:
            if pid == jogador.id:
                if jogador.status == "VIVO":
                    novo_lider = pid
                    break
            else:
                d = jogador.tabela_peers[pid]
                if d["status"] == "VIVO":
                    # Só marca como ELIMINADO se falhar rigorosamente no PING
                    if rede.esta_vivo(d["ip"], d["porta"]):
                        novo_lider = pid
                        break
                    else:
                        print(f"[ELEICAO] Peer ID {pid} nao respondeu ao PING. Marcando como ELIMINADO.")
                        jogador.tabela_peers[pid]["status"] = "ELIMINADO"

        if novo_lider is None:
            print("[ELEICAO] Nenhum peer vivo encontrado. Encerrando jogo.")
            sys.exit()

        antigo_lider = jogador.id_lider
        jogador.id_lider = novo_lider

        if jogador.id == novo_lider:
            if antigo_lider != novo_lider:
                print(f"\n=================================================")
                print(f"[SISTEMA] VOCÊ é o novo Anfitrião/Líder da partida! (ID {jogador.id})")
                print(f"=================================================\n")
                
                msg_novo_lider = {"tipo": "NOVO_LIDER", "novo_lider": novo_lider}
                for pid, d in jogador.tabela_peers.items():
                    if pid != jogador.id and d["status"] == "VIVO":
                        rede.enviar_json(d["ip"], d["porta"], msg_novo_lider)
        else:
            print(f"[ELEICAO] Novo lider confirmado: ID {novo_lider}")