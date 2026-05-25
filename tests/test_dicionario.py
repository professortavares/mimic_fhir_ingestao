"""Testes para o módulo dicionario."""

import datetime
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

from dicionario import (
    obter_colunas_tabela,
    obter_chaves_primarias,
    obter_chaves_estrangeiras,
    obter_exemplos_coluna,
    construir_dicionario,
    salvar_dicionario_yaml,
    gerar_dicionario,
    TABELAS,
)


class TestObterColunaTabela(unittest.TestCase):
    """Testes para obter_colunas_tabela."""

    def test_retorna_lista_de_colunas(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('id', 'character varying', 'NO'),
            ('nome', 'text', 'NO'),
        ]

        resultado = obter_colunas_tabela(mock_conexao, 'organizacoes')

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]['nome_coluna'], 'id')
        self.assertEqual(resultado[0]['tipo_dado'], 'character varying')
        self.assertFalse(resultado[0]['nullable'])

    def test_nullable_yes_resulta_em_true(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('coluna_opt', 'text', 'YES'),
        ]

        resultado = obter_colunas_tabela(mock_conexao, 'test')

        self.assertTrue(resultado[0]['nullable'])

    def test_tabela_sem_colunas(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        resultado = obter_colunas_tabela(mock_conexao, 'nonexistent')

        self.assertEqual(resultado, [])

    def test_cursor_execute_chamado_com_tabela_correta(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_colunas_tabela(mock_conexao, 'organizacoes')

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn('information_schema.columns', call_args[0][0])
        self.assertEqual(call_args[0][1], ('organizacoes',))

    def test_cursor_fechado_apos_execucao(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_colunas_tabela(mock_conexao, 'test')

        mock_cursor.close.assert_called_once()


class TestObterChavesPrimarias(unittest.TestCase):
    """Testes para obter_chaves_primarias."""

    def test_retorna_set_de_colunas_pk(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('id',)]

        resultado = obter_chaves_primarias(mock_conexao, 'organizacoes')

        self.assertEqual(resultado, {'id'})

    def test_pk_composta(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('encontro_id',),
            ('localizacao_id',),
        ]

        resultado = obter_chaves_primarias(mock_conexao, 'encontros_localizacoes')

        self.assertEqual(resultado, {'encontro_id', 'localizacao_id'})

    def test_tabela_sem_pk(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        resultado = obter_chaves_primarias(mock_conexao, 'test')

        self.assertEqual(resultado, set())

    def test_cursor_execute_com_constraint_type_pk(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_chaves_primarias(mock_conexao, 'test')

        call_args = mock_cursor.execute.call_args[0][0]
        self.assertIn('PRIMARY KEY', call_args)

    def test_cursor_fechado(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_chaves_primarias(mock_conexao, 'test')

        mock_cursor.close.assert_called_once()


class TestObterChavesEstrangeiras(unittest.TestCase):
    """Testes para obter_chaves_estrangeiras."""

    def test_retorna_dict_de_fks(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('organizacao_id', 'organizacoes'),
        ]

        resultado = obter_chaves_estrangeiras(mock_conexao, 'localizacoes')

        self.assertEqual(resultado, {'organizacao_id': 'organizacoes'})

    def test_multiplas_fks(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('paciente_id', 'pacientes'),
            ('encontro_id', 'encontros'),
        ]

        resultado = obter_chaves_estrangeiras(mock_conexao, 'condicoes')

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado['paciente_id'], 'pacientes')
        self.assertEqual(resultado['encontro_id'], 'encontros')

    def test_sem_fks(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        resultado = obter_chaves_estrangeiras(mock_conexao, 'organizacoes')

        self.assertEqual(resultado, {})

    def test_cursor_execute_com_constraint_type_fk(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_chaves_estrangeiras(mock_conexao, 'test')

        call_args = mock_cursor.execute.call_args[0][0]
        self.assertIn('FOREIGN KEY', call_args)

    def test_cursor_fechado(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_chaves_estrangeiras(mock_conexao, 'test')

        mock_cursor.close.assert_called_once()


class TestObterExemplosColuna(unittest.TestCase):
    """Testes para obter_exemplos_coluna."""

    def test_retorna_ate_tres_exemplos(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('val1',),
            ('val2',),
            ('val3',),
        ]

        resultado = obter_exemplos_coluna(mock_conexao, 'test', 'col')

        self.assertEqual(resultado, ['val1', 'val2', 'val3'])

    def test_tabela_vazia_retorna_lista_vazia(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        resultado = obter_exemplos_coluna(mock_conexao, 'empty', 'col')

        self.assertEqual(resultado, [])

    def test_converte_datetime_para_string_iso(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        dt = datetime.datetime(2180, 6, 27, 10, 0)
        mock_cursor.fetchall.return_value = [(dt,)]

        resultado = obter_exemplos_coluna(mock_conexao, 'test', 'col')

        self.assertEqual(resultado, ['2180-06-27T10:00:00'])

    def test_converte_date_para_string_iso(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        d = datetime.date(1945, 3, 21)
        mock_cursor.fetchall.return_value = [(d,)]

        resultado = obter_exemplos_coluna(mock_conexao, 'test', 'col')

        self.assertEqual(resultado, ['1945-03-21'])

    def test_valores_string_sem_conversao(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('hello',)]

        resultado = obter_exemplos_coluna(mock_conexao, 'test', 'col')

        self.assertEqual(resultado, ['hello'])

    def test_cursor_fechado(self):
        mock_cursor = MagicMock()
        mock_conexao = MagicMock()
        mock_conexao.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        obter_exemplos_coluna(mock_conexao, 'test', 'col')

        mock_cursor.close.assert_called_once()


class TestConstruirDicionario(unittest.TestCase):
    """Testes para construir_dicionario."""

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
        {'nome_coluna': 'nome', 'tipo_dado': 'text', 'nullable': False},
    ])
    def test_retorna_dict_com_chave_tabelas(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        self.assertIn('tabelas', resultado)

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
    ])
    def test_numero_correto_de_tabelas(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        self.assertEqual(len(resultado['tabelas']), len(TABELAS))

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
    ])
    def test_estrutura_de_tabela_tem_chaves_obrigatorias(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        tabela = resultado['tabelas'][0]
        self.assertIn('nome', tabela)
        self.assertIn('descricao', tabela)
        self.assertIn('colunas', tabela)

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
    ])
    def test_estrutura_de_coluna_tem_todas_as_chaves(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        coluna = resultado['tabelas'][0]['colunas'][0]
        self.assertIn('nome', coluna)
        self.assertIn('descricao', coluna)
        self.assertIn('tipo', coluna)
        self.assertIn('obrigatorio', coluna)
        self.assertIn('chave_primaria', coluna)
        self.assertIn('chave_estrangeira', coluna)
        self.assertIn('exemplos', coluna)

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
    ])
    def test_coluna_pk_marcada_corretamente(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        coluna = resultado['tabelas'][0]['colunas'][0]
        self.assertTrue(coluna['chave_primaria'])

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={'organizacao_id': 'organizacoes'})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
        {'nome_coluna': 'organizacao_id', 'tipo_dado': 'character varying', 'nullable': True},
    ])
    def test_coluna_fk_marcada_corretamente(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        coluna_fk = resultado['tabelas'][0]['colunas'][1]
        self.assertEqual(coluna_fk['chave_estrangeira'], 'organizacoes')

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'id', 'tipo_dado': 'character varying', 'nullable': False},
    ])
    def test_coluna_sem_fk_tem_null(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        coluna = resultado['tabelas'][0]['colunas'][0]
        self.assertIsNone(coluna['chave_estrangeira'])

    @patch('dicionario.obter_exemplos_coluna', return_value=[])
    @patch('dicionario.obter_chaves_estrangeiras', return_value={})
    @patch('dicionario.obter_chaves_primarias', return_value={'id'})
    @patch('dicionario.obter_colunas_tabela', return_value=[
        {'nome_coluna': 'nome', 'tipo_dado': 'text', 'nullable': True},
    ])
    def test_obrigatorio_false_quando_nullable(self, mock_cols, mock_pks, mock_fks, mock_exs):
        mock_conexao = MagicMock()
        resultado = construir_dicionario(mock_conexao)

        coluna = resultado['tabelas'][0]['colunas'][0]
        self.assertFalse(coluna['obrigatorio'])


class TestSalvarDicionarioYaml(unittest.TestCase):
    """Testes para salvar_dicionario_yaml."""

    def test_cria_arquivo_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, 'test.yaml')
            dicionario = {'tabelas': []}

            salvar_dicionario_yaml(dicionario, caminho)

            self.assertTrue(os.path.exists(caminho))

    def test_conteudo_yaml_valido(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, 'test.yaml')
            dicionario = {
                'tabelas': [
                    {'nome': 'test', 'descricao': 'desc', 'colunas': []}
                ]
            }

            salvar_dicionario_yaml(dicionario, caminho)

            import yaml
            with open(caminho, 'r', encoding='utf-8') as f:
                lido = yaml.safe_load(f)
            self.assertEqual(lido['tabelas'][0]['nome'], 'test')

    def test_cria_diretorio_se_nao_existir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, 'subdir', 'outro', 'test.yaml')
            dicionario = {'tabelas': []}

            salvar_dicionario_yaml(dicionario, caminho)

            self.assertTrue(os.path.exists(caminho))

    def test_unicode_preservado(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, 'test.yaml')
            dicionario = {
                'tabelas': [
                    {'nome': 'test', 'descricao': 'Organizações', 'colunas': []}
                ]
            }

            salvar_dicionario_yaml(dicionario, caminho)

            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            self.assertIn('Organizações', conteudo)

    def test_lista_vazia_de_exemplos_serializada(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = os.path.join(tmpdir, 'test.yaml')
            dicionario = {
                'tabelas': [
                    {
                        'nome': 'test',
                        'descricao': 'desc',
                        'colunas': [
                            {
                                'nome': 'col',
                                'descricao': 'd',
                                'tipo': 't',
                                'obrigatorio': True,
                                'chave_primaria': False,
                                'chave_estrangeira': None,
                                'exemplos': [],
                            }
                        ]
                    }
                ]
            }

            salvar_dicionario_yaml(dicionario, caminho)

            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            self.assertIn('exemplos: []', conteudo)


class TestGerarDicionario(unittest.TestCase):
    """Testes para gerar_dicionario."""

    @patch('dicionario.salvar_dicionario_yaml')
    @patch('dicionario.construir_dicionario')
    def test_chama_construir_e_salvar(self, mock_construir, mock_salvar):
        mock_conexao = MagicMock()
        mock_construir.return_value = {'tabelas': []}

        gerar_dicionario(mock_conexao)

        mock_construir.assert_called_once_with(mock_conexao)
        mock_salvar.assert_called_once()

    @patch('dicionario.salvar_dicionario_yaml')
    @patch('dicionario.construir_dicionario')
    def test_usa_caminho_padrao(self, mock_construir, mock_salvar):
        mock_conexao = MagicMock()
        mock_construir.return_value = {'tabelas': []}

        gerar_dicionario(mock_conexao)

        call_args = mock_salvar.call_args
        self.assertEqual(call_args[0][1], './dic/dicionario_dados.yaml')

    @patch('dicionario.salvar_dicionario_yaml')
    @patch('dicionario.construir_dicionario')
    def test_usa_caminho_customizado(self, mock_construir, mock_salvar):
        mock_conexao = MagicMock()
        mock_construir.return_value = {'tabelas': []}

        gerar_dicionario(mock_conexao, '/custom/path.yaml')

        call_args = mock_salvar.call_args
        self.assertEqual(call_args[0][1], '/custom/path.yaml')

    @patch('dicionario.construir_dicionario')
    def test_propaga_excecao_do_banco(self, mock_construir):
        mock_conexao = MagicMock()
        mock_construir.side_effect = Exception('DB error')

        with self.assertRaises(Exception) as ctx:
            gerar_dicionario(mock_conexao)

        self.assertEqual(str(ctx.exception), 'DB error')

    @patch('dicionario.salvar_dicionario_yaml')
    @patch('dicionario.construir_dicionario')
    def test_propaga_excecao_de_io(self, mock_construir, mock_salvar):
        mock_conexao = MagicMock()
        mock_construir.return_value = {'tabelas': []}
        mock_salvar.side_effect = OSError('No permission')

        with self.assertRaises(OSError) as ctx:
            gerar_dicionario(mock_conexao)

        self.assertEqual(str(ctx.exception), 'No permission')


if __name__ == '__main__':
    unittest.main()
