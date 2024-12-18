import ast
import importlib
import inspect
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import os

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = defaultdict(set)
        self.module_dependencies = defaultdict(set)
        self.current_class = None
        self.current_module = None
        self.imports = {}
        self.from_imports = defaultdict(dict)
        self.star_imports = set()
        self.module_functions = defaultdict(set)


    def analyze_imported_module(self, module_name):
        try:
            module = importlib.import_module(module_name)
            functions = [name for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
            self.module_functions[module_name].update(functions)
        except ImportError:
            print(f"Warning: Could not import module {module_name}")

    def visit_Import(self, node):
        for alias in node.names:
            full_name = alias.name
            self.imports[alias.asname or alias.name] = full_name
            self.analyze_imported_module(full_name)
            self.module_dependencies[self.current_module].add(full_name)

    def visit_ImportFrom(self, node):
        module = node.module
        if node.names[0].name == '*':
            self.star_imports.add(module)
        else:
            for alias in node.names:
                self.from_imports[module][alias.asname or alias.name] = alias.name
                self.module_dependencies[self.current_module].add(module)

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
        if name in self.imports:
            imported_module = self.imports[name]
            if imported_module in self.module_functions and name in self.module_functions[imported_module]:
                return f"{imported_module}.{name}"
            return imported_module
        
        for module, imports in self.from_imports.items():
            if name in imports:
                return f"{module}.{imports[name]}"
        
        for module in self.star_imports:
            return f"{module}.{name}"
        
        return f"{self.current_module}.{name}"

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return self.resolve_name(node.id)
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return ""


def collect_project_objects(project_path):
    project_objects = set()

    class ObjectCollector(ast.NodeVisitor):
        def __init__(self, module_name):
            self.module_name = module_name

        def visit_ClassDef(self, node):
            project_objects.add(f"{self.module_name}.{node.name}")
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            project_objects.add(f"{self.module_name}.{node.name}")
            self.generic_visit(node)

    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                module_name = os.path.splitext(relative_path.replace(os.path.sep, '.'))[0]
                
                # Add the module to project_objects
                project_objects.add(module_name)
                
                with open(file_path, 'r') as f:
                    code = f.read()
                tree = ast.parse(code)
                
                collector = ObjectCollector(module_name)
                collector.visit(tree)

    return project_objects


def analyze_project(project_path):
    visitor = DependencyVisitor()
    project_objects = collect_project_objects(project_path)
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

    # Add the functions from modules imported using 'import module'
    for module, functions in visitor.module_functions.items():
        for func in functions:
            visitor.dependencies[visitor.current_module].add(f"{module}.{func}")

    combined_dependencies = defaultdict(set)
    for module, deps in visitor.dependencies.items():
        combined_dependencies[module].update(deps)
    for module, deps in visitor.module_dependencies.items():
        combined_dependencies[module].update(deps)

    return combined_dependencies, project_objects


def create_reversed_dependency(dependencies, project_objects):
    d = defaultdict(list)
    for k,vals in dependencies.items():
        print("k,vals", k,vals)
        if k in project_objects:
            for v in vals:
                if v in project_objects:
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


def analyze_file_structure(file_path, project_path):
    line_mapping = {}
    current_class = None
    current_function = None

    class Visitor(ast.NodeVisitor):
        def visit(self, node):
            nonlocal current_class, current_function
            relative_path = os.path.relpath(file_path, project_path)
            module_name = os.path.splitext(relative_path.replace(os.path.sep, '.'))[0]

            if isinstance(node, ast.ClassDef):
                current_class = node.name
                current_function = None
                line_mapping[node.lineno] = [f"{module_name}.{node.name}"]
                self.generic_visit(node)
                current_class = None
            elif isinstance(node, ast.FunctionDef):
                current_function = node.name
                if current_class:
                    line_mapping[node.lineno] = [f"{module_name}.{current_class}.{node.name}"]
                else:
                    line_mapping[node.lineno] = [f"{module_name}.{node.name}"]
                self.generic_visit(node)
                current_function = None
            else:
                self.generic_visit(node)
            
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                start = node.lineno
                end = node.end_lineno if node.end_lineno is not None else node.lineno
                for i in range(start, end + 1):
                    if i not in line_mapping:
                        if current_class and current_function:
                            line_mapping[i] = [f"{module_name}.{current_class}.{current_function}"]
                            line_mapping[i].append(f"{module_name}.{current_class}")
                        elif current_class:
                            line_mapping[i] = [f"{module_name}.{current_class}"]
                        elif current_function:
                            line_mapping[i] = [f"{module_name}.{current_function}"]
                        else:
                            line_mapping[i] = [module_name]

    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        Visitor().visit(tree)

    return line_mapping

def get_context_for_line(file_path, project_path, line_number):
    line_mapping = analyze_file_structure(file_path, project_path)
    
    for i in range(line_number, 0, -1):
        if i in line_mapping:
            return line_mapping[i]
    
    return "Not within any module, class or function"


# Usage
project_path = r"MyProjects/TEST"
dependency_graph, project_objects = analyze_project(project_path)
print("dependency_graph", dependency_graph)
print("project_objects", project_objects)
dependencies = create_reversed_dependency(dependency_graph, project_objects)
G = create_dependency_graph(dependencies)
print(dependencies)


filename = r"functions\func.py"
file_path = os.path.join(project_directory, filename)

try:
    line_number = 6
    context = get_context_for_line(file_path, project_directory, line_number)
    print(f"Line {line_number} is in: {context}")
except FileNotFoundError:
    print("File not found. Please check the file path and try again.")

for i in context:
    print(dependencies[i])
