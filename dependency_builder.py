import ast
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import os

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = defaultdict(set)
        self.current_class = None
        self.current_module = None

    def visit_ClassDef(self, node):
        class_name = f"{self.current_module}.{node.name}"
        self.current_class = class_name
        
        # Add inheritance dependencies
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.dependencies[class_name].add(base.id)
            elif isinstance(base, ast.Attribute):
                self.dependencies[class_name].add(f"{base.value.id}.{base.attr}")

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if not self.current_class:
            self.current_class = f"{self.current_module}.{node.name}"
        self.generic_visit(node)
        if not self.current_class.endswith(node.name):
            self.current_class = None

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if self.current_class:
                self.dependencies[self.current_class].add(func_name)
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if self.current_class:
                self.dependencies[self.current_class].add(func_name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if self.current_class:
                self.dependencies[self.current_class].add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            if self.current_class:
                self.dependencies[self.current_class].add(f"{module}.{alias.name}")
        self.generic_visit(node)

def analyze_project(project_path):
    visitor = DependencyVisitor()
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                module_name = os.path.splitext(relative_path.replace(os.path.sep, '.'))[0]
                
                with open(file_path, 'r') as f:
                    code = f.read()
                tree = ast.parse(code)
                visitor.current_module = module_name
                visitor.visit(tree)
    return visitor.dependencies

def create_reversed_dependency(dependencies):
    d = defaultdict(list)
    for k,vals in dependencies.items():
        for v in vals:
            d[v].append(k)
    return d

def create_dependency_graph(dependencies):
    G = nx.DiGraph()
    
    for source, targets in dependencies.items():
        G.add_node(source)
        for target in targets:
            G.add_node(target)
            G.add_edge(source, target)
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='lightblue', 
            font_size=8, font_weight='bold', arrows=True)
    plt.title('Dependency Graph (including inheritance)')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    return G

# Usage
project_path = r"C:\Users\delsa\Documents\My Projects\TEST"
dependencies = create_reversed_dependency(analyze_project(project_path))
G = create_dependency_graph(dependencies)
print(dependencies)
