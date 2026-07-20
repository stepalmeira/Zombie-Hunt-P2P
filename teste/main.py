# arquivo: main.py
import sys
import time
import socket
from jogador import Jogador
from rede import GerenciadorDeRede
from jogo import MotorDoJogo

IP_LOCAL = "127.0.0.1"
PORTA_PADRAO_LOBBY = 5000

# Tenta conectar na porta padrão (5000) da rede local. Se conseguir, já existe um anfitrião
def verificar_se_existe_anfitriao():
    """Tenta conectar na porta padrão (5000) da rede local. Se conseguir, já existe um anfitrião"""

    teste_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    teste_socket.settimeout(0.5) # Espera no máximo meio segundo
    try:
        teste_socket.connect((IP_LOCAL, PORTA_PADRAO_LOBBY))
        teste_socket.close()
        return True # Conectou, portanto, já existe um anfitrião ativo
    except (ConnectionRefusedError, socket.timeout):
        return False # Não conectou. Eu serei o anfitrião
    

def executar_rodada(jogador, rede, rodada):
    print("\n" + "="*50)
    print(f"🔄 INICIANDO RODADA {rodada} | Suas Cartas: {jogador.deck}")
    print("="*50)
    
    # 1. Sorteio determinístico (todos fazem o mesmo cálculo e concordam)
    duplas, folga = MotorDoJogo.formar_duplas(jogador.tabela_peers, rodada)
    
    # Verifica quem é o meu adversário nesta rodada
    meu_adversario = None
    for p1, p2 in duplas:
        if p1 == jogador.id: meu_adversario = p2
        elif p2 == jogador.id: meu_adversario = p1
        
    if jogador.id == folga:
        print("☕ Você ficou de FOLGA nesta rodada (número ímpar de jogadores vivos)!")
    elif meu_adversario is None or jogador.status != "VIVO":
        print("💀 Você está eliminado e apenas assistirá à rodada.")
    else:
        adv_dados = jogador.tabela_peers[meu_adversario]
        print(f"⚔️ SEU DUELO: Você (ID {jogador.id}) vs. Jogador ID {meu_adversario}")
        
        # 2. Escolha da carta (Interativo no terminal)
        while True:
            try:
                escolha = int(input(f"Escolha uma carta do seu deck {jogador.deck}: "))
                if escolha in jogador.deck:
                    minha_carta = escolha
                    jogador.deck.remove(escolha)
                    break
                print("❌ Carta inválida ou já utilizada!")
            except ValueError:
                print("❌ Digite apenas o número da carta!")
                
        # 3. FASE COMMIT (Envelope Lacrado)
        hash_jogada, salt = jogador.gerar_commit_jogada(minha_carta)
        msg_commit = {"tipo": "COMMIT", "de": jogador.id, "hash_jogada": hash_jogada}
        
        print("🔒 Enviando seu commit (jogada lacrada) para o adversário...")
        rede.enviar_json(adv_dados["ip"], adv_dados["porta"], msg_commit)
        
        # Aguarda receber o commit do oponente
        print("⏳ Aguardando a jogada do adversário...")
        tempo_limite = time.time() + 15 # 15 segundos de timeout
        while rede.commit_recebido is None:
            if time.time() > tempo_limite:
                print("⏰ TIMEOUT: O adversário demorou para jogar! Você venceu por WO.")
                # Reporta queda para a rede
                msg_queda = {"tipo": "ATUALIZAR_ESTADO", "id": meu_adversario, "novo_status": "ELIMINADO"}
                for p in jogador.tabela_peers.values():
                    rede.enviar_json(p["ip"], p["porta"], msg_queda)
                return
            time.sleep(0.5)
            
        print("📩 Commit do adversário recebido! Abrindo os envelopes (Reveal)...")
        
        # 4. FASE REVEAL (Revelar Carta real e Salt)
        msg_reveal = {
            "tipo": "REVEAL",
            "de": jogador.id,
            "carta": minha_carta,
            "salt": salt,
            "papel": jogador.papel_secreto,
            "senha_papel": jogador.senha_do_papel
        }
        rede.enviar_json(adv_dados["ip"], adv_dados["porta"], msg_reveal)
        
        # Aguarda o reveal do oponente
        while rede.reveal_recebido is None:
            time.sleep(0.5)
            
        adv_reveal = rede.reveal_recebido
        
        # 5. VALIDAÇÃO ANTITRAPAÇA (Falha Bizantina!)
        hash_recalculado = jogador.gerar_hash(f"{adv_reveal['carta']}_{adv_reveal['salt']}")
        if hash_recalculado != rede.commit_recebido:
            print("🚨 ALERTA BIZANTINO: O adversário tentou trapacear trocando a carta! Eliminado por fraude.")
            return
            
        # 6. RESOLUÇÃO DO COMBATE
        print(f"\n🃏 Revelação: Você jogou [{minha_carta}] | Oponente jogou [{adv_reveal['carta']}]")
        print(f"🎭 Papel do adversário revelado: {adv_reveal['papel']}")
        
        resultado, consequencia = MotorDoJogo.resolver_combate(
            jogador.papel_secreto, adv_reveal["papel"], minha_carta, adv_reveal["carta"]
        )
        
        print(f"🏁 Resultado do Duelo: Você {resultado}!")
        
        # Aplica consequências
        if consequencia == "MORRER" and resultado == "PERDEU":
            print("💥 Você foi morto pelo Caçador!")
            jogador.status = "ELIMINADO"
            msg_morte = {"tipo": "ATUALIZAR_ESTADO", "id": jogador.id, "novo_status": "ELIMINADO"}
            for pid, p in jogador.tabela_peers.items():
                if pid != jogador.id: rede.enviar_json(p["ip"], p["porta"], msg_morte)
                
        elif consequencia == "VIRAR_ZUMBI" and resultado == "PERDEU":
            print("🧟 Você foi infectado! Agora você é um ZUMBI.")
            jogador.papel_secreto = "Zumbi"
            msg_transf = {"tipo": "ATUALIZAR_ESTADO", "id": jogador.id, "novo_status": "VIVO", "novo_papel": "Zumbi"}
            for pid, p in jogador.tabela_peers.items():
                if pid != jogador.id: rede.enviar_json(p["ip"], p["porta"], msg_transf)
                
        elif consequencia == "VIRAR_CIVIL" and resultado == "PERDEU":
            print("💉 Você foi curado pelo Médico! Agora você é um CIVIL.")
            jogador.papel_secreto = "Civil"
            msg_transf = {"tipo": "ATUALIZAR_ESTADO", "id": jogador.id, "novo_status": "VIVO", "novo_papel": "Civil"}
            for pid, p in jogador.tabela_peers.items():
                if pid != jogador.id: rede.enviar_json(p["ip"], p["porta"], msg_transf)
                
    # 7. SINCRONIZAÇÃO DE BARREIRA (Espera todos acabarem a rodada)
    print("\n🛑 Barreira: Aguardando todos os peers finalizarem a rodada...")
    # Limpa variáveis para a próxima rodada
    rede.commit_recebido = None
    rede.reveal_recebido = None
    
    # Avisa todos que eu acabei minha rodada
    msg_barreira = {"tipo": "FIM_RODADA_PEER", "id": jogador.id}
    rede.rodada_finalizada_peers.add(jogador.id)
    for pid, p in jogador.tabela_peers.items():
        if pid != jogador.id and p["status"] == "VIVO":
            rede.enviar_json(p["ip"], p["porta"], msg_barreira)
            
    # Espera até que todos os VIVOS tenham mandado o aviso de fim de rodada
    vivos = [pid for pid, d in jogador.tabela_peers.items() if d["status"] == "VIVO"]
    while not set(vivos).issubset(rede.rodada_finalizada_peers):
        time.sleep(0.5)
        
    rede.rodada_finalizada_peers.clear()
    print("✅ Todos prontos! Avançando para a próxima rodada...")



def main():
    print("--- ZOMBIE HUNT P2P ---")

    ja_existe_anfitriao = verificar_se_existe_anfitriao()
    
    if not ja_existe_anfitriao:
        # ==============================================================
        # CASO 1: Ninguém na rede -> ESSA INSTÂNCIA DE JOGADOR VIRA O ANFITRIÃO
        # ==============================================================
        print("> Nenhum lobby encontrado. Você é o PRIMEIRO jogador e assumiu como ANFITRIÃO!")
        jogador = Jogador(IP_LOCAL, PORTA_PADRAO_LOBBY, eh_anfitriao=True)
        rede = GerenciadorDeRede(jogador)
        
        while True:
            cmd = input("\n> [Anfitrião] Digite 'start' quando estiverem todos prontos para iniciar a partida: ").strip().lower()
            if cmd == "start":  
                # Adiciona o próprio anfitrião na tabela
                jogador.tabela_peers[0] = {
                    "ip": IP_LOCAL, 
                    "porta": PORTA_PADRAO_LOBBY, 
                    "status": "VIVO",
                }

                print("\n> Disparando tabela full mesh para todos os nós...")
                for pid, dados in jogador.tabela_peers.items():
                    if pid == 0: continue
                    msg = {
                        "tipo": "INICIAR_PARTIDA",
                        "seu_id": pid,
                        "tabela": jogador.tabela_peers
                        }
                    rede.enviar_json(dados["ip"], dados["porta"], msg)
                break
                                
    # ==============================================
    # CASO 2: Lobby encontrado -> VIRO UM CONVIDADO
    # ==============================================
    else:
        print("> Lobby encontrado! Conectando-se como CONVIDADO...")

        # Escolhendo uma porta livre aleatória para o convidado não dar conflito (ex: 51234)
        meu_socket_temporario = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        meu_socket_temporario.bind((IP_LOCAL, 0))
        sua_porta = meu_socket_temporario.getsockname()[1]
        meu_socket_temporario.close()

        # print(f"> Porta atribuída ao seu nó: {sua_porta}")
        jogador = Jogador(IP_LOCAL, sua_porta, eh_anfitriao=False)
        rede = GerenciadorDeRede(jogador)

        # print(f"> Enviando seu registro e hash ({jogador.hash_do_papel[:8]}...) para o Anfitrião...")
        # Enviando meu endereço e papel para o anfitrião
        msg = {
            "tipo": "ENTRAR_LOBBY",
            "ip": IP_LOCAL,
            "porta": sua_porta,
            "hash_papel": jogador.hash_do_papel
        }
        rede.enviar_json(IP_LOCAL, PORTA_PADRAO_LOBBY, msg)

        print("> Aguardando o anfitrião iniciar a partida...")
        while jogador.id is None:
            time.sleep(1)




    # === LOOP PRINCIPAL DE 10 RODADAS ===
    for rodada in range(1, 11):
        executar_rodada(jogador, rede, rodada)
        
        # Confere se algum time já venceu
        fim, msg_fim = MotorDoJogo.verificar_fim_de_jogo(
            jogador.tabela_peers, jogador.id, jogador.status, jogador.papel_secreto, rodada
        )
        print(f"\n📊 Placar da Rodada -> {msg_fim}")
        if fim:
            print("\n" + "*"*50)
            print("🚨 FIM DE JOGO! 🚨")
            print("*"*50)
            break
            
    print("\n🏁 Partida encerrada! Obrigado por jogar.")
    sys.exit()


if __name__ == "__main__":
    main()