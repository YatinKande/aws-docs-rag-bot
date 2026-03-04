import ast
import os
import sys
import importlib

def run_audit():
    broken = []
    imports = set()
    
    # 1. Syntax Audit
    for root, dirs, files in os.walk('backend'):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.venv']]
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file:
                        content = file.read()
                        tree = ast.parse(content)
                        # Collect imports for Step 2
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for n in node.names:
                                    imports.add(n.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                except SyntaxError as e:
                    broken.append(f"{path}: {e}")
                except Exception as e:
                    print(f"Error reading {path}: {e}")

    print("--- SYNTAX ERRORS ---")
    for b in broken:
        print(b)
    print(f"Total syntax errors: {len(broken)}")

    # 2. Dependency Audit
    print("\n--- MISSING DEPENDENCIES ---")
    missing = []
    # Add project root to path for local imports
    sys.path.insert(0, os.getcwd())
    
    for imp in sorted(imports):
        if imp == 'backend': continue # self reference
        try:
            importlib.import_module(imp)
        except ImportError:
            missing.append(imp)
        except Exception as e:
            # Some modules might fail on import due to env, but they are "present"
            pass
            
    for m in missing:
        print(f"  - {m}")
    print(f"Total missing dependencies: {len(missing)}")

if __name__ == "__main__":
    run_audit()
