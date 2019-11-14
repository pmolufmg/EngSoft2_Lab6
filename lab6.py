import git
import sys
import pandas as pd
from itertools import combinations

"""
Engenharia de Software 2 - DCC072 - UFMG
Lab 6: Acoplamento Lógico
=========================================

Programa-exemplo para detectar acoplamento lógico de sistemas
a partir de dados git log.

A solução desenvolvida se baseia na identificação dos arquivos 
alterados em cada commit por meior da geração de pares (combinação 2 a 2) 
e na contagem destes pares com a finalidade de identificar aqueles 
que são mais comumente alterados em conjunto.

Como saída é produzida uma tabela ordenada de forma decrescente 
através da qual é possível observar o número de commits onde
ocorreu a alteração conjunta de cada par.

Esta tabela pode ser gravada em um arquivo csv através da função
save_table_to_csv_file.

Este código contém o próprio main, onde deverão ser realizadas 
as alterações para teste, e utiliza o módulo gitpython para facilitar
o parsing do git log.

Parâmetros:

:repository_path: caminho para a pasta do repositório (.git)
:ascending: define a ordem de apresentação das instâncias na tabela 
(False -> decrescente)


"""


class LogicalCoupling:

	def __init__(self, repository_path, ascending = False):

		# Carrega dados do repositorio
		self.repo = git.Repo(repository_path)

		self.commits = self.get_git_log_commits()
		self.order = ascending
		self.pairs = []
		self.dataframe = pd.DataFrame()
		self.count_changed_file_pairs_by_commit()

	# Carrega a lista de commits
	def get_git_log_commits(self):
		commits = [commit for commit in self.repo.iter_commits()]

		self.test_commits_list(commits)

		return commits

	# Conta o numero de ocorrência de cada par e monta o DataFrame
	def count_changed_file_pairs_by_commit(self):
		for commit in self.commits:
			files = self.sorted_valid_files_list(commit)

			if not files:
				continue

			self.set_file_pairs_combination(files)

		counted_pair_set = self.count_pairs()

		self.set_data_frame(counted_pair_set)

	# Ordena os arquivos para evitar instancias duplicadas na combinacao
	def sorted_valid_files_list(self, commit):
		files = sorted(list(commit.stats.files.keys()))

		return self.valid_files(files)

	# Realiza combinacao 2 a 2 dos arquivos da lista para
	# produzir a associacao de todos os pares alterados
	def set_file_pairs_combination(self, file_list):
		files = file_list
		total_files = len(files)

		if total_files > 1:
			self.pairs += list(combinations(files, 2))

		elif total_files == 1:
			self.pairs.append((files[0], None))

	# Conta o numero de ocorrencia de cada par de arquivos associados
	# nos mesmos commits
	def count_pairs(self):
		pair_set = set()
		counted = []

		for pair in self.pairs:
			if pair not in counted:
				counted.append(pair)
				changes = self.pairs.count(pair)
				pair_set.add((pair[0], pair[1], changes))

		return pair_set if pair_set else False

	# Monta e ordena o DataFrame pandas
	def set_data_frame(self, counted_pair_set):
		pair_set = counted_pair_set
		df = pd.DataFrame(list(pair_set), columns = ['File1', 'File2', 'Changes'])
		self.dataframe = df.sort_values(by = ['Changes'], ascending = self.order)
		self.dataframe.set_index('File1', inplace = True)

	# Avalia se existem commits no log do repositorio
	@staticmethod
	def test_commits_list(commits):
		if not commits:
			sys.exit('f"No commits found in {self.repo} git log."')
		else:
			return

	# Valida formatos de arquivos para limpar os dados gerados pelo parser
	@staticmethod
	def valid_files(file_list):
		files = file_list
		invalid_files = []

		for file in files:
			if '.' not in file:
				invalid_files.append(file)

		if invalid_files:
			for invalid in invalid_files:
				files.remove(invalid)

		if not files:
			return False

		return file_list

	def print_table(self):
		print(self.dataframe)

	def save_table_to_csv_file(self, file_path):
		with open(file_path, 'w') as file:
			self.dataframe.to_csv(file)


if __name__ == "__main__":
	# Path para o repositorio a ser analisado
	my_repo = '.'

	# Nome do arquivo onde deverá ser gravada a tabela
	csv_file = 'lab6.csv'

	lc = LogicalCoupling(my_repo, ascending = False)
	lc.print_table()

	# Para nao produzir arquivo, comente a proxima linha
	lc.save_table_to_csv_file(csv_file)
