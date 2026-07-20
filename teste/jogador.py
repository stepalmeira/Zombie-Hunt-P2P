import random
import hashlib
import string

class Jogador:
    def __init__(self, ip, porta, eh_anfitriao=False):
        self.id = 0 if eh_anfitriao else None
        self.ip = ip
        self.porta = int(porta)
        self.eh_anfitriao = eh_anfitriao
        self.status = "VIVO"
        
        # O deck inicial de 1 a 10
        self.deck = list(range(1, 11))
        
        # Sorteia o papel inicial
        papeis_possiveis = ["Zumbi", "Caçador", "Médico", "Civil"]
        self.papel_secreto = random.choice(papeis_possiveis)
        
        # Gera a "senha" do papel e o hash para divulgar no início (Protocolo de Segredo)
        self.senha_do_papel = self._gerar_texto_aleatorio(8)
        self.hash_do_papel = self.gerar_hash(f"{self.papel_secreto}_{self.senha_do_papel}")
        
        # Tabela Full Mesh: guarda os dados e status dos outros peers da rede
        self.tabela_peers = {}

    # Escolhe uma carta aleatória do deck e remove ela (vai ser adaptado pra pedir input do usuário depois).
    def escolher_carta(self):
        if not self.deck:
            return None
        carta = random.choice(self.deck)
        self.deck.remove(carta)
        return carta

    # Gera uma palavra aleatória (usada para senhas e salts)
    @staticmethod
    def _gerar_texto_aleatorio(tamanho=6):
        letras = string.ascii_letters + string.digits
        return ''.join(random.choice(letras) for _ in range(tamanho))

    # Função hash SHA-256
    @staticmethod 
    def gerar_hash(texto):
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def gerar_commit_jogada(self, carta):
        """Gera o salt temporário da rodada e cria o hash da jogada."""
        salt_temporario = self._gerar_texto_aleatorio(6)
        texto_lacrado = f"{carta}_{salt_temporario}"
        hash_jogada = self.gerar_hash(texto_lacrado)
        return hash_jogada, salt_temporario