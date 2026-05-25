"""Testes para o módulo banco."""

import unittest
from unittest.mock import MagicMock, patch, call
from banco import (
    conectar,
    criar_tabela,
    inserir_organizacoes,
    criar_tabela_localizacoes,
    inserir_localizacoes,
    criar_tabela_pacientes,
    inserir_pacientes,
    criar_tabela_encontros,
    inserir_encontros,
    criar_tabela_encontros_localizacoes,
    inserir_encontros_localizacoes
)


class TestConectar(unittest.TestCase):
    """Testes para a função conectar."""

    @patch('banco.psycopg2.connect')
    def test_conectar_sucesso(self, mock_connect):
        """Testa conexão bem-sucedida."""
        mock_conexao = MagicMock()
        mock_connect.return_value = mock_conexao

        test_credential = 'test_password_fixture'  # noqa: S105
        config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'mimic_fhir',
            'user': 'postgres',
            'password': test_credential
        }

        resultado = conectar(config)

        self.assertEqual(resultado, mock_conexao)
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            database='mimic_fhir',
            user='postgres',
            password=test_credential
        )

    @patch('banco.psycopg2.connect')
    def test_conectar_falha(self, mock_connect):
        """Testa falha na conexão."""
        import psycopg2
        mock_connect.side_effect = psycopg2.Error("Erro de conexão")

        test_credential = 'test_password_fixture'  # noqa: S105
        config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'mimic_fhir',
            'user': 'postgres',
            'password': test_credential
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


class TestCriarTabelaLocalizacoes(unittest.TestCase):
    """Testes para a função criar_tabela_localizacoes."""

    def test_criar_tabela_localizacoes_sucesso(self):
        """Testa criação de tabela localizacoes com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        criar_tabela_localizacoes(mock_conexao)

        mock_cursor.execute.assert_called_once()
        # Verifica se o SQL contém as partes esperadas
        sql_chamada = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS localizacoes', sql_chamada)
        self.assertIn('id VARCHAR(255) PRIMARY KEY', sql_chamada)
        self.assertIn('nome TEXT NOT NULL', sql_chamada)
        self.assertIn('organizacao_id VARCHAR(255) REFERENCES organizacoes(id)', sql_chamada)

        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestInserirLocalizacoes(unittest.TestCase):
    """Testes para a função inserir_localizacoes."""

    def test_inserir_localizacoes_sucesso(self):
        """Testa inserção de registros de localizações com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        registros = [
            {
                'id': 'loc-1',
                'nome': 'Localização A',
                'organizacao_id': 'org-1'
            },
            {
                'id': 'loc-2',
                'nome': 'Localização B',
                'organizacao_id': 'org-1'
            }
        ]

        resultado = inserir_localizacoes(mock_conexao, registros)

        self.assertEqual(resultado, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_inserir_localizacoes_vazio(self):
        """Testa inserção com lista vazia."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        resultado = inserir_localizacoes(mock_conexao, [])

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()

    def test_inserir_localizacoes_com_fk(self):
        """Testa que FK é incluída no INSERT."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        registros = [
            {
                'id': 'loc-uuid',
                'nome': 'Test Location',
                'organizacao_id': 'org-uuid'
            }
        ]

        inserir_localizacoes(mock_conexao, registros)

        # Verifica que execute foi chamado com 3 valores (id, nome, organizacao_id)
        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(call_args[1], ('loc-uuid', 'Test Location', 'org-uuid'))


class TestCriarTabelaPacientes(unittest.TestCase):
    """Testes para a função criar_tabela_pacientes."""

    def test_criar_tabela_pacientes_sucesso(self):
        """Testa criação de tabela pacientes com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        criar_tabela_pacientes(mock_conexao)

        mock_cursor.execute.assert_called_once()
        # Verifica se o SQL contém as partes esperadas
        sql_chamada = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS pacientes', sql_chamada)
        self.assertIn('id VARCHAR(255) PRIMARY KEY', sql_chamada)
        self.assertIn('nome_familia TEXT NOT NULL', sql_chamada)
        self.assertIn('genero VARCHAR(50)', sql_chamada)
        self.assertIn('data_nascimento DATE', sql_chamada)
        self.assertIn('raca TEXT', sql_chamada)
        self.assertIn('identificador VARCHAR(255)', sql_chamada)
        self.assertIn('idioma VARCHAR(10)', sql_chamada)
        self.assertIn('estado_civil VARCHAR(50)', sql_chamada)
        self.assertIn('organizacao_id VARCHAR(255) REFERENCES organizacoes(id)', sql_chamada)

        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestInserirPacientes(unittest.TestCase):
    """Testes para a função inserir_pacientes."""

    def test_inserir_pacientes_sucesso(self):
        """Testa inserção de registros de pacientes com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        registros = [
            {
                'id': 'pat-1',
                'nome_familia': 'Silva',
                'genero': 'male',
                'data_nascimento': '1980-01-01',
                'raca': 'White',
                'identificador': 'ID123',
                'idioma': 'en',
                'estado_civil': 'M',
                'organizacao_id': 'org-1'
            },
            {
                'id': 'pat-2',
                'nome_familia': 'Santos',
                'genero': 'female',
                'data_nascimento': '1985-05-15',
                'raca': 'Black',
                'identificador': 'ID456',
                'idioma': 'pt',
                'estado_civil': 'S',
                'organizacao_id': 'org-1'
            }
        ]

        resultado = inserir_pacientes(mock_conexao, registros)

        self.assertEqual(resultado, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_inserir_pacientes_vazio(self):
        """Testa inserção com lista vazia."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        resultado = inserir_pacientes(mock_conexao, [])

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()

    def test_inserir_pacientes_com_fk(self):
        """Testa que FK é incluída no INSERT."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        registros = [
            {
                'id': 'pat-uuid',
                'nome_familia': 'Test',
                'genero': 'male',
                'data_nascimento': '1990-01-01',
                'raca': None,
                'identificador': None,
                'idioma': None,
                'estado_civil': None,
                'organizacao_id': 'org-uuid'
            }
        ]

        inserir_pacientes(mock_conexao, registros)

        # Verifica que execute foi chamado com 9 valores
        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(
            call_args[1],
            ('pat-uuid', 'Test', 'male', '1990-01-01', None, None, None, None, 'org-uuid')
        )


class TestCriarTabelaEncontros(unittest.TestCase):
    """Testes para a função criar_tabela_encontros."""

    def test_criar_tabela_encontros_sucesso(self):
        """Testa criação de tabela encontros com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        criar_tabela_encontros(mock_conexao)

        mock_cursor.execute.assert_called_once()
        sql_chamada = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS encontros', sql_chamada)
        self.assertIn('id VARCHAR(255) PRIMARY KEY', sql_chamada)
        self.assertIn('tipo TEXT', sql_chamada)
        self.assertIn('classe VARCHAR(50)', sql_chamada)
        self.assertIn('periodo_inicio TIMESTAMP', sql_chamada)
        self.assertIn('periodo_fim TIMESTAMP', sql_chamada)
        self.assertIn('status VARCHAR(50)', sql_chamada)
        self.assertIn('hospitalizacao_code VARCHAR(50)', sql_chamada)
        self.assertIn('alta_code VARCHAR(50)', sql_chamada)
        self.assertIn('paciente_id VARCHAR(255) REFERENCES pacientes(id)', sql_chamada)

        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestInserirEncontros(unittest.TestCase):
    """Testes para a função inserir_encontros."""

    def test_inserir_encontros_sucesso(self):
        """Testa inserção de registros de encontros com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        registros = [
            {
                'id': 'enc-1',
                'tipo': 'Hospitalization',
                'classe': 'IMP',
                'periodo_inicio': '2020-01-01T10:00:00Z',
                'periodo_fim': '2020-01-05T14:00:00Z',
                'status': 'finished',
                'hospitalizacao_code': 'hosp-code',
                'alta_code': 'discharge-code',
                'paciente_id': 'pat-1',
                'localizacoes': []
            },
            {
                'id': 'enc-2',
                'tipo': 'Outpatient',
                'classe': 'AMB',
                'periodo_inicio': '2020-02-01T09:00:00Z',
                'periodo_fim': '2020-02-01T11:00:00Z',
                'status': 'finished',
                'hospitalizacao_code': None,
                'alta_code': None,
                'paciente_id': 'pat-2',
                'localizacoes': []
            }
        ]

        resultado = inserir_encontros(mock_conexao, registros)

        self.assertEqual(resultado, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_inserir_encontros_vazio(self):
        """Testa inserção com lista vazia."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        resultado = inserir_encontros(mock_conexao, [])

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()

    def test_inserir_encontros_com_fk(self):
        """Testa que FK é incluída no INSERT."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        registros = [
            {
                'id': 'enc-uuid',
                'tipo': 'Hospitalization',
                'classe': 'IMP',
                'periodo_inicio': '2020-01-01T10:00:00Z',
                'periodo_fim': '2020-01-05T14:00:00Z',
                'status': 'finished',
                'hospitalizacao_code': 'code',
                'alta_code': 'discharge',
                'paciente_id': 'pat-uuid',
                'localizacoes': []
            }
        ]

        inserir_encontros(mock_conexao, registros)

        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(
            call_args[1],
            (
                'enc-uuid',
                'Hospitalization',
                'IMP',
                '2020-01-01T10:00:00Z',
                '2020-01-05T14:00:00Z',
                'finished',
                'code',
                'discharge',
                'pat-uuid'
            )
        )


class TestCriarTabelaEncontrosLocalizacoes(unittest.TestCase):
    """Testes para a função criar_tabela_encontros_localizacoes."""

    def test_criar_tabela_encontros_localizacoes_sucesso(self):
        """Testa criação de tabela encontros_localizacoes com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        criar_tabela_encontros_localizacoes(mock_conexao)

        mock_cursor.execute.assert_called_once()
        sql_chamada = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS encontros_localizacoes', sql_chamada)
        self.assertIn('encontro_id VARCHAR(255) REFERENCES encontros(id)', sql_chamada)
        self.assertIn('localizacao_id VARCHAR(255) REFERENCES localizacoes(id)', sql_chamada)
        self.assertIn('periodo_inicio TIMESTAMP', sql_chamada)
        self.assertIn('periodo_fim TIMESTAMP', sql_chamada)
        self.assertIn('PRIMARY KEY (encontro_id, localizacao_id)', sql_chamada)

        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestInserirEncontrosLocalizacoes(unittest.TestCase):
    """Testes para a função inserir_encontros_localizacoes."""

    def test_inserir_encontros_localizacoes_sucesso(self):
        """Testa inserção de relacionamentos encontro-localização com sucesso."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        encontros = [
            {
                'id': 'enc-1',
                'localizacoes': [
                    {
                        'localizacao_id': 'loc-1',
                        'periodo_inicio': '2020-01-01T10:00:00Z',
                        'periodo_fim': '2020-01-03T14:00:00Z'
                    },
                    {
                        'localizacao_id': 'loc-2',
                        'periodo_inicio': '2020-01-03T15:00:00Z',
                        'periodo_fim': '2020-01-05T14:00:00Z'
                    }
                ]
            }
        ]

        resultado = inserir_encontros_localizacoes(mock_conexao, encontros)

        self.assertEqual(resultado, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conexao.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_inserir_encontros_localizacoes_vazio(self):
        """Testa inserção com lista vazia de encontros."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        resultado = inserir_encontros_localizacoes(mock_conexao, [])

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()

    def test_inserir_encontros_localizacoes_sem_locations(self):
        """Testa inserção com encontro sem localizações."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        encontros = [
            {
                'id': 'enc-1',
                'localizacoes': []
            }
        ]

        resultado = inserir_encontros_localizacoes(mock_conexao, encontros)

        self.assertEqual(resultado, 0)
        mock_cursor.execute.assert_not_called()
        mock_conexao.commit.assert_called_once()

    def test_inserir_encontros_localizacoes_com_fks(self):
        """Testa que FKs são incluídas no INSERT."""
        mock_conexao = MagicMock()
        mock_cursor = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor

        encontros = [
            {
                'id': 'enc-uuid',
                'localizacoes': [
                    {
                        'localizacao_id': 'loc-uuid',
                        'periodo_inicio': '2020-01-01T10:00:00Z',
                        'periodo_fim': '2020-01-03T14:00:00Z'
                    }
                ]
            }
        ]

        inserir_encontros_localizacoes(mock_conexao, encontros)

        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(
            call_args[1],
            ('enc-uuid', 'loc-uuid', '2020-01-01T10:00:00Z', '2020-01-03T14:00:00Z')
        )


if __name__ == '__main__':
    unittest.main()
