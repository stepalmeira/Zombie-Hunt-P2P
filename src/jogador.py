import random
import hashlib
import string

class Jogador:
    def __init__(self, ip, porta, eh_anfitriao=False):
        self.id = 0 if eh_anfitriao else None  # Nomeação --> Cada nó possui um ID numérico plano (0, 1, 2...) associado a seus atributos de rede
        self.ip = ip
        self.porta = int(porta)
        self.status = "VIVO"
        
        # [Conceito: Coordenação Centralizada] O nó 0 começa como Coordenador
        self.id_lider = 0 
        
        self.deck = list(range(1, 11))
        
        # Servidor Stateful: Mantém em memória o estado local do nó 
        # (deck, papel_secreto, status e a réplica da tabela_peers)
        self.papel_secreto = None
        self.senha_do_papel = self._gerar_texto_aleatorio(8)
        self.hash_do_papel = None
        
        # Replicação e Consistência --> A tabela_peers é totalmente replicada em todos os nós da rede
        self.tabela_peers = {}  # Nomeação --> Funciona como a tabela de resolução local mapeando ID -> Atributos

    def definir_papel(self, papel):
        """Método chamado para atribuir o papel vindo do Líder."""
        self.papel_secreto = papel
        self.hash_do_papel = self.gerar_hash(f"{self.papel_secreto}_{self.senha_do_papel}")

    def escolher_carta(self):
        if not self.deck: return None
        carta = random.choice(self.deck)
        self.deck.remove(carta)
        return carta

    @staticmethod
    def _gerar_texto_aleatorio(tamanho=6):
        letras = string.ascii_letters + string.digits
        return ''.join(random.choice(letras) for _ in range(tamanho))

    # Coordenação --> Gera o hash SHA-256 e o salt para realizar a jogada
    @staticmethod 
    def gerar_hash(texto):
        # [Conceito: Funções Hash] Garante resistência à colisão e caminho único
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def gerar_commit_jogada(self, carta):
        salt = self._gerar_texto_aleatorio(6)
        texto_lacrado = f"{carta}_{salt}"
        return self.gerar_hash(texto_lacrado), salt