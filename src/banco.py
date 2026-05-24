"""Módulo para operações com banco de dados PostgreSQL."""

import logging
import psycopg2

logger = logging.getLogger(__name__)


def conectar(configuracao):
    """
    Cria e retorna uma conexão com PostgreSQL.

    Args:
        configuracao (dict): Dicionário com chaves:
            - host: endereço do servidor PostgreSQL
            - port: porta do servidor
            - database: nome do banco de dados
            - user: usuário de acesso
            - password: senha de acesso

    Returns:
        psycopg2.connection: Conexão com o banco de dados.

    Raises:
        psycopg2.Error: Se a conexão falhar.
    """
    try:
        conexao = psycopg2.connect(
            host=configuracao['host'],
            port=configuracao['port'],
            database=configuracao['database'],
            user=configuracao['user'],
            password=configuracao['password']
        )
        logger.info(f"Conexão estabelecida com {configuracao['host']}")
        return conexao

    except psycopg2.Error as e:
        logger.error(f"Falha ao conectar com banco de dados: {e}")
        raise


def criar_tabela(conexao):
    """
    Cria tabela 'organizacoes' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - nome: TEXT, obrigatório

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS organizacoes (
        id VARCHAR(255) PRIMARY KEY,
        nome TEXT NOT NULL
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'organizacoes' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_organizacoes(conexao, registros):
    """
    Insere registros de organizações na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com 'id' e 'nome'.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO organizacoes (id, nome)
    VALUES (%s, %s)
    ON CONFLICT (id) DO NOTHING
    """

    contador = 0

    try:
        cursor = conexao.cursor()

        for registro in registros:
            try:
                cursor.execute(sql, (registro['id'], registro['nome']))
                contador += 1
                logger.info(
                    f"Registro inserido: id={registro['id']}, "
                    f"nome={registro['nome']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir registro {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de registros processados: {contador}")

    finally:
        cursor.close()

    return contador


def criar_tabela_localizacoes(conexao):
    """
    Cria tabela 'localizacoes' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - nome: TEXT, obrigatório
    - organizacao_id: VARCHAR(255), chave estrangeira referenciando organizacoes

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS localizacoes (
        id VARCHAR(255) PRIMARY KEY,
        nome TEXT NOT NULL,
        organizacao_id VARCHAR(255) REFERENCES organizacoes(id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'localizacoes' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_localizacoes(conexao, registros):
    """
    Insere registros de localizações na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com 'id', 'nome', 'organizacao_id'.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO localizacoes (id, nome, organizacao_id)
    VALUES (%s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """

    contador = 0

    try:
        cursor = conexao.cursor()

        for registro in registros:
            try:
                cursor.execute(
                    sql,
                    (
                        registro['id'],
                        registro['nome'],
                        registro['organizacao_id']
                    )
                )
                contador += 1
                logger.info(
                    f"Localização inserida: id={registro['id']}, "
                    f"nome={registro['nome']}, "
                    f"organizacao_id={registro['organizacao_id']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir localização {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de localizações processadas: {contador}")

    finally:
        cursor.close()

    return contador
