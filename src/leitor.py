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


def extrair_campos_encounter(registro):
    """
    Extrai campos de um registro JSON FHIR Encounter.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Encounter.

    Returns:
        dict: Dicionário com chaves 'id', 'tipo', 'classe', 'periodo_inicio',
              'periodo_fim', 'status', 'hospitalizacao_code', 'alta_code',
              'paciente_id', 'localizacoes'.

    Raises:
        ValueError: Se algum campo obrigatório estiver ausente.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'subject' not in registro:
        raise ValueError("Campo obrigatório ausente: 'subject'")

    reference = registro['subject'].get('reference', '')
    if not reference:
        raise ValueError("Campo vazio ou inválido: 'subject.reference'")

    paciente_id = reference.split('/')[-1]

    tipo = None
    if 'type' in registro and isinstance(registro['type'], list) and len(registro['type']) > 0:
        coding = registro['type'][0].get('coding', [])
        if coding and len(coding) > 0:
            tipo = coding[0].get('display', '')

    classe = None
    if 'class' in registro:
        classe = registro['class'].get('code', '')

    periodo_inicio = registro.get('period', {}).get('start', None)
    periodo_fim = registro.get('period', {}).get('end', None)

    status = registro.get('status', None)

    hospitalizacao_code = None
    if 'hospitalization' in registro:
        coding = registro['hospitalization'].get('coding', [])
        if coding and len(coding) > 0:
            hospitalizacao_code = coding[0].get('code', '')

    alta_code = None
    if 'dischargeDisposition' in registro:
        coding = registro['dischargeDisposition'].get('coding', [])
        if coding and len(coding) > 0:
            alta_code = coding[0].get('code', '')

    localizacoes = []
    if 'location' in registro and isinstance(registro['location'], list):
        for loc in registro['location']:
            localizacao_id = None
            loc_periodo_inicio = None
            loc_periodo_fim = None

            if 'location' in loc:
                reference = loc['location'].get('reference', '')
                if reference:
                    localizacao_id = reference.split('/')[-1]

            if 'period' in loc:
                loc_periodo_inicio = loc['period'].get('start', None)
                loc_periodo_fim = loc['period'].get('end', None)

            if localizacao_id:
                localizacoes.append({
                    'localizacao_id': localizacao_id,
                    'periodo_inicio': loc_periodo_inicio,
                    'periodo_fim': loc_periodo_fim
                })

    return {
        'id': registro['id'],
        'tipo': tipo,
        'classe': classe,
        'periodo_inicio': periodo_inicio,
        'periodo_fim': periodo_fim,
        'status': status,
        'hospitalizacao_code': hospitalizacao_code,
        'alta_code': alta_code,
        'paciente_id': paciente_id,
        'localizacoes': localizacoes
    }


def ler_encontros(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de encontros.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    um encontro (Encounter) FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id', 'tipo', 'classe',
              'periodo_inicio', 'periodo_fim', 'status', 'hospitalizacao_code',
              'alta_code', 'paciente_id', 'localizacoes'.

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
                    registro_extraido = extrair_campos_encounter(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Encontro {numero_linha} lido com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Encontro {numero_linha} ignorado: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de encontros lidos com sucesso: {len(registros)}")
    return registros


def extrair_campos_condition(registro):
    """
    Extrai campos de um registro JSON FHIR Condition.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Condition.

    Returns:
        dict: Dicionário com chaves 'id', 'code_system', 'code_value', 'code_display',
              'paciente_id', 'encontro_id'.

    Raises:
        ValueError: Se algum campo obrigatório estiver ausente.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'subject' not in registro:
        raise ValueError("Campo obrigatório ausente: 'subject'")

    reference = registro['subject'].get('reference', '')
    if not reference:
        raise ValueError("Campo vazio ou inválido: 'subject.reference'")

    paciente_id = reference.split('/')[-1]

    encontro_id = None
    if 'encounter' in registro:
        reference = registro['encounter'].get('reference', '')
        if reference:
            encontro_id = reference.split('/')[-1]

    code_system = None
    code_value = None
    code_display = None
    if 'code' in registro:
        coding = registro['code'].get('coding', [])
        if coding and len(coding) > 0:
            code_system = coding[0].get('system', '')
            code_value = coding[0].get('code', '')
            code_display = coding[0].get('display', '')

    return {
        'id': registro['id'],
        'code_system': code_system,
        'code_value': code_value,
        'code_display': code_display,
        'paciente_id': paciente_id,
        'encontro_id': encontro_id
    }


def extrair_campos_procedure(registro):
    """
    Extrai campos de um registro JSON FHIR Procedure.

    Args:
        registro (dict): Dicionário contendo um registro FHIR Procedure.

    Returns:
        dict: Dicionário com chaves 'id', 'code_value', 'code_display', 'status',
              'performed_date_time', 'paciente_id', 'encontro_id'.

    Raises:
        ValueError: Se algum campo obrigatório estiver ausente.
    """
    if 'id' not in registro:
        raise ValueError("Campo obrigatório ausente: 'id'")
    if 'subject' not in registro:
        raise ValueError("Campo obrigatório ausente: 'subject'")

    reference = registro['subject'].get('reference', '')
    if not reference:
        raise ValueError("Campo vazio ou inválido: 'subject.reference'")

    paciente_id = reference.split('/')[-1]

    encontro_id = None
    if 'encounter' in registro:
        reference = registro['encounter'].get('reference', '')
        if reference:
            encontro_id = reference.split('/')[-1]

    code_value = None
    code_display = None
    if 'code' in registro:
        coding = registro['code'].get('coding', [])
        if coding and len(coding) > 0:
            code_value = coding[0].get('code', '')
            code_display = coding[0].get('display', '')

    status = registro.get('status', None)
    performed_date_time = registro.get('performedDateTime', None)

    return {
        'id': registro['id'],
        'code_value': code_value,
        'code_display': code_display,
        'status': status,
        'performed_date_time': performed_date_time,
        'paciente_id': paciente_id,
        'encontro_id': encontro_id
    }


def ler_procedimentos(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de procedimentos.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    um procedimento (Procedure) FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id', 'code_value', 'code_display',
              'status', 'performed_date_time', 'paciente_id', 'encontro_id'.

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
                    registro_extraido = extrair_campos_procedure(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Procedimento {numero_linha} lido com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Procedimento {numero_linha} ignorado: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de procedimentos lidos com sucesso: {len(registros)}")
    return registros


def ler_condicoes(caminho_arquivo):
    """
    Lê arquivo NDJSON.gz e extrai registros de condições.

    Cada linha do arquivo deve conter um objeto JSON válido representando
    uma condição (Condition) FHIR. Linhas com campos obrigatórios ausentes são
    ignoradas com um aviso de log.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.

    Returns:
        list: Lista de dicionários com chaves 'id', 'code_system', 'code_value',
              'code_display', 'paciente_id', 'encontro_id'.

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
                    registro_extraido = extrair_campos_condition(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"Condição {numero_linha} lida com sucesso: "
                        f"id={registro_extraido['id']}"
                    )

                except ValueError as e:
                    logger.warning(
                        f"Condição {numero_linha} ignorada: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de condições lidas com sucesso: {len(registros)}")
    return registros
