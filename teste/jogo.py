
class MotorDoJogo:

    # Recebe os dados de um duelo e retorna o resultado para o jogador A
    # Retornos possíveis: 'VENCEU', 'PERDEU', 'EMPATE' e a 'CONSEQUENCIA' (morte/transformação)
    @staticmethod
    def resolver_combate(papel_a, papel_b, carta_a, carta_b):
        if carta_a == carta_b:
            return "EMPATE", "NADA"
        
        vencedor = "A" if carta_a > carta_b else "B"
        
        # Se os papéis forem iguais, ninguém morre ou transforma
        if papel_a == papel_b:
            return ("VENCEU" if vencedor == "A" else "PERDEU"), "NADA"
            
        # Vamos avaliar as regras da tabela
        p_vencedor = papel_a if vencedor == "A" else papel_b
        p_perdedor = papel_b if vencedor == "A" else papel_a
        
        consequencia = "NADA"
        if p_vencedor == "Zumbi" and p_perdedor in ["Caçador", "Médico", "Civil"]:
            consequencia = "VIRAR_ZUMBI"
        elif p_vencedor == "Caçador" and p_perdedor == "Zumbi":
            consequencia = "MORRER"
        elif p_vencedor == "Médico" and p_perdedor == "Zumbi":
            consequencia = "VIRAR_CIVIL" # Usando nossa regra do Ponto 2!
        elif p_vencedor == "Caçador" and p_perdedor in ["Médico", "Civil"]:
            consequencia = "MORRER"
            
        return ("VENCEU" if vencedor == "A" else "PERDEU"), consequencia

    # Verifica se o jogo deve acabar (fim das 10 rodadas ou um time foi dizimado)
    @staticmethod
    def verificar_fim_de_jogo(tabela_peers, meu_id, meu_status, meu_papel, rodada_atual):
        """Verifica se o jogo deve acabar (fim das 10 rodadas ou um time foi dizimado)"""

        if rodada_atual >= 10:
            return True, "Fim das 10 rodadas!"
            
        zumbis = 0
        humanos = 0
        
        # Contabiliza a própria vida -> (Ste: Como isso é possível num método estático??)
        if meu_status == "VIVO":
            if meu_papel == "Zumbi": zumbis += 1
            else: humanos += 1
            
        # Contabiliza o restante da rede
        for p in tabela_peers.values():
            if p["status"] == "VIVO":
                # Aqui usamos o papel que a rede já revelou ou conhece
                papel = p.get("papel_conhecido", "Civil") # Simplificação para o exemplo
                if papel == "Zumbi": zumbis += 1
                else: humanos += 1
                
        if zumbis == 0:
            return True, "🏆 HUMANOS VENCERAM! Todos os zumbis foram erradicados."
        if humanos == 0:
            return True, "🧟 ZUMBIS VENCERAM!"
            
        return False, f"Sobreviventes -> Humanos: {humanos} | Zumbis: {zumbis}"
    

    @staticmethod
    def formar_duplas(tabela_peers, rodada):
        """
        Forma as duplas da rodada de forma idêntica em todos os computadores.
        Retorna uma lista de duplas (ex: [(0, 1), (2, 3)]) e o ID de quem ficou de folga (se houver ímpar).
        """

        # 1. Pega apenas os IDs dos jogadores VIVOS em ordem crescente
        vivos = sorted([pid for pid, dados in tabela_peers.items() if dados["status"] == "VIVO"])
        
        if len(vivos) < 2:
            return [], vivos[0] if vivos else None
            
        # 2. Rotaciona a lista baseando-se no número da rodada para variar os confrontos
        deslocamento = (rodada - 1) % len(vivos)
        vivos_rotacionados = vivos[deslocamento:] + vivos[:deslocamento]
        
        duplas = []
        # 3. Agrupa de dois em dois
        for i in range(0, len(vivos_rotacionados) - 1, 2):
            duplas.append((vivos_rotacionados[i], vivos_rotacionados[i+1]))
            
        # Se sobrou alguém (número ímpar de vivos), o último ganha "folga" na rodada
        jogador_folga = vivos_rotacionados[-1] if len(vivos_rotacionados) % 2 != 0 else None
        
        return duplas, jogador_folga