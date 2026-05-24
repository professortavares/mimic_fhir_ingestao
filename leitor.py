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
