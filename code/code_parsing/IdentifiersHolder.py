from scipy.sparse import csr_matrix


class IdentifiersHolder(object):

    def __init__(self, people, variables, imports):
        self.imports = csr_matrix((len(people), len(imports)))
        self.variables = csr_matrix((len(people), len(variables)))
    # TODO Как в самом начале определить, сколько людей, сколько переменных, сколько импортов?
    # Делать два прогона?