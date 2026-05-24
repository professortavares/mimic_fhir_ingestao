"""Testes para o módulo leitor."""

import gzip
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from leitor import extrair_campos, ler_registros


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


if __name__ == '__main__':
    unittest.main()
