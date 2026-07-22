import random

class MotorDoJogo:
    @staticmethod
    def resolver_combate(papel_a, papel_b, carta_a, carta_b):
        if carta_a == carta_b:
            return "EMPATOU", "NADA"
        
        vencedor = "A" if carta_a > carta_b else "B"
        if papel_a == papel_b:
            return ("VENCEU" if vencedor == "A" else "PERDEU"), "NADA"
            
        p_vencedor = papel_a if vencedor == "A" else papel_b
        p_perdedor = papel_b if vencedor == "A" else papel_a
        
        consequencia = "NADA"
        if p_vencedor == "Zumbi" and p_perdedor in ["Caçador", "Médico", "Civil"]:
            consequencia = "VIRAR_ZUMBI"
        elif p_vencedor == "Caçador" and p_perdedor == "Zumbi":
            consequencia = "MORRER"
        elif p_vencedor == "Médico" and p_perdedor == "Zumbi":
            consequencia = "VIRAR_CIVIL"
            
        return ("VENCEU" if vencedor == "A" else "PERDEU"), consequencia

    @staticmethod
    def verificar_fim_de_jogo(tabela_peers, meu_id, meu_status, meu_papel, rodada):
        if rodada >= 10:
            return True, "[FIM] Limite de 10 rodadas atingido."
            
        zumbis = humanos = 0
        if meu_status == "VIVO":
            if meu_papel == "Zumbi": zumbis += 1
            else: humanos += 1
            
        for p in tabela_peers.values():
            if p["status"] == "VIVO":
                papel = p.get("papel_conhecido", "Civil")
                if papel == "Zumbi": zumbis += 1
                else: humanos += 1
                
        if zumbis == 0: return True, "[VITORIA] HUMANOS VENCERAM!"
        if humanos == 0: return True, "[VITORIA] ZUMBIS VENCERAM!"
        return False, f"Sobreviventes: Humanos ({humanos}) | Zumbis ({zumbis})"

    @staticmethod
    def formar_duplas(tabela_peers):
        vivos = [pid for pid, dados in tabela_peers.items() if dados["status"] == "VIVO"]
        if len(vivos) < 2:
            return [], vivos[0] if vivos else None
            
        random.shuffle(vivos)
        duplas = [(vivos[i], vivos[i+1]) for i in range(0, len(vivos) - 1, 2)]
        folga = vivos[-1] if len(vivos) % 2 != 0 else None
        return duplas, folga