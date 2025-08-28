import requests
import pandas as pd
import os

# Constantes globais
URL_IPCA = "https://sidra.ibge.gov.br/Ajax/Json/Tabela/1/1737?versao=-1"
PASTA_SAIDA = "saida_dados"


def capturar_dados(url: str) -> dict:
    """
    Captura os dados da API do SIDRA/IBGE.
    """
    print(f"Iniciando a captura de dados da URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Dados capturados com sucesso!\n")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar acessar a URL: {e}")
        return {}


def extrair_e_processar_lista(dados_json: dict, caminho_chaves: list) -> pd.DataFrame:
    """
    Navega no dicionário JSON usando as chaves pré definidas,
    extrai uma lista e a converte para um DataFrame do Pandas.
    """

    dados_atuais = dados_json
    for chave in caminho_chaves:
        dados_atuais = dados_atuais.get(chave)
        if dados_atuais is None:

            return pd.DataFrame()
    
    lista_de_dados = dados_atuais

    if not isinstance(lista_de_dados, list) or not lista_de_dados:
        return pd.DataFrame()

    if all(isinstance(item, str) for item in lista_de_dados):
        nome_coluna = caminho_chaves[-1].replace('s', '').capitalize() # Ex: 'Notas' -> 'Nota'
        return pd.DataFrame(lista_de_dados, columns=[nome_coluna])
    
    # Para listas de dicionários, a conversão é direta
    return pd.DataFrame(lista_de_dados)


def gravar_arquivo_parquet(df: pd.DataFrame, nome_arquivo: str, pasta: str):
    """
    Grava o DataFrame em um arquivo Parquet dentro de uma pasta chamada saida_dados.
    """
    if df.empty:
        print(f"DataFrame para '{nome_arquivo}' está vazio. Arquivo não será gerado.")
        return

    caminho_completo = os.path.join(pasta, nome_arquivo)

    try:
        df.to_parquet(caminho_completo, engine='pyarrow', index=False)
        print(f"Arquivo '{caminho_completo}' salvo com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro ao tentar salvar o arquivo '{caminho_completo}': {e}")


def main():
    """
    Função principal que orquestra todo o processo.
    Criando a pasta de saída, se não existir.
    Capturando os dados da API do SIDRA/IBGE.
    Realizando o mapeamento de listas presentes na API.
    Extraindo e gravando essas listas em parquet.
    """
    print("--- INÍCIO DO PROCESSO DO BOT ---")
    
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    dados_json = capturar_dados(URL_IPCA)

    if not dados_json:
        print("--- FIM DO PROCESSO (sem dados para processar) ---")
        return

    print("--- INICIANDO GERAÇÃO DOS ARQUIVOS PARQUET ---\n")


    tabelas_para_extrair = {
        'variaveis.parquet': ['Variaveis'],
        'unidades_de_medida.parquet': ['UnidadesDeMedida'],
        'periodos.parquet': ['Periodos', 'Periodos'],
        'conjuntos_periodos.parquet': ['Periodos', 'Conjuntos'],
        'notas.parquet': ['Notas']
    }

    for nome_arquivo, caminho in tabelas_para_extrair.items():
        df_processado = extrair_e_processar_lista(dados_json, caminho)
        gravar_arquivo_parquet(df_processado, nome_arquivo, PASTA_SAIDA)
        print("-" * 30)

    print("\n--- FIM DO PROCESSO DO BOT ---")


if __name__ == "__main__":
    main()