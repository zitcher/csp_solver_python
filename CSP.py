import numpy as np

# CSP GRAPH MODEL
# node dictionary of dim k [c_1][c_2] .... [c_k] -> list of domain
# edge dictionary of dim d [c_1][c_2] .... [c_k] -> tuple list of (connected nodes, boolean function on node vals)


class cspSolver(object):
    """
        A generic CSP solver for problems with finite domain
        nodes: dictionary of dimension k (node[(c_1, ..., c_k)]) -> list of domain
        edges: dictionary of dimension k (node[(c_1, ..., c_k)]) ->
                Tuple of tuples of connected between node (tuple rep) and boolean constraint function
                ( ((c_1, ..., c_k), lambda x, y: x != y), ... )
    """
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def ac3(self):
        assert(self.nodes.keys() == self.edges.keys())
        # actually a set but called queue by tradition
        queue = {((node, edge[0]), edge[1]) for node in self.nodes.keys() for edge in self.edges[node]}

        return queue

    def revise(self, constraint, node, edge):
        domain = self.nodes[node]
        pass


nodes = dict()
edges = dict()
nodes[(1, 1)] = [1, 2]
nodes[(2, 2)] = [2]
edges[(1, 1)] = (((2, 2), lambda x, y: x != y),)
edges[(2, 2)] = (((1, 1), lambda x, y: x != y),)
csp = cspSolver(nodes, edges)
print(csp.ac3())
