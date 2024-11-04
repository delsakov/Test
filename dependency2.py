import ast
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import os

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = defaultdict(set)
        self.current_class = None
        self.current_module = None
        self.imports = {}
        self.from_imports = defaultdict(dict)
        self.star_imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name

    def visit_ImportFrom(self, node):
        module = node.module
        if node.names[0].name == '*':
            self.star_imports.add(module)
        else:
            for alias in node.names:
                self.from_imports[module][alias.asname or alias.name] = alias.name

    def visit_ClassDef(self, node):
        class_name = f"{self.current_module}.{node.name}"
        self.current_class = class_name
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                full_base_name = self.resolve_name(base_name)
                self.dependencies[class_name].add(full_base_name)
            elif isinstance(base, ast.Attribute):
                full_base_name = self.get_full_name(base)
                self.dependencies[class_name].add(full_base_name)

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if not self.current_class:
            self.current_class = f"{self.current_module}.{node.name}"
        self.generic_visit(node)
        if not self.current_class.endswith(node.name):
            self.current_class = None

    def visit_Call(self, node):
        if self.current_class:
            if isinstance(node.func, ast.Name):
                func_name = self.resolve_name(node.func.id)
                self.dependencies[self.current_class].add(func_name)
            elif isinstance(node.func, ast.Attribute):
                func_name = self.get_full_name(node.func)
                self.dependencies[self.current_class].add(func_name)
        self.generic_visit(node)

    def resolve_name(self, name):
        # Check regular imports
        if name in self.imports:
            return self.imports[name]
        
        # Check from imports
        for module, imports in self.from_imports.items():
            if name in imports:
                return f"{module}.{imports[name]}"
        
        # Check star imports
        for module in self.star_imports:
            # Assume the name exists in the star-imported module
            return f"{module}.{name}"
        
        # If not found in imports, assume it's in the current module
        return f"{self.current_module}.{name}"

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return self.resolve_name(node.id)
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return ""

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
                visitor.imports.clear()
                visitor.from_imports.clear()
                visitor.star_imports.clear()
                visitor.visit(tree)
    return visitor.dependencies


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
