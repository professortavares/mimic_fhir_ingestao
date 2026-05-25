"""Módulo para geração de dicionário de dados YAML a partir do banco PostgreSQL."""

import datetime
import logging
import os

import yaml
from psycopg2 import sql as psycopg2_sql

logger = logging.getLogger(__name__)

TABELAS = [
    'organizacoes',
    'localizacoes',
    'pacientes',
    'encontros',
    'encontros_localizacoes',
    'condicoes',
    'procedimentos',
]

DESCRICOES_TABELAS = {
    'organizacoes': 'Organizações hospitalares ou de saúde do MIMIC FHIR.',
    'localizacoes': 'Localizações físicas (leitos, alas) vinculadas a organizações.',
    'pacientes': 'Pacientes do conjunto de dados MIMIC FHIR.',
    'encontros': 'Encontros (visitas ou internações) de pacientes.',
    'encontros_localizacoes': 'Relacionamento entre encontros e localizações com seus períodos.',
    'condicoes': 'Condições clínicas diagnosticadas em pacientes.',
    'procedimentos': 'Procedimentos clínicos realizados em pacientes.',
}

DESCRICOES_COLUNAS = {
    'id': 'Identificador único do registro.',
    'nome': 'Nome descritivo.',
    'organizacao_id': 'Referência à organização associada.',
    'nome_familia': 'Sobrenome do paciente.',
    'genero': 'Gênero do paciente (male, female, etc.).',
    'data_nascimento': 'Data de nascimento do paciente.',
    'raca': 'Raça ou etnia do paciente.',
    'identificador': 'Identificador externo (ex.: MRN).',
    'idioma': 'Código de idioma preferencial (ex.: en, pt).',
    'estado_civil': 'Estado civil do paciente.',
    'tipo': 'Tipo do encontro.',
    'classe': 'Classe do encontro (IMP, AMB, etc.).',
    'periodo_inicio': 'Data e hora de início do período.',
    'periodo_fim': 'Data e hora de fim do período.',
    'status': 'Status do registro.',
    'hospitalizacao_code': 'Código da fonte de admissão hospitalar.',
    'alta_code': 'Código do destino de alta hospitalar.',
    'paciente_id': 'Referência ao paciente associado.',
    'encontro_id': 'Referência ao encontro associado.',
    'localizacao_id': 'Referência à localização associada.',
    'code_system': 'URI do sistema de codificação (ex.: SNOMED, ICD).',
    'code_value': 'Código do termo no sistema de codificação.',
    'code_display': 'Descrição legível do código.',
    'performed_date_time': 'Data e hora em que o procedimento foi realizado.',
}


def obter_colunas_tabela(conexao, nome_tabela):
    """
    Consulta information_schema para obter metadados de colunas de uma tabela.

    Args:
        conexao: Conexão com o banco.
        nome_tabela (str): Nome da tabela a consultar.

    Returns:
        list[dict]: Lista de dicts com chaves 'nome_coluna', 'tipo_dado', 'nullable'.
                    'nullable' é bool (True se a coluna aceita NULL).

    Raises:
        psycopg2.Error: Se a consulta SQL falhar.
    """
    cursor = conexao.cursor()
    try:
        query = (
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s "
            "ORDER BY ordinal_position"
        )
        cursor.execute(query, (nome_tabela,))
        linhas = cursor.fetchall()
    finally:
        cursor.close()

    resultado = []
    for linha in linhas:
        resultado.append({
            'nome_coluna': linha[0],
            'tipo_dado': linha[1],
            'nullable': linha[2] == 'YES'
        })
    return resultado


def obter_chaves_primarias(conexao, nome_tabela):
    """
    Consulta information_schema para identificar colunas que são chave primária.

    Args:
        conexao: Conexão com o banco.
        nome_tabela (str): Nome da tabela a consultar.

    Returns:
        set[str]: Conjunto de nomes de colunas que compõem a chave primária.

    Raises:
        psycopg2.Error: Se a consulta SQL falhar.
    """
    cursor = conexao.cursor()
    try:
        query = (
            "SELECT kcu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "WHERE tc.constraint_type = 'PRIMARY KEY' "
            "  AND tc.table_schema = 'public' "
            "  AND tc.table_name = %s"
        )
        cursor.execute(query, (nome_tabela,))
        linhas = cursor.fetchall()
    finally:
        cursor.close()

    return {linha[0] for linha in linhas}


def obter_chaves_estrangeiras(conexao, nome_tabela):
    """
    Consulta information_schema para identificar colunas com FK e sua tabela de destino.

    Args:
        conexao: Conexão com o banco.
        nome_tabela (str): Nome da tabela a consultar.

    Returns:
        dict[str, str]: Mapeamento coluna_origem -> tabela_destino.

    Raises:
        psycopg2.Error: Se a consulta SQL falhar.
    """
    cursor = conexao.cursor()
    try:
        query = (
            "SELECT kcu.column_name, ccu.table_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON ccu.constraint_name = tc.constraint_name "
            "  AND ccu.table_schema = tc.table_schema "
            "WHERE tc.constraint_type = 'FOREIGN KEY' "
            "  AND tc.table_schema = 'public' "
            "  AND tc.table_name = %s"
        )
        cursor.execute(query, (nome_tabela,))
        linhas = cursor.fetchall()
    finally:
        cursor.close()

    return {linha[0]: linha[1] for linha in linhas}


def obter_exemplos_coluna(conexao, nome_tabela, nome_coluna):
    """
    Obtém até 3 valores distintos não-nulos de uma coluna como exemplos.

    Converte datetime.date, datetime.datetime para string ISO 8601.
    Retorna lista vazia se a tabela estiver vazia ou a coluna só tiver NULLs.

    Args:
        conexao: Conexão com o banco.
        nome_tabela (str): Nome da tabela.
        nome_coluna (str): Nome da coluna.

    Returns:
        list: Lista com até 3 valores (str, int, float, etc.) serializáveis em YAML.

    Raises:
        psycopg2.Error: Se a consulta SQL falhar.
    """
    cursor = conexao.cursor()
    try:
        query = psycopg2_sql.SQL(
            "SELECT DISTINCT {col} FROM {tab} WHERE {col} IS NOT NULL LIMIT 3"
        ).format(
            col=psycopg2_sql.Identifier(nome_coluna),
            tab=psycopg2_sql.Identifier(nome_tabela)
        )
        cursor.execute(query)
        linhas = cursor.fetchall()
    finally:
        cursor.close()

    exemplos = []
    for linha in linhas:
        valor = linha[0]
        if isinstance(valor, datetime.datetime):
            valor = valor.isoformat()
        elif isinstance(valor, datetime.date):
            valor = valor.isoformat()
        exemplos.append(valor)

    if not exemplos:
        logger.debug(
            f"Nenhum valor de exemplo encontrado para {nome_tabela}.{nome_coluna}"
        )
    return exemplos


def construir_dicionario(conexao):
    """
    Monta a estrutura completa do dicionário de dados consultando o banco.

    Itera sobre TABELAS, chama obter_colunas_tabela, obter_chaves_primarias,
    obter_chaves_estrangeiras e obter_exemplos_coluna para cada coluna.

    Args:
        conexao: Conexão com o banco.

    Returns:
        dict: Estrutura completa do dicionário pronta para serialização YAML.

    Raises:
        psycopg2.Error: Se qualquer consulta SQL falhar.
    """
    tabelas_dict = []

    for nome_tabela in TABELAS:
        logger.debug(f"Coletando metadados para tabela: {nome_tabela}")

        colunas_info = obter_colunas_tabela(conexao, nome_tabela)
        pks = obter_chaves_primarias(conexao, nome_tabela)
        fks = obter_chaves_estrangeiras(conexao, nome_tabela)

        colunas_dict = []
        for col_info in colunas_info:
            nome_coluna = col_info['nome_coluna']

            exemplos = obter_exemplos_coluna(conexao, nome_tabela, nome_coluna)

            coluna_dict = {
                'nome': nome_coluna,
                'descricao': DESCRICOES_COLUNAS.get(
                    nome_coluna,
                    'Sem descrição disponível'
                ),
                'tipo': col_info['tipo_dado'],
                'obrigatorio': not col_info['nullable'],
                'chave_primaria': nome_coluna in pks,
                'chave_estrangeira': fks.get(nome_coluna),
                'exemplos': exemplos,
            }
            colunas_dict.append(coluna_dict)

        tabela_dict = {
            'nome': nome_tabela,
            'descricao': DESCRICOES_TABELAS[nome_tabela],
            'colunas': colunas_dict,
        }
        tabelas_dict.append(tabela_dict)

    return {'tabelas': tabelas_dict}


def salvar_dicionario_yaml(dicionario, caminho_arquivo):
    """
    Serializa o dicionário de dados em YAML e salva no caminho especificado.

    Cria o diretório pai se não existir.

    Args:
        dicionario (dict): Estrutura de dados a serializar.
        caminho_arquivo (str): Caminho completo do arquivo de saída.

    Raises:
        OSError: Se não for possível criar o diretório ou escrever o arquivo.
    """
    diretorio = os.path.dirname(os.path.abspath(caminho_arquivo))
    os.makedirs(diretorio, exist_ok=True)

    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        yaml.dump(
            dicionario,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )
    logger.info(f"Dicionário de dados salvo em: {caminho_arquivo}")


def gerar_dicionario(conexao, caminho_arquivo='./dic/dicionario_dados.yaml'):
    """
    Ponto de entrada público: constrói e salva o dicionário de dados.

    Orquestra construir_dicionario() e salvar_dicionario_yaml().

    Args:
        conexao: Conexão ativa com o banco.
        caminho_arquivo (str): Caminho de saída para o YAML.
                               Padrão: './dic/dicionario_dados.yaml'.

    Raises:
        Exception: Propaga qualquer erro para o chamador (sem swallow silencioso).
    """
    logger.info("Iniciando geração do dicionário de dados")
    dicionario = construir_dicionario(conexao)
    salvar_dicionario_yaml(dicionario, caminho_arquivo)
    logger.info("Dicionário de dados gerado com sucesso")
