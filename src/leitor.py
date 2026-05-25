"""Módulo para leitura de arquivos NDJSON comprimidos com gzip."""

import gzip
import json
import logging

logger = logging.getLogger(__name__)

MSG_CAMPO_ID_AUSENTE = "Campo obrigatório ausente: 'id'"
MSG_CAMPO_NAME_AUSENTE = "Campo obrigatório ausente: 'name'"
MSG_CAMPO_SUBJECT_AUSENTE = "Campo obrigatório ausente: 'subject'"
MSG_REFERENCE_INVALIDA = "Campo vazio ou inválido: 'subject.reference'"
MSG_MANAGING_ORG_AUSENTE = "Campo obrigatório ausente: 'managingOrganization'"
MSG_MANAGING_ORG_INVALIDA = "Campo vazio ou inválido: 'managingOrganization.reference'"


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
        raise ValueError(MSG_CAMPO_ID_AUSENTE)
    if 'name' not in registro:
        raise ValueError(MSG_CAMPO_NAME_AUSENTE)

    return {
        'id': registro['id'],
        'nome': registro['name']
    }


def _ler_arquivo_generico(caminho_arquivo, funcao_extracao, tipo_registro):
    """
    Função auxiliar para ler arquivo NDJSON.gz e extrair registros.

    Args:
        caminho_arquivo (str): Caminho do arquivo NDJSON.gz.
        funcao_extracao: Função para extrair campos do registro.
        tipo_registro (str): Nome do tipo de registro para logs.

    Returns:
        list: Lista de dicionários extraídos.

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
                    registro_extraido = funcao_extracao(registro_json)
                    registros.append(registro_extraido)
                    logger.info(
                        f"{tipo_registro} {numero_linha} lido com sucesso: "
                        f"id={registro_extraido['id']}"
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"{tipo_registro} {numero_linha} ignorado: {e}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Erro ao fazer parse da linha {numero_linha}: {e}"
                    )
                    raise

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise

    logger.info(f"Total de {tipo_registro.lower()}s lidos com sucesso: {len(registros)}")
    return registros


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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos, "Registro")


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
        raise ValueError(MSG_CAMPO_ID_AUSENTE)
    if 'name' not in registro:
        raise ValueError(MSG_CAMPO_NAME_AUSENTE)
    if 'managingOrganization' not in registro:
        raise ValueError(MSG_MANAGING_ORG_AUSENTE)

    reference = registro['managingOrganization'].get('reference', '')
    if not reference:
        raise ValueError(MSG_MANAGING_ORG_INVALIDA)

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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos_location, "Localização")


def _extrair_raca_from_extensions(extensions):
    """Extrai raça dos extensions de um registro Patient."""
    if not extensions or not isinstance(extensions, list):
        return None

    for ext in extensions:
        if not ext.get('url', '').endswith('race'):
            continue

        value_coding = ext.get('valueCodeableConcept', {})
        coding = value_coding.get('coding', [])
        if coding and len(coding) > 0:
            return coding[0].get('display', '')

        nested_ext = ext.get('extension', [])
        if isinstance(nested_ext, list):
            for nested in nested_ext:
                value_obj = nested.get('valueCoding', {})
                if value_obj.get('display'):
                    return value_obj.get('display', '')

    return None


def _extrair_identificador_from_list(identifiers):
    """Extrai primeiro identificador de uma lista."""
    if identifiers and isinstance(identifiers, list) and len(identifiers) > 0:
        return identifiers[0].get('value', '')
    return None


def _extrair_idioma_from_communication(communications):
    """Extrai código de idioma do primeiro item de comunicação."""
    if communications and isinstance(communications, list) and len(communications) > 0:
        language = communications[0].get('language', {})
        coding = language.get('coding', [])
        if coding and len(coding) > 0:
            return coding[0].get('code', '')
    return None


def _extrair_codigo_from_coding(coding_field):
    """Extrai código do primeiro item em um coding."""
    if coding_field and isinstance(coding_field, dict):
        coding = coding_field.get('coding', [])
        if coding and len(coding) > 0:
            return coding[0].get('code', '')
    return None


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
        raise ValueError(MSG_CAMPO_ID_AUSENTE)
    if 'name' not in registro or not registro['name']:
        raise ValueError(MSG_CAMPO_NAME_AUSENTE)
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

    raca = _extrair_raca_from_extensions(registro.get('extension'))
    identificador = _extrair_identificador_from_list(registro.get('identifier'))
    idioma = _extrair_idioma_from_communication(registro.get('communication'))
    estado_civil = _extrair_codigo_from_coding(registro.get('maritalStatus'))

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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos_patient, "Paciente")


def _extrair_tipo_from_encounter(tipo_list):
    """Extrai tipo de display do primeiro coding da lista type."""
    if tipo_list and isinstance(tipo_list, list) and len(tipo_list) > 0:
        coding = tipo_list[0].get('coding', [])
        if coding and len(coding) > 0:
            return coding[0].get('display', '')
    return None


def _extrair_classe_from_encounter(classe_obj):
    """Extrai código da classe."""
    if classe_obj and isinstance(classe_obj, dict):
        return classe_obj.get('code', '')
    return None


def _extrair_hosp_admit_source(registro_id, hosp):
    """Extrai código de admissão hospitalar."""
    if not hosp or 'admitSource' not in hosp:
        return None

    coding = hosp['admitSource'].get('coding', [])
    if coding and len(coding) > 0:
        return coding[0].get('code', None)

    logger.debug(
        f"Registro {registro_id}: hospitalizacao_code vazio ou ausente"
    )
    return None


def _extrair_hosp_discharge_disposition(registro_id, hosp):
    """Extrai código de alta hospitalar."""
    if not hosp or 'dischargeDisposition' not in hosp:
        return None

    coding = hosp['dischargeDisposition'].get('coding', [])
    if coding and len(coding) > 0:
        return coding[0].get('code', None)

    logger.debug(
        f"Registro {registro_id}: alta_code vazio ou ausente"
    )
    return None


def _extrair_localizacoes_from_encounter(location_list):
    """Extrai lista de localizações com seus períodos."""
    localizacoes = []
    if not location_list or not isinstance(location_list, list):
        return localizacoes

    for loc in location_list:
        localizacao_id = None
        if 'location' in loc:
            reference = loc['location'].get('reference', '')
            if reference:
                localizacao_id = reference.split('/')[-1]

        if not localizacao_id:
            continue

        loc_periodo_inicio = None
        loc_periodo_fim = None
        if 'period' in loc:
            loc_periodo_inicio = loc['period'].get('start', None)
            loc_periodo_fim = loc['period'].get('end', None)

        localizacoes.append({
            'localizacao_id': localizacao_id,
            'periodo_inicio': loc_periodo_inicio,
            'periodo_fim': loc_periodo_fim
        })

    return localizacoes


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
        raise ValueError(MSG_CAMPO_ID_AUSENTE)
    if 'subject' not in registro:
        raise ValueError(MSG_CAMPO_SUBJECT_AUSENTE)

    reference = registro['subject'].get('reference', '')
    if not reference:
        raise ValueError(MSG_REFERENCE_INVALIDA)

    paciente_id = reference.split('/')[-1]

    tipo = _extrair_tipo_from_encounter(registro.get('type'))
    classe = _extrair_classe_from_encounter(registro.get('class'))
    periodo_inicio = registro.get('period', {}).get('start', None)
    periodo_fim = registro.get('period', {}).get('end', None)
    status = registro.get('status', None)

    registro_id = registro.get('id', 'unknown')
    hosp = registro.get('hospitalization')
    hospitalizacao_code = _extrair_hosp_admit_source(registro_id, hosp)
    alta_code = _extrair_hosp_discharge_disposition(registro_id, hosp)

    localizacoes = _extrair_localizacoes_from_encounter(registro.get('location'))

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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos_encounter, "Encontro")


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
        raise ValueError(MSG_CAMPO_ID_AUSENTE)
    if 'subject' not in registro:
        raise ValueError(MSG_CAMPO_SUBJECT_AUSENTE)

    reference = registro['subject'].get('reference', '')
    if not reference:
        raise ValueError(MSG_REFERENCE_INVALIDA)

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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos_procedure, "Procedimento")


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
    return _ler_arquivo_generico(caminho_arquivo, extrair_campos_condition, "Condição")
