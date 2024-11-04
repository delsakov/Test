import ast
from collections import defaultdict
import os

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = defaultdict(set)
        self.current_class = None
        self.current_module = None
        self.imports = {}

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.name] = alias.name

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            self.imports[alias.name] = f"{module}.{alias.name}"

    def visit_ClassDef(self, node):
        class_name = f"{self.current_module}.{node.name}"
        self.current_class = class_name
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                # Check if the base class is imported
                if base_name in self.imports:
                    full_base_name = self.imports[base_name]
                else:
                    # Assume it's in the same module if not imported
                    full_base_name = f"{self.current_module}.{base_name}"
                self.dependencies[class_name].add(full_base_name)
            elif isinstance(base, ast.Attribute):
                # Handle cases like module.ClassName
                full_base_name = self.get_full_name(base)
                self.dependencies[class_name].add(full_base_name)

        self.generic_visit(node)
        self.current_class = None

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return ""

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
                visitor.imports.clear()  # Clear imports for each new file
                visitor.visit(tree)
    return visitor.dependencies

# Usage
project_path = r"/MyProjects/TEST"
dependencies = create_reversed_dependency(analyze_project(project_path))
G = create_dependency_graph(dependencies)
print(dependencies)
