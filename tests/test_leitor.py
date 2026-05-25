"""Testes para o módulo leitor."""

import gzip
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from leitor import (
    extrair_campos,
    ler_registros,
    extrair_campos_location,
    ler_localizacoes,
    extrair_campos_patient,
    ler_pacientes,
    extrair_campos_encounter,
    ler_encontros
)


class TestExtrairCampos(unittest.TestCase):
    """Testes para a função extrair_campos."""

    def test_extrair_campos_sucesso(self):
        """Testa extração com dict válido contendo id e name."""
        registro = {
            'id': 'ee172322-118b-5716-abbc-18e4c5437e15',
            'name': 'Beth Israel Deaconess Medical Center',
            'resourceType': 'Organization',
            'active': True
        }

        resultado = extrair_campos(registro)

        self.assertEqual(resultado['id'], 'ee172322-118b-5716-abbc-18e4c5437e15')
        self.assertEqual(resultado['nome'], 'Beth Israel Deaconess Medical Center')

    def test_extrair_campos_sem_id(self):
        """Testa que ValueError é levantado se 'id' está ausente."""
        registro = {'name': 'Organização A'}

        with self.assertRaises(ValueError) as contexto:
            extrair_campos(registro)

        self.assertIn('id', str(contexto.exception))

    def test_extrair_campos_sem_nome(self):
        """Testa que ValueError é levantado se 'name' está ausente."""
        registro = {'id': '123'}

        with self.assertRaises(ValueError) as contexto:
            extrair_campos(registro)

        self.assertIn('name', str(contexto.exception))

    def test_extrair_campos_campos_extras(self):
        """Testa que campos extras não afetam a extração."""
        registro = {
            'id': '123',
            'name': 'Test Org',
            'resourceType': 'Organization',
            'active': True,
            'type': [{'coding': []}]
        }

        resultado = extrair_campos(registro)

        self.assertEqual(resultado['id'], '123')
        self.assertEqual(resultado['nome'], 'Test Org')
        self.assertEqual(len(resultado), 2)


class TestLerRegistros(unittest.TestCase):
    """Testes para a função ler_registros."""

    def test_ler_registros_sucesso(self):
        """Testa leitura bem-sucedida de arquivo NDJSON.gz."""
        dados = [
            {'id': '123', 'name': 'Org 1'},
            {'id': '456', 'name': 'Org 2'}
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_registros(tmp.name)

                self.assertEqual(len(resultado), 2)
                self.assertEqual(resultado[0]['id'], '123')
                self.assertEqual(resultado[0]['nome'], 'Org 1')
                self.assertEqual(resultado[1]['id'], '456')
                self.assertEqual(resultado[1]['nome'], 'Org 2')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_registros_arquivo_nao_encontrado(self):
        """Testa que FileNotFoundError é levantado para arquivo inexistente."""
        with self.assertRaises(FileNotFoundError):
            ler_registros('/arquivo/inexistente.gz')

    def test_ler_registros_json_invalido(self):
        """Testa que registros com JSON inválido são ignorados."""
        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                gz.write('{"id": "123", "name": "Org 1}\n')  # JSON inválido
                gz.write('{"id": "456", "name": "Org 2"}\n')  # JSON válido

            try:
                resultado = ler_registros(tmp.name)
                # O primeiro registro inválido é ignorado, apenas o segundo é retornado
                self.assertEqual(len(resultado), 1)
                self.assertEqual(resultado[0]['id'], '456')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_registros_campos_ausentes(self):
        """Testa que registros com campos ausentes são ignorados."""
        dados = [
            {'id': '123', 'name': 'Org 1'},
            {'id': '456'},  # sem name
            {'name': 'Org 3'}  # sem id
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_registros(tmp.name)

                # Apenas o primeiro registro deve estar na lista
                self.assertEqual(len(resultado), 1)
                self.assertEqual(resultado[0]['id'], '123')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_registros_arquivo_vazio(self):
        """Testa leitura de arquivo vazio."""
        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                pass  # Arquivo vazio

            try:
                resultado = ler_registros(tmp.name)
                self.assertEqual(len(resultado), 0)

            finally:
                import os
                os.unlink(tmp.name)


class TestExtrairCamposLocation(unittest.TestCase):
    """Testes para a função extrair_campos_location."""

    def test_extrair_campos_location_sucesso(self):
        """Testa extração com dict válido contendo id, name e managingOrganization."""
        registro = {
            'id': 'ecbf468a-22ec-5320-8e11-6ebcc918dad5',
            'name': 'Cardiology Surgery Intermediate',
            'resourceType': 'Location',
            'status': 'active',
            'managingOrganization': {
                'reference': 'Organization/ee172322-118b-5716-abbc-18e4c5437e15'
            }
        }

        resultado = extrair_campos_location(registro)

        self.assertEqual(resultado['id'], 'ecbf468a-22ec-5320-8e11-6ebcc918dad5')
        self.assertEqual(resultado['nome'], 'Cardiology Surgery Intermediate')
        self.assertEqual(resultado['organizacao_id'], 'ee172322-118b-5716-abbc-18e4c5437e15')

    def test_extrair_campos_location_sem_managing_org(self):
        """Testa que ValueError é levantado se managingOrganization está ausente."""
        registro = {
            'id': '123',
            'name': 'Localização A'
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_location(registro)

        self.assertIn('managingOrganization', str(contexto.exception))

    def test_extrair_campos_location_sem_id(self):
        """Testa que ValueError é levantado se 'id' está ausente."""
        registro = {
            'name': 'Localização A',
            'managingOrganization': {'reference': 'Organization/123'}
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_location(registro)

        self.assertIn('id', str(contexto.exception))

    def test_extrair_campos_location_sem_nome(self):
        """Testa que ValueError é levantado se 'name' está ausente."""
        registro = {
            'id': '123',
            'managingOrganization': {'reference': 'Organization/456'}
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_location(registro)

        self.assertIn('name', str(contexto.exception))

    def test_extrair_campos_location_reference_invalida(self):
        """Testa que ValueError é levantado se reference está vazia."""
        registro = {
            'id': '123',
            'name': 'Localização A',
            'managingOrganization': {'reference': ''}
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_location(registro)

        self.assertIn('reference', str(contexto.exception).lower())

    def test_extrair_campos_location_extrai_uuid_corretamente(self):
        """Testa que o UUID é extraído corretamente da reference."""
        registro = {
            'id': 'local-1',
            'name': 'Test Location',
            'managingOrganization': {
                'reference': 'Organization/org-uuid-12345'
            }
        }

        resultado = extrair_campos_location(registro)

        self.assertEqual(resultado['organizacao_id'], 'org-uuid-12345')


class TestLerLocalizacoes(unittest.TestCase):
    """Testes para a função ler_localizacoes."""

    def test_ler_localizacoes_sucesso(self):
        """Testa leitura bem-sucedida de arquivo NDJSON.gz de localizações."""
        dados = [
            {
                'id': 'loc-1',
                'name': 'Cardiology',
                'managingOrganization': {'reference': 'Organization/org-1'}
            },
            {
                'id': 'loc-2',
                'name': 'Emergency',
                'managingOrganization': {'reference': 'Organization/org-1'}
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_localizacoes(tmp.name)

                self.assertEqual(len(resultado), 2)
                self.assertEqual(resultado[0]['id'], 'loc-1')
                self.assertEqual(resultado[0]['nome'], 'Cardiology')
                self.assertEqual(resultado[0]['organizacao_id'], 'org-1')
                self.assertEqual(resultado[1]['id'], 'loc-2')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_localizacoes_arquivo_nao_encontrado(self):
        """Testa que FileNotFoundError é levantado para arquivo inexistente."""
        with self.assertRaises(FileNotFoundError):
            ler_localizacoes('/arquivo/inexistente.gz')

    def test_ler_localizacoes_campos_ausentes(self):
        """Testa que registros com campos ausentes são ignorados."""
        dados = [
            {
                'id': 'loc-1',
                'name': 'Localização A',
                'managingOrganization': {'reference': 'Organization/org-1'}
            },
            {
                'id': 'loc-2',
                'name': 'Localização B'
                # sem managingOrganization
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_localizacoes(tmp.name)

                # Apenas o primeiro registro deve estar na lista
                self.assertEqual(len(resultado), 1)
                self.assertEqual(resultado[0]['id'], 'loc-1')

            finally:
                import os
                os.unlink(tmp.name)


class TestExtrairCamposPatient(unittest.TestCase):
    """Testes para a função extrair_campos_patient."""

    def test_extrair_campos_patient_sucesso(self):
        """Testa extração com dict válido contendo campos obrigatórios."""
        registro = {
            'id': 'pat-1',
            'gender': 'male',
            'name': [{'family': 'Silva'}],
            'birthDate': '1980-01-01',
            'managingOrganization': {'reference': 'Organization/org-1'},
            'identifier': [{'value': 'ID123'}],
            'extension': [
                {
                    'url': 'http://example.com/race',
                    'valueCodeableConcept': {
                        'coding': [{'display': 'White'}]
                    }
                }
            ],
            'communication': [
                {
                    'language': {
                        'coding': [{'code': 'en'}]
                    }
                }
            ],
            'maritalStatus': {
                'coding': [{'code': 'M'}]
            }
        }

        resultado = extrair_campos_patient(registro)

        self.assertEqual(resultado['id'], 'pat-1')
        self.assertEqual(resultado['nome_familia'], 'Silva')
        self.assertEqual(resultado['genero'], 'male')
        self.assertEqual(resultado['data_nascimento'], '1980-01-01')
        self.assertEqual(resultado['organizacao_id'], 'org-1')
        self.assertEqual(resultado['identificador'], 'ID123')
        self.assertEqual(resultado['raca'], 'White')
        self.assertEqual(resultado['idioma'], 'en')
        self.assertEqual(resultado['estado_civil'], 'M')

    def test_extrair_campos_patient_sem_id(self):
        """Testa que ValueError é levantado se 'id' está ausente."""
        registro = {
            'gender': 'female',
            'name': [{'family': 'Santos'}]
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_patient(registro)

        self.assertIn('id', str(contexto.exception))

    def test_extrair_campos_patient_sem_gender(self):
        """Testa que ValueError é levantado se 'gender' está ausente."""
        registro = {
            'id': 'pat-2',
            'name': [{'family': 'Santos'}]
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_patient(registro)

        self.assertIn('gender', str(contexto.exception))

    def test_extrair_campos_patient_sem_name(self):
        """Testa que ValueError é levantado se 'name' está ausente ou vazio."""
        registro = {
            'id': 'pat-3',
            'gender': 'male'
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_patient(registro)

        self.assertIn('name', str(contexto.exception))

    def test_extrair_campos_patient_name_vazio(self):
        """Testa que ValueError é levantado se name.family está vazio."""
        registro = {
            'id': 'pat-4',
            'gender': 'female',
            'name': [{'family': ''}]
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_patient(registro)

        self.assertIn('family', str(contexto.exception).lower())

    def test_extrair_campos_patient_campos_opcionais_none(self):
        """Testa extração com campos opcionais ausentes (devem ser None)."""
        registro = {
            'id': 'pat-5',
            'gender': 'male',
            'name': [{'family': 'Oliveira'}]
        }

        resultado = extrair_campos_patient(registro)

        self.assertEqual(resultado['id'], 'pat-5')
        self.assertEqual(resultado['nome_familia'], 'Oliveira')
        self.assertEqual(resultado['genero'], 'male')
        self.assertIsNone(resultado['data_nascimento'])
        self.assertIsNone(resultado['raca'])
        self.assertIsNone(resultado['identificador'])
        self.assertIsNone(resultado['idioma'])
        self.assertIsNone(resultado['estado_civil'])
        self.assertIsNone(resultado['organizacao_id'])

    def test_extrair_campos_patient_extrai_uuid_org_corretamente(self):
        """Testa que o UUID da organização é extraído corretamente."""
        registro = {
            'id': 'pat-6',
            'gender': 'female',
            'name': [{'family': 'Costa'}],
            'managingOrganization': {
                'reference': 'Organization/org-uuid-12345'
            }
        }

        resultado = extrair_campos_patient(registro)

        self.assertEqual(resultado['organizacao_id'], 'org-uuid-12345')


class TestLerPacientes(unittest.TestCase):
    """Testes para a função ler_pacientes."""

    def test_ler_pacientes_sucesso(self):
        """Testa leitura bem-sucedida de arquivo NDJSON.gz de pacientes."""
        dados = [
            {
                'id': 'pat-1',
                'gender': 'male',
                'name': [{'family': 'Silva'}],
                'managingOrganization': {'reference': 'Organization/org-1'}
            },
            {
                'id': 'pat-2',
                'gender': 'female',
                'name': [{'family': 'Santos'}],
                'managingOrganization': {'reference': 'Organization/org-1'}
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_pacientes(tmp.name)

                self.assertEqual(len(resultado), 2)
                self.assertEqual(resultado[0]['id'], 'pat-1')
                self.assertEqual(resultado[0]['nome_familia'], 'Silva')
                self.assertEqual(resultado[0]['genero'], 'male')
                self.assertEqual(resultado[1]['id'], 'pat-2')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_pacientes_arquivo_nao_encontrado(self):
        """Testa que FileNotFoundError é levantado para arquivo inexistente."""
        with self.assertRaises(FileNotFoundError):
            ler_pacientes('/arquivo/inexistente.gz')

    def test_ler_pacientes_campos_ausentes(self):
        """Testa que registros com campos obrigatórios ausentes são ignorados."""
        dados = [
            {
                'id': 'pat-1',
                'gender': 'male',
                'name': [{'family': 'Silva'}]
            },
            {
                'id': 'pat-2',
                'gender': 'female'
                # sem name
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_pacientes(tmp.name)

                # Apenas o primeiro registro deve estar na lista
                self.assertEqual(len(resultado), 1)
                self.assertEqual(resultado[0]['id'], 'pat-1')

            finally:
                import os
                os.unlink(tmp.name)


class TestExtrairCamposEncounter(unittest.TestCase):
    """Testes para a função extrair_campos_encounter."""

    def test_extrair_campos_encounter_sucesso(self):
        """Testa extração com dict válido contendo campos obrigatórios."""
        registro = {
            'id': 'enc-1',
            'subject': {'reference': 'Patient/pat-1'},
            'type': [{'coding': [{'display': 'Hospitalization'}]}],
            'class': {'code': 'IMP'},
            'period': {'start': '2020-01-01T10:00:00Z', 'end': '2020-01-05T14:00:00Z'},
            'status': 'finished',
            'hospitalization': {'coding': [{'code': 'hosp-code'}]},
            'dischargeDisposition': {'coding': [{'code': 'discharge-code'}]},
            'location': [
                {
                    'location': {'reference': 'Location/loc-1'},
                    'period': {'start': '2020-01-01T10:00:00Z', 'end': '2020-01-03T14:00:00Z'}
                },
                {
                    'location': {'reference': 'Location/loc-2'},
                    'period': {'start': '2020-01-03T15:00:00Z', 'end': '2020-01-05T14:00:00Z'}
                }
            ]
        }

        resultado = extrair_campos_encounter(registro)

        self.assertEqual(resultado['id'], 'enc-1')
        self.assertEqual(resultado['paciente_id'], 'pat-1')
        self.assertEqual(resultado['tipo'], 'Hospitalization')
        self.assertEqual(resultado['classe'], 'IMP')
        self.assertEqual(resultado['periodo_inicio'], '2020-01-01T10:00:00Z')
        self.assertEqual(resultado['periodo_fim'], '2020-01-05T14:00:00Z')
        self.assertEqual(resultado['status'], 'finished')
        self.assertEqual(resultado['hospitalizacao_code'], 'hosp-code')
        self.assertEqual(resultado['alta_code'], 'discharge-code')
        self.assertEqual(len(resultado['localizacoes']), 2)
        self.assertEqual(resultado['localizacoes'][0]['localizacao_id'], 'loc-1')
        self.assertEqual(resultado['localizacoes'][1]['localizacao_id'], 'loc-2')

    def test_extrair_campos_encounter_sem_id(self):
        """Testa que ValueError é levantado se 'id' está ausente."""
        registro = {
            'subject': {'reference': 'Patient/pat-1'}
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_encounter(registro)

        self.assertIn('id', str(contexto.exception))

    def test_extrair_campos_encounter_sem_subject(self):
        """Testa que ValueError é levantado se 'subject' está ausente."""
        registro = {
            'id': 'enc-1'
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_encounter(registro)

        self.assertIn('subject', str(contexto.exception))

    def test_extrair_campos_encounter_subject_reference_vazia(self):
        """Testa que ValueError é levantado se subject.reference está vazia."""
        registro = {
            'id': 'enc-1',
            'subject': {'reference': ''}
        }

        with self.assertRaises(ValueError) as contexto:
            extrair_campos_encounter(registro)

        self.assertIn('reference', str(contexto.exception).lower())

    def test_extrair_campos_encounter_campos_opcionais_none(self):
        """Testa extração com campos opcionais ausentes (devem ser None)."""
        registro = {
            'id': 'enc-2',
            'subject': {'reference': 'Patient/pat-2'}
        }

        resultado = extrair_campos_encounter(registro)

        self.assertEqual(resultado['id'], 'enc-2')
        self.assertEqual(resultado['paciente_id'], 'pat-2')
        self.assertIsNone(resultado['tipo'])
        self.assertIsNone(resultado['classe'])
        self.assertIsNone(resultado['periodo_inicio'])
        self.assertIsNone(resultado['periodo_fim'])
        self.assertIsNone(resultado['status'])
        self.assertIsNone(resultado['hospitalizacao_code'])
        self.assertIsNone(resultado['alta_code'])
        self.assertEqual(len(resultado['localizacoes']), 0)

    def test_extrair_campos_encounter_extrai_uuid_paciente_corretamente(self):
        """Testa que o UUID do paciente é extraído corretamente."""
        registro = {
            'id': 'enc-3',
            'subject': {'reference': 'Patient/patient-uuid-12345'}
        }

        resultado = extrair_campos_encounter(registro)

        self.assertEqual(resultado['paciente_id'], 'patient-uuid-12345')

    def test_extrair_campos_encounter_sem_localizacoes(self):
        """Testa extração sem field location (devem ser lista vazia)."""
        registro = {
            'id': 'enc-4',
            'subject': {'reference': 'Patient/pat-4'}
        }

        resultado = extrair_campos_encounter(registro)

        self.assertEqual(len(resultado['localizacoes']), 0)


class TestLerEncontros(unittest.TestCase):
    """Testes para a função ler_encontros."""

    def test_ler_encontros_sucesso(self):
        """Testa leitura bem-sucedida de arquivo NDJSON.gz de encontros."""
        dados = [
            {
                'id': 'enc-1',
                'subject': {'reference': 'Patient/pat-1'},
                'type': [{'coding': [{'display': 'Hospitalization'}]}],
                'class': {'code': 'IMP'},
                'status': 'finished'
            },
            {
                'id': 'enc-2',
                'subject': {'reference': 'Patient/pat-2'},
                'type': [{'coding': [{'display': 'Outpatient'}]}],
                'class': {'code': 'AMB'},
                'status': 'finished'
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_encontros(tmp.name)

                self.assertEqual(len(resultado), 2)
                self.assertEqual(resultado[0]['id'], 'enc-1')
                self.assertEqual(resultado[0]['paciente_id'], 'pat-1')
                self.assertEqual(resultado[0]['tipo'], 'Hospitalization')
                self.assertEqual(resultado[1]['id'], 'enc-2')

            finally:
                import os
                os.unlink(tmp.name)

    def test_ler_encontros_arquivo_nao_encontrado(self):
        """Testa que FileNotFoundError é levantado para arquivo inexistente."""
        with self.assertRaises(FileNotFoundError):
            ler_encontros('/arquivo/inexistente.gz')

    def test_ler_encontros_campos_ausentes(self):
        """Testa que registros com campos obrigatórios ausentes são ignorados."""
        dados = [
            {
                'id': 'enc-1',
                'subject': {'reference': 'Patient/pat-1'}
            },
            {
                'id': 'enc-2'
                # sem subject
            }
        ]

        with tempfile.NamedTemporaryFile(suffix='.ndjson.gz', delete=False) as tmp:
            with gzip.open(tmp.name, 'wt', encoding='utf-8') as gz:
                for registro in dados:
                    gz.write(json.dumps(registro) + '\n')

            try:
                resultado = ler_encontros(tmp.name)

                # Apenas o primeiro registro deve estar na lista
                self.assertEqual(len(resultado), 1)
                self.assertEqual(resultado[0]['id'], 'enc-1')

            finally:
                import os
                os.unlink(tmp.name)


if __name__ == '__main__':
    unittest.main()
