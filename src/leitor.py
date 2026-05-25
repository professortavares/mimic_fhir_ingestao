"""Módulo para leitura de arquivos NDJSON comprimidos com gzip."""

import gzip
import json
import logging

logger = logging.getLogger(__name__)


def extrair_campos(registro):
    """
    Extrai campos 'id' e 'name' de um registro JSON FHIR.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Organization.

    Returns:
        dict: Dicionário com chaves 'id' e 'nome'.

    Raises:
        ValueError: Se 'id' ou 'name' estão ausentes do registro.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'name' not in registro:
        raise ValueError("Campo obrigatório ausente: 'name'")

    return {
        'id': registro['id'],
        'nome': registro['name']
    }


def ler_registros(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de organizações.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    uma organização FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id' e 'nome'.

    Raises:
        FileNotFoundError: Se o arquivo não existe.
        json.JSONDecodeError: Se uma linha não é JSON válido.
    """
    registros = []

    try:
        with gzip.open(caminho_arquivo, 'rt', encoding='utf-8') as arquivo:
            for numero_linha, linha in enumerate(arquivo, start=1):
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    registro_json = json.loads(linha)
                    registro_extraido = extrair_campos(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Registro {numero_linha} lido com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Registro {numero_linha} ignorado: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de registros lidos com sucesso: {len(registros)}")
    return registros


def extrair_campos_location(registro):
    """
    Extrai campos de um registro JSON FHIR Location.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Location.

    Returns:
        dict: Dicionário com chaves 'id', 'nome', 'organizacao_id'.

    Raises:
        ValueError: Se algum campo obrigatório estiver ausente.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'name' not in registro:
        raise ValueError("Campo obrigatório ausente: 'name'")
    if 'managingOrganization' not in registro:
        raise ValueError("Campo obrigatório ausente: 'managingOrganization'")

    reference = registro['managingOrganization'].get('reference', '')
    if not reference:
        raise ValueError("Campo vazio ou inválido: 'managingOrganization.reference'")

    organizacao_id = reference.split('/')[-1]

    return {
        'id': registro['id'],
        'nome': registro['name'],
        'organizacao_id': organizacao_id
    }


def ler_localizacoes(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de localizações.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    uma localização FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id', 'nome', 'organizacao_id'.

    Raises:
        FileNotFoundError: Se o arquivo não existe.
        json.JSONDecodeError: Se uma linha não é JSON válido.
    """
    registros = []

    try:
        with gzip.open(caminho_arquivo, 'rt', encoding='utf-8') as arquivo:
            for numero_linha, linha in enumerate(arquivo, start=1):
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    registro_json = json.loads(linha)
                    registro_extraido = extrair_campos_location(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Localização {numero_linha} lida com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Localização {numero_linha} ignorada: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de localizações lidas com sucesso: {len(registros)}")
    return registros


def extrair_campos_patient(registro):
    """
    Extrai campos de um registro JSON FHIR Patient.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Patient.

    Returns:
        dict: Dicionário com chaves 'id', 'nome_familia', 'genero', 'data_nascimento',
              'raca', 'identificador', 'idioma', 'estado_civil', 'organizacao_id'.

    Raises:
        ValueError: Se algum campo obrigatório estiver ausente.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'name' not in registro or not registro['name']:
        raise ValueError("Campo obrigatório ausente: 'name'")
    if 'gender' not in registro:
        raise ValueError("Campo obrigatório ausente: 'gender'")

    name_list = registro['name']
    if not isinstance(name_list, list) or len(name_list) == 0:
        raise ValueError("Campo inválido: 'name' deve ser uma lista não vazia")

    nome_familia = name_list[0].get('family', '')
    if not nome_familia:
        raise ValueError("Campo vazio: 'name[0].family'")

    organizacao_id = None
    if 'managingOrganization' in registro:
        reference = registro['managingOrganization'].get('reference', '')
        if reference:
            organizacao_id = reference.split('/')[-1]

    raca = None
    if 'extension' in registro and isinstance(registro['extension'], list):
        for ext in registro['extension']:
            if ext.get('url', '').endswith('race'):
                value_coding = ext.get('valueCodeableConcept', {})
                coding = value_coding.get('coding', [])
                if coding and len(coding) > 0:
                    raca = coding[0].get('display', '')
                    break
                nested_ext = ext.get('extension', [])
                if isinstance(nested_ext, list):
                    for nested in nested_ext:
                        value_obj = nested.get('valueCoding', {})
                        if value_obj.get('display'):
                            raca = value_obj.get('display', '')
                            break
                if raca:
                    break

    identificador = None
    if 'identifier' in registro and isinstance(registro['identifier'], list):
        if len(registro['identifier']) > 0:
            identificador = registro['identifier'][0].get('value', '')

    idioma = None
    if 'communication' in registro and isinstance(registro['communication'], list):
        if len(registro['communication']) > 0:
            language = registro['communication'][0].get('language', {})
            coding = language.get('coding', [])
            if coding and len(coding) > 0:
                idioma = coding[0].get('code', '')

    estado_civil = None
    if 'maritalStatus' in registro:
        coding = registro['maritalStatus'].get('coding', [])
        if coding and len(coding) > 0:
            estado_civil = coding[0].get('code', '')

    data_nascimento = registro.get('birthDate', None)

    return {
        'id': registro['id'],
        'nome_familia': nome_familia,
        'genero': registro['gender'],
        'data_nascimento': data_nascimento,
        'raca': raca,
        'identificador': identificador,
        'idioma': idioma,
        'estado_civil': estado_civil,
        'organizacao_id': organizacao_id
    }


def ler_pacientes(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de pacientes.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    um paciente FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id', 'nome_familia', 'genero',
              'data_nascimento', 'raca', 'identificador', 'idioma', 'estado_civil',
              'organizacao_id'.

    Raises:
        FileNotFoundError: Se o arquivo não existe.
        json.JSONDecodeError: Se uma linha não é JSON válido.
    """
    registros = []

    try:
        with gzip.open(caminho_arquivo, 'rt', encoding='utf-8') as arquivo:
            for numero_linha, linha in enumerate(arquivo, start=1):
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    registro_json = json.loads(linha)
                    registro_extraido = extrair_campos_patient(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Paciente {numero_linha} lido com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Paciente {numero_linha} ignorado: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de pacientes lidos com sucesso: {len(registros)}")
    return registros
