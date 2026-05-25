"""Script principal para ingestão de dados MIMIC FHIR em PostgreSQL."""

import logging
import os
import sys

from leitor import ler_registros, ler_localizacoes, ler_pacientes, ler_encontros, ler_condicoes
from banco import (
    conectar,
    criar_tabela,
    inserir_organizacoes,
    criar_tabela_localizacoes,
    inserir_localizacoes,
    criar_tabela_pacientes,
    inserir_pacientes,
    criar_tabela_encontros,
    inserir_encontros,
    criar_tabela_encontros_localizacoes,
    inserir_encontros_localizacoes,
    criar_tabela_condicoes,
    inserir_condicoes
)


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
    - POSTGRES_PASSWORD: senha (obrigatória)

    Returns:
        dict: Configuração do banco com as chaves esperadas por banco.conectar().
    """
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'mimic_fhir'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }


def main():
    """
    Orquestra o fluxo principal de ingestão:
    1. Configura logging
    2. Lê variáveis de ambiente
    3. Conecta ao banco
    4. Cria tabelas (organizacoes, localizacoes, pacientes, encontros, encontros_localizacoes, condicoes)
    5. Lê e insere registros de organizações
    6. Lê e insere registros de localizações
    7. Lê e insere registros de pacientes
    8. Lê e insere registros de encontros e seus relacionamentos com localizações
    9. Lê e insere registros de condições
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    configurar_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info("Iniciando ingestão de dados MIMIC FHIR")

    caminho_arquivo_org = os.getenv(
        'CAMINHO_ARQUIVO',
        './data/MimicOrganization.ndjson.gz'
    )
    caminho_arquivo_loc = os.getenv(
        'CAMINHO_ARQUIVO_LOCATION',
        './data/MimicLocation.ndjson.gz'
    )
    caminho_arquivo_pac = os.getenv(
        'CAMINHO_ARQUIVO_PATIENT',
        './data/MimicPatient.ndjson.gz'
    )
    caminho_arquivo_enc = os.getenv(
        'CAMINHO_ARQUIVO_ENCOUNTER',
        './data/MimicEncounter.ndjson.gz'
    )
    caminho_arquivo_cond = os.getenv(
        'CAMINHO_ARQUIVO_CONDITION',
        './data/MimicCondition.ndjson.gz'
    )

    config_banco = obter_configuracao_banco()
    conexao = None

    try:
        # Conecta ao banco
        conexao = conectar(config_banco)

        # Cria tabelas em ordem de dependência
        criar_tabela(conexao)
        criar_tabela_localizacoes(conexao)
        criar_tabela_pacientes(conexao)
        criar_tabela_encontros(conexao)
        criar_tabela_encontros_localizacoes(conexao)
        criar_tabela_condicoes(conexao)

        # Ingestão de Organizações
        logger.info(f"Lendo arquivo de organizações: {caminho_arquivo_org}")
        registros_org = ler_registros(caminho_arquivo_org)

        if registros_org:
            total_org = inserir_organizacoes(conexao, registros_org)
            logger.info(
                f"Organizações ingeridas com sucesso: "
                f"{total_org} registros processados"
            )
        else:
            logger.warning("Nenhum registro de organização válido encontrado")

        # Ingestão de Localizações
        logger.info(f"Lendo arquivo de localizações: {caminho_arquivo_loc}")
        registros_loc = ler_localizacoes(caminho_arquivo_loc)

        if registros_loc:
            total_loc = inserir_localizacoes(conexao, registros_loc)
            logger.info(
                f"Localizações ingeridas com sucesso: "
                f"{total_loc} registros processados"
            )
        else:
            logger.warning("Nenhum registro de localização válido encontrado")

        # Ingestão de Pacientes
        logger.info(f"Lendo arquivo de pacientes: {caminho_arquivo_pac}")
        registros_pac = ler_pacientes(caminho_arquivo_pac)

        if registros_pac:
            total_pac = inserir_pacientes(conexao, registros_pac)
            logger.info(
                f"Pacientes ingeridos com sucesso: "
                f"{total_pac} registros processados"
            )
        else:
            logger.warning("Nenhum registro de paciente válido encontrado")

        # Ingestão de Encontros
        logger.info(f"Lendo arquivo de encontros: {caminho_arquivo_enc}")
        registros_enc = ler_encontros(caminho_arquivo_enc)

        if registros_enc:
            total_enc = inserir_encontros(conexao, registros_enc)
            logger.info(
                f"Encontros ingeridos com sucesso: "
                f"{total_enc} registros processados"
            )

            total_enc_loc = inserir_encontros_localizacoes(conexao, registros_enc)
            logger.info(
                f"Relacionamentos encontro-localização ingeridos com sucesso: "
                f"{total_enc_loc} registros processados"
            )
        else:
            logger.warning("Nenhum registro de encontro válido encontrado")

        # Ingestão de Condições
        logger.info(f"Lendo arquivo de condições: {caminho_arquivo_cond}")
        registros_cond = ler_condicoes(caminho_arquivo_cond)

        if registros_cond:
            total_cond = inserir_condicoes(conexao, registros_cond)
            logger.info(
                f"Condições ingeridas com sucesso: "
                f"{total_cond} registros processados"
            )
        else:
            logger.warning("Nenhum registro de condição válido encontrado")

        logger.info("Ingestão de dados MIMIC FHIR concluída com sucesso")

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Erro durante ingestão: {e}")
        sys.exit(1)

    finally:
        if conexao:
            conexao.close()
            logger.info("Conexão com banco fechada")


if __name__ == '__main__':
    main()
