import socket
import threading
import sys
import json
import time

# Pega os dados do terminal ao rodar o programa
if len(sys.argv) < 3:
    print("Uso: python p2p.py <Meu_ID> <Meu_Nome> [ID_Vizinho1] [ID_Vizinho2] ...")
    sys.exit()

meu_id = int(sys.argv[1])
meu_nome = sys.argv[2]
# A nossa "Tabela de Roteamento" (uma lista simples de quem conhecemos)
vizinhos = [int(x) for x in sys.argv[3:]] 

# Usamos a porta 5000 + o ID para simular o IP de cada um na mesma máquina
minha_porta = 5000 + meu_id

def repassar_para(id_alvo, mensagem):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria o Socket UDP para enviar a mensagem
    porta_alvo = 5000 + id_alvo
    cliente.sendto(json.dumps(mensagem).encode('utf-8'), ('127.0.0.1', porta_alvo)) # Codifica a mensagem de dicionário para JSON e envia para o nó alvo

def escutar_mensagem():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Cria o Socket UDP para receber mensagens
    servidor.bind(('127.0.0.1', minha_porta)) 
    
    while True: # O nó nunca para de ouvir
        dados, _ = servidor.recvfrom(1024) # Recebe até 1024 bytes de dados
        mensagem = json.loads(dados.decode('utf-8')) # Decodifica a mensagem recebida de JSON para dicionário
        
        # Se a mensagem é para mim, eu leio!
        if mensagem['destino'] == meu_id:
            print(f"\n[URGENTE] {mensagem['origem']} mandou uma mensagem pra você: '{mensagem['texto']}'\n> ", end="")
        
        # Se não é para mim, eu olho minha tabela e repasso (O Roteamento!)
        else:
            print(f"\n[SUSSURRO] Ouvi uma mensagem para o Nó {mensagem['destino']}. ", end="")
            if mensagem['destino'] in vizinhos:
                print("Ele é meu vizinho! Entregando...\n> ", end="")
                repassar_para(mensagem['destino'], mensagem)
            elif vizinhos:
                print(f"Repassando cegamente para meu contato Nó {vizinhos[0]}...\n> ", end="")
                repassar_para(vizinhos[0], mensagem)

# Criando a thread de escuta que fica em segundo plano, como um "ouvido" que fica sempre atento às mensagens que chegam
threading.Thread(target=escutar_mensagem, daemon=True).start()
time.sleep(0.5) # Pausa rápida só para o terminal ficar bonito

print(f"\n--- {meu_nome} (Nó {meu_id}) acordou na Cidade! ---")
print(f"Sua tabela de contatos tem os Nós: {vizinhos}")

# Loop principal para você digitar as mensagens
while True:
    try:
        alvo = int(input("\nPara qual Nó (ID) você quer enviar uma mensagem? "))
        texto = input("Qual é a mensagem? ")
        
        mensagem = {'origem': meu_nome, 'destino': alvo, 'texto': texto}
        
        # Lógica de Roteamento P2P super simples
        if alvo in vizinhos:
            print(f"Você conhece o Nó {alvo}. Sussurrando direto...")
            repassar_para(alvo, mensagem)
        elif vizinhos:
            print(f"Você não conhece o Nó {alvo}. Pedindo para o Nó {vizinhos[0]} repassar...")
            repassar_para(vizinhos[0], mensagem)
        else:
            print("Você está isolado e não tem vizinhos na tabela!")
            
    except KeyboardInterrupt:
        print("\nSaindo do jogo...")
        break
    except ValueError:
        print("Digite apenas números para o ID do Nó!")