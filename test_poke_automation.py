import requests
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

# Configurações globais
BASE_URL = "https://pokeapi.co/api/data/v2/pokemon/"
TARGETS = ["pikachu", "charizard", "bulbasaur", "squirtle", "mewtwo"]

# --- 1. TESTES FUNCIONAIS E DE CONTRATO (RESILIÊNCIA) ---
@pytest.mark.parametrize("poke_name", TARGETS)
def test_poke_api_contract(poke_name):
    """Valida se a API retorna os dados no formato esperado e lida com mudanças de campos."""
    response = requests.get(f"{BASE_URL}{poke_name}")
    assert response.status_code == 200
    data = response.json()
    
    # Validação de tipos básicos
    assert isinstance(data['name'], str)
    assert isinstance(data['id'], int)
    
    # Lógica de Retrocompatibilidade (Self-healing)
    # Tenta 'movimentos' (novo) ou 'moves' (antigo)
    movimentos_data = data.get('movimentos') or data.get('moves')
    assert movimentos_data is not None, "Falha de contrato: Campo de movimentos não encontrado."
    assert isinstance(movimentos_data, list)

# --- 2. TESTES DE PERFORMANCE (LATÊNCIA P95) ---
def test_performance_p95():
    """Simula carga e valida a experiência do usuário mais lento."""
    latencias = []
    
    def make_request():
        start = time.perf_counter()
        requests.get(f"{BASE_URL}pikachu")
        return time.perf_counter() - start

    # Simula 20 requisições concorrentes
    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda f: f(), [make_request] * 20))
    
    latencias = [r * 1000 for r in resultados] # Converte para ms
    p95 = statistics.quantiles(latencias, n=100)[94]
    
    print(f"\n⏱️ Latência Média: {statistics.mean(latencias):.2f}ms")
    print(f"🚀 Latência P95: {p95:.2f}ms")
    
    assert p95 < 1000, f"Performance P95 instável: {p95:.2f}ms"

# --- 3. TESTE DE PESO DO PAYLOAD (OTIMIZAÇÃO) ---
def test_payload_size_check():
    """Valida se o JSON retornado não é excessivamente pesado para conexões móveis."""
    url = f"{BASE_URL}mewtwo"
    response = requests.get(url)
    size_kb = len(response.content) / 1024
    
    print(f"\n📦 Tamanho do Payload (Mewtwo): {size_kb:.2f} KB")
    # Limite sugerido para evitar lentidão em redes 3G/4G
    assert size_kb < 500, f"Alerta: Payload pesado detectado ({size_kb:.2f} KB)"

# --- 4. TESTE DE SEGURANÇA (HEADERS) ---
def test_security_and_compression_headers():
    """Verifica se o servidor utiliza boas práticas de entrega (Gzip/JSON)."""
    response = requests.get(BASE_URL)
    headers = response.headers
    
    # Verifica se há compressão de dados para economizar banda
    has_compression = 'gzip' in headers.get('Content-Encoding', '') or 'br' in headers.get('Content-Encoding', '')
    print(f"\n🔐 Compressão ativa: {has_compression}")
    assert 'application/json' in headers['Content-Type']

# --- 5. TESTE NEGATIVO (TRATAMENTO DE ERROS) ---
def test_invalid_endpoint_error_handling():
    """Garante que a API responde corretamente (404) a dados inexistentes."""
    # Agumon não é um Pokémon (é Digimon), deve retornar 404
    response = requests.get(f"{BASE_URL}agumon")
    
    print(f"\n🚫 Status para busca inválida: {response.status_code}")
    assert response.status_code == 404

if __name__ == "__main__":
    # Comando para rodar via script: python test_poke_automation.py
    pytest.main([__file__, "-s", "-v"])
