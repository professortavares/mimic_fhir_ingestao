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


def criar_tabela_pacientes(conexao):
    """
    Cria tabela 'pacientes' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - nome_familia: TEXT, obrigatório
    - genero: VARCHAR(50)
    - data_nascimento: DATE
    - raca: TEXT
    - identificador: VARCHAR(255)
    - idioma: VARCHAR(10)
    - estado_civil: VARCHAR(50)
    - organizacao_id: VARCHAR(255), chave estrangeira referenciando organizacoes

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS pacientes (
        id VARCHAR(255) PRIMARY KEY,
        nome_familia TEXT NOT NULL,
        genero VARCHAR(50),
        data_nascimento DATE,
        raca TEXT,
        identificador VARCHAR(255),
        idioma VARCHAR(10),
        estado_civil VARCHAR(50),
        organizacao_id VARCHAR(255) REFERENCES organizacoes(id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'pacientes' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_pacientes(conexao, registros):
    """
    Insere registros de pacientes na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com campos de paciente.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO pacientes (id, nome_familia, genero, data_nascimento, raca,
                          identificador, idioma, estado_civil, organizacao_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        registro['nome_familia'],
                        registro['genero'],
                        registro['data_nascimento'],
                        registro['raca'],
                        registro['identificador'],
                        registro['idioma'],
                        registro['estado_civil'],
                        registro['organizacao_id']
                    )
                )
                contador += 1
                logger.info(
                    f"Paciente inserido: id={registro['id']}, "
                    f"nome_familia={registro['nome_familia']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir paciente {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de pacientes processados: {contador}")

    finally:
        cursor.close()

    return contador


def criar_tabela_encontros(conexao):
    """
    Cria tabela 'encontros' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - tipo: TEXT
    - classe: VARCHAR(50)
    - periodo_inicio: TIMESTAMP
    - periodo_fim: TIMESTAMP
    - status: VARCHAR(50)
    - hospitalizacao_code: VARCHAR(50)
    - alta_code: VARCHAR(50)
    - paciente_id: VARCHAR(255), chave estrangeira referenciando pacientes

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS encontros (
        id VARCHAR(255) PRIMARY KEY,
        tipo TEXT,
        classe VARCHAR(50),
        periodo_inicio TIMESTAMP,
        periodo_fim TIMESTAMP,
        status VARCHAR(50),
        hospitalizacao_code VARCHAR(50),
        alta_code VARCHAR(50),
        paciente_id VARCHAR(255) REFERENCES pacientes(id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'encontros' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_encontros(conexao, registros):
    """
    Insere registros de encontros na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com campos de encontro.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO encontros (id, tipo, classe, periodo_inicio, periodo_fim,
                          status, hospitalizacao_code, alta_code, paciente_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        registro['tipo'],
                        registro['classe'],
                        registro['periodo_inicio'],
                        registro['periodo_fim'],
                        registro['status'],
                        registro['hospitalizacao_code'],
                        registro['alta_code'],
                        registro['paciente_id']
                    )
                )
                contador += 1
                logger.info(
                    f"Encontro inserido: id={registro['id']}, "
                    f"paciente_id={registro['paciente_id']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir encontro {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de encontros processados: {contador}")

    finally:
        cursor.close()

    return contador


def criar_tabela_encontros_localizacoes(conexao):
    """
    Cria tabela 'encontros_localizacoes' se não existir.

    A tabela possui colunas:
    - encontro_id: VARCHAR(255), chave estrangeira referenciando encontros
    - localizacao_id: VARCHAR(255), chave estrangeira referenciando localizacoes
    - periodo_inicio: TIMESTAMP
    - periodo_fim: TIMESTAMP
    - Chave primária composta: (encontro_id, localizacao_id)

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS encontros_localizacoes (
        encontro_id VARCHAR(255) REFERENCES encontros(id),
        localizacao_id VARCHAR(255) REFERENCES localizacoes(id),
        periodo_inicio TIMESTAMP,
        periodo_fim TIMESTAMP,
        PRIMARY KEY (encontro_id, localizacao_id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'encontros_localizacoes' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_encontros_localizacoes(conexao, encontros_com_localizacoes):
    """
    Insere registros de relacionamento entre encontros e localizações.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um relacionamento com mesmos 'encontro_id' e 'localizacao_id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        encontros_com_localizacoes (list): Lista de dicionários com 'id' (encontro)
                                           e 'localizacoes' (lista de localizações).

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO encontros_localizacoes (encontro_id, localizacao_id, periodo_inicio, periodo_fim)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (encontro_id, localizacao_id) DO NOTHING
    """

    contador = 0

    try:
        cursor = conexao.cursor()

        for encontro in encontros_com_localizacoes:
            for localizacao in encontro.get('localizacoes', []):
                try:
                    cursor.execute(
                        sql,
                        (
                            encontro['id'],
                            localizacao['localizacao_id'],
                            localizacao['periodo_inicio'],
                            localizacao['periodo_fim']
                        )
                    )
                    contador += 1
                    logger.info(
                        f"Relacionamento inserido: encontro_id={encontro['id']}, "
                        f"localizacao_id={localizacao['localizacao_id']}"
                    )

                except psycopg2.Error as e:
                    logger.error(
                        f"Erro ao inserir relacionamento "
                        f"encontro {encontro['id']}, "
                        f"localização {localizacao['localizacao_id']}: {e}"
                    )
                    conexao.rollback()
                    raise

        conexao.commit()
        logger.info(f"Total de relacionamentos processados: {contador}")

    finally:
        cursor.close()

    return contador


def criar_tabela_condicoes(conexao):
    """
    Cria tabela 'condicoes' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - code_system: VARCHAR(500)
    - code_value: VARCHAR(100)
    - code_display: TEXT
    - paciente_id: VARCHAR(255), chave estrangeira referenciando pacientes
    - encontro_id: VARCHAR(255), chave estrangeira referenciando encontros (opcional)

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS condicoes (
        id VARCHAR(255) PRIMARY KEY,
        code_system VARCHAR(500),
        code_value VARCHAR(100),
        code_display TEXT,
        paciente_id VARCHAR(255) REFERENCES pacientes(id),
        encontro_id VARCHAR(255) REFERENCES encontros(id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'condicoes' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def criar_tabela_procedimentos(conexao):
    """
    Cria tabela 'procedimentos' se não existir.

    A tabela possui colunas:
    - id: VARCHAR(255), chave primária
    - code_value: VARCHAR(100)
    - code_display: TEXT
    - status: VARCHAR(50)
    - performed_date_time: TIMESTAMP
    - paciente_id: VARCHAR(255), chave estrangeira referenciando pacientes
    - encontro_id: VARCHAR(255), chave estrangeira referenciando encontros (opcional)

    Args:
        conexao (psycopg2.connection): Conexão com o banco.

    Raises:
        psycopg2.Error: Se o comando SQL falhar.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS procedimentos (
        id VARCHAR(255) PRIMARY KEY,
        code_value VARCHAR(100),
        code_display TEXT,
        status VARCHAR(50),
        performed_date_time TIMESTAMP,
        paciente_id VARCHAR(255) REFERENCES pacientes(id),
        encontro_id VARCHAR(255) REFERENCES encontros(id)
    )
    """

    try:
        cursor = conexao.cursor()
        cursor.execute(sql)
        conexao.commit()
        logger.info("Tabela 'procedimentos' criada ou já existe")

    except psycopg2.Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        conexao.rollback()
        raise

    finally:
        cursor.close()


def inserir_procedimentos(conexao, registros):
    """
    Insere registros de procedimentos na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com campos de procedimento.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO procedimentos
    (id, code_value, code_display, status, performed_date_time,
     paciente_id, encontro_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
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
                        registro['code_value'],
                        registro['code_display'],
                        registro['status'],
                        registro['performed_date_time'],
                        registro['paciente_id'],
                        registro['encontro_id']
                    )
                )
                contador += 1
                logger.info(
                    f"Procedimento inserido: id={registro['id']}, "
                    f"code={registro['code_value']}, "
                    f"paciente_id={registro['paciente_id']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir procedimento {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de procedimentos processados: {contador}")

    finally:
        cursor.close()

    return contador


def inserir_condicoes(conexao, registros):
    """
    Insere registros de condições na tabela.

    Usa INSERT ... ON CONFLICT para garantir idempotência:
    se um registro com mesmo 'id' já existe, é ignorado.

    Args:
        conexao (psycopg2.connection): Conexão com o banco.
        registros (list): Lista de dicionários com campos de condição.

    Returns:
        int: Número de registros processados.

    Raises:
        psycopg2.Error: Se algum INSERT falhar.
    """
    sql = """
    INSERT INTO condicoes (id, code_system, code_value, code_display, paciente_id, encontro_id)
    VALUES (%s, %s, %s, %s, %s, %s)
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
                        registro['code_system'],
                        registro['code_value'],
                        registro['code_display'],
                        registro['paciente_id'],
                        registro['encontro_id']
                    )
                )
                contador += 1
                logger.info(
                    f"Condição inserida: id={registro['id']}, "
                    f"code={registro['code_value']}, "
                    f"paciente_id={registro['paciente_id']}"
                )

            except psycopg2.Error as e:
                logger.error(
                    f"Erro ao inserir condição {registro['id']}: {e}"
                )
                conexao.rollback()
                raise

        conexao.commit()
        logger.info(f"Total de condições processadas: {contador}")

    finally:
        cursor.close()

    return contador
