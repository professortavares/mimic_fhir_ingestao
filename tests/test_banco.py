"""Testes para o módulo banco."""

import unittest
from unittest.mock import MagicMock, patch, call
from banco import conectar, criar_tabela, inserir_organizacoes


class TestConectar(unittest.TestCase):
    """Testes para a função conectar."""

    @patch('banco.psycopg2.connect')
    def test_conectar_sucesso(self, mock_connect):
        """Testa conexão bem-sucedida."""
        mock_conexao = MagicMock()
        mock_connect.return_value = mock_conexao

        config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'mimic_fhir',
            'user': 'postgres',
            'password': 'postgres'
        }

        resultado = conectar(config)

        self.assertEqual(resultado, mock_conexao)
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            database='mimic_fhir',
            user='postgres',
            password='postgres'
        )

    @patch('banco.psycopg2.connect')
    def test_conectar_falha(self, mock_connect):
        """Testa falha na conexão."""
        import psycopg2
        mock_connect.side_effect = psycopg2.Error("Erro de conexão")

        config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'mimic_fhir',
            'user': 'postgres',
            'password': 'postgres'
        }

        with self.assertRaises(Exception):
            conectar(config)


class TestCriarTabela(unittest.TestCase):
    """Testes para a função criar_tabela."""

    def test_criar_tabela_sucesso(self):
        """Testa criação de tabela com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        criar_tabela(mock_conexao)

        mock_cursor.execute.assert_called_once()
        # Verifica se o SQL contém as partes esperadas
        sql_chamada = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS organizacoes', sql_chamada)
        self.assertIn('id VARCHAR(255) PRIMARY KEY', sql_chamada)
        self.assertIn('nome TEXT NOT NULL', sql_chamada)

        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestInserirOrganizacoes(unittest.TestCase):
    """Testes para a função inserir_organizacoes."""

    def test_inserir_organizacoes_sucesso(self):
        """Testa inserção de registros com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1  # Simula que uma linha foi inserida

        registros = [
            {'id': '123', 'nome': 'Organização A'},
            {'id': '456', 'nome': 'Organização B'}
        ]

        resultado = inserir_organizacoes(mock_conexao, registros)

        self.assertEqual(resultado, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_inserir_organizacoes_vazio(self):
        """Testa inserção com lista vazia."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        resultado = inserir_organizacoes(mock_conexao, [])

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
