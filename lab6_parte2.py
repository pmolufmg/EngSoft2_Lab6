import git
from collections import defaultdict
import sys
import numpy as np

"""
Engenharia de Software 2 - DCC072 - UFMG
Lab 6 parte 2: Truck Factor 
=========================================

Programa-exemplo para calcular Truck Factor e definir 
os principais autores de sistemas a partir de dados de git log.

---
A solução desenvolvida implementa o seguinte algoritmo:
	
	1. Dado um repositório, coleta-se os dados de todos os commits 
	realizados (git log)
	
	2. Ordena-se commits por data (mais antigo primeiro)
	
	3. Define-se os tipos de arquivos de interesse (código fonte)
	
	4. Associa-se cada arquivo válido modificado aos autores 
	dos respectivos commits, de forma ordenada (criadores primeiro),
	no formato {Arquivo: Lista de autores}. 
	
	OBS: O tamanho da lista de autores indica também o número de vezes em 
	que o arquivo foi modificado. 
	
	5. Calcula-se a autoria, para cada arquivo F e para cada autor Mf (alias, email)
	conforme fórmula: autoria(Mf, F) = C + 0.5 * MD - 0.1 * MO, onde:
		
		4.1. Para o primeiro autor da lista de cada arquivo C = 1;
		para os demais C = 0.
		
		4.2. Seja Nx o número de vezes em que o autor x aparece na lista,
		MDx = Nx, caso o autor não seja o criador e, MDx = Nx - 1, caso seja
		(exclui de MD o evento de criação do arquivo).
		
		4.3. Seja T o número total de modificações do arquivo 
		(não considera o evento de criação), MOx = T - MDx
	
	6. Normaliza-se a lista de valores de autoria de cada arquivo 
	dividindo-se cada valor da lista pelo maior valor.
	
	7. Insere-se, em uma tabela de autoria, para cada autor, seu respectivo 
	valor de autoria(Mf, F) normalizado, sse maior ou igual	ao limite 
	estabelecido de 0.5.
	
	OBS: A tabela resultante de 7 contém, para cada autor, uma lista de valores (>= 0.5)
	de autoria, cujo tamanho indica o número de arquivos fortemente 
	relacionados ao autor.
	
	8. Para cada autor na tabela de autoria, conta-se a quantidade de arquivos 
	fortemente relacionados a ele.
	
		8.1. Se o número de arquivos fortemente relacionados a um autor for maior 
		ou igual à metade do total de arquivos do sistema, incrementa-se o valor de 
		truck factor daquele sistema em 1.
		
	9. Como resultado de 8, tem-se o valor de Truck Factor do sistema.
	
	10. Define-se o grau de importância de cada autor do sistema através da fórmula 
	Ix = MAx * NFx, onde 
		- Ix é a importância do autor x para o sistema, 
		- MAx é a média aritmética de seus valores de autoria normalizados e
		- NFx é o número de arquivos considerados da autoria de x
	
	11. Ordena-se, de modo decrescente, a lista de valores de importância.
	
	12. Apresenta-se os autores relacionados aos N primeiros valores da lista 
	de importância como os N autores mais importantes do sistema, de forma 
	ordenada (a partir do mais importante).

---
Este programa recebe um caminho para repositório (em disco) e produz como saída (sysout):
	- O nome do repositório analisado
	- Uma lista contendo os N autores mais importantes e seus respectivos 'valores de importância'
	- O valor de Truck Factor do sistema

Este código contém o próprio main, onde deverão ser realizadas 
as alterações para teste, e utiliza o módulo gitpython para facilitar
o parsing do git log.

Parâmetros:

:repository_path: caminho para a pasta do repositório (.git)


Uso:

> python lab6_parte2.py <repository_path> 


"""


class TruckFactor:
	def __init__(self, git_log):
		self.treshold = 0.5
		self.ignorable_files = ['json', 'md']
		self.repo = git_log
		self.file_authors = defaultdict(list)
		self.authorship = defaultdict(list)
		self.top_authors = []
		self.commits = self.get_git_log_commits()
		self.tf = 0

	def truck_factor(self):
		self.set_file_authors()
		self.set_degree_of_autorship()
		total_files = len(self.file_authors)
		for author in self.authorship:
			authored_files = len(self.authorship[author])
			coverage = authored_files / total_files
			if coverage >= 0.5:
				self.tf += 1

			importance = coverage * np.mean(self.authorship[author])
			self.top_authors.append((author, importance))

	def set_degree_of_autorship(self):
		for file in self.file_authors:
			authorship = self.file_authors[file]
			doas = []
			devs = []
			counted_set = set()

			lead_dev = authorship[0]
			creator_doa = self.degree_of_autorship(lead_dev, authorship, creator = True)
			counted_set.add(lead_dev)
			doas.append(creator_doa)
			devs.append(lead_dev)

			for author in authorship:
				if author in counted_set:
					continue

				doas.append(self.degree_of_autorship(author, authorship))
				counted_set.add(author)
				devs.append(author)

			normal_doa = self.normalize_doa(doas)
			self.define_valuable_authors(normal_doa, devs)

	def define_valuable_authors(self, normalized_doa, devs):
		doa = normalized_doa
		for ix, dev in enumerate(devs):
			if doa[ix] >= self.treshold:
				self.authorship[dev].append(doa[ix])

	@staticmethod
	def normalize_doa(doa_list):
		max_val = max(doa_list)

		if max_val == 0:
			return doa_list

		normalized = list(map((lambda x: x / max_val), doa_list))

		return normalized

	@staticmethod
	def degree_of_autorship(author, author_list, creator = False):
		num_of_devs = len(author_list) - 1

		if creator:
			c = 1
			md = author_list.count(author) - 1

		else:
			c = 0
			md = author_list.count(author)

		mo = num_of_devs - md

		doa = c + 0.5 * md - 0.1 * mo

		return doa

	def set_file_authors(self):
		for commit in self.commits:
			files = self.valid_files(commit)
			if not files:
				continue

			author = (commit.author.name, commit.author.email)
			if not author:
				continue

			self.associate_elements(files, author)

	def associate_elements(self, files, author):
		for file in files:
			self.file_authors[file].append(author)

	def valid_files(self, commit):
		all_files = list(commit.stats.files.keys())
		valid = []

		for file in all_files:
			if '.' not in file:
				continue

			extension = file.split('.')[-1]

			if extension not in self.ignorable_files:
				valid.append(file)

		return valid

	# Carrega a lista de commits
	def get_git_log_commits(self):
		commits = list(self.repo.iter_commits())

		self.test_commits_list(commits)
		commits.reverse()

		return commits

	@staticmethod
	def test_commits_list(commits):
		if not commits:
			sys.exit('f"No commits found in {self.repo} git log."')
		else:
			return

	def get_truck_factor(self):
		return self.tf

	def get_top_authors(self, num_of_authors = 10):
		sorted_authors = sorted(self.top_authors, key = lambda x: x[-1], reverse = True)
		return sorted_authors[:num_of_authors]


def get_repository_path():
	args = sys.argv
	if len(args) < 2:
		sys.exit('Inform repository path after the script name in command line.')

	repo = sys.argv[1]
	return repo


def get_git_log(repo):
	try:
		rep = git.Repo(repo)
		return rep

	except git.GitError:
		sys.exit('Invalid repository path.')


def get_repository_name(rep_path):
	rep_name = rep_path.split('/')
	folder = rep_name[-1]
	if folder == '':
		folder = rep_name[-2]

	return folder


def get_formatted_authors(aut_list):
	authors = ''
	counter = 0

	for author in aut_list:
		counter += 1
		id = author[0]
		name = id[0]
		if len(id) < 2:
			email = None
		else:
			email = id[-1]
		value = author[-1]

		authors += '{}.\nName: {}\n' \
		           'E-mail: {}\n' \
		           'Computed Author Value: {:.4f}\n\n' \
			.format(counter, name, email, value)

	return authors


def print_results(rep, t_fac, t_authors):
	rep_name = get_repository_name(rep)
	authors = get_formatted_authors(t_authors)

	results = 'Repository: {}\n\n'.format(rep_name)
	results += 'Main Authors:\n{}'.format(authors)
	results += 'Truck Factor = {}\n'.format(t_fac)

	print(results)


if __name__ == "__main__":
	repository = get_repository_path()
	repository_data = get_git_log(repository)
	tf = TruckFactor(repository_data)
	tf.truck_factor()
	tf_val = tf.get_truck_factor()
	main_authors = tf.get_top_authors(10)
	print_results(repository, tf_val, main_authors)
