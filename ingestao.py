"""Script principal para ingestão de dados MIMIC FHIR em PostgreSQL."""

import logging
import os
import sys

from leitor import ler_registros
from banco import conectar, criar_tabela, inserir_organizacoes


def configurar_logging(nivel='INFO'):
    """
    Configura o sistema de logging com formato padrão.

    Args:
        nivel (str): Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                     Padrão: INFO.
    """
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        format=format_str,
        level=nivel.upper(),
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def obter_configuracao_banco():
    """
    Obtém configuração do banco de dados a partir de variáveis de ambiente.

    Variáveis esperadas:
    - POSTGRES_HOST: endereço do servidor (padrão: localhost)
    - POSTGRES_PORT: porta (padrão: 5432)
    - POSTGRES_DB: nome do banco (padrão: mimic_fhir)
    - POSTGRES_USER: usuário (padrão: postgres)
    - POSTGRES_PASSWORD: senha (padrão: postgres)

    Returns:
        dict: Configuração do banco com as chaves esperadas por banco.conectar().
    """
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'mimic_fhir'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }


def main():
    """
    Orquestra o fluxo principal de ingestão:
    1. Configura logging
    2. Lê variáveis de ambiente
    3. Conecta ao banco
    4. Cria tabela (se necessário)
    5. Lê arquivo NDJSON.gz
    6. Insere registros no banco
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    configurar_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info("Iniciando ingestão de dados MIMIC FHIR")

    caminho_arquivo = os.getenv(
        'CAMINHO_ARQUIVO',
        './data/MimicOrganization.ndjson.gz'
    )

    try:
        # Lê registros do arquivo
        logger.info(f"Lendo arquivo: {caminho_arquivo}")
        registros = ler_registros(caminho_arquivo)

        if not registros:
            logger.warning("Nenhum registro válido encontrado no arquivo")
            logger.info("Ingestão concluída sem registros")
            return

        # Conecta ao banco
        config_banco = obter_configuracao_banco()
        conexao = conectar(config_banco)

        try:
            # Cria tabela
            criar_tabela(conexao)

            # Insere registros
            total_inserido = inserir_organizacoes(conexao, registros)

            logger.info(
                f"Ingestão concluída com sucesso: "
                f"{total_inserido} registros processados"
            )

        finally:
            conexao.close()
            logger.info("Conexão com banco fechada")

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Erro durante ingestão: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
