import os
import re
import subprocess
import sys
from argparse import ArgumentParser
from colorama import Fore, Style, init

init(autoreset=True)

GITHUB_PREFIX = "github.com/ouzrourextra/"

def color(s, c):
    return f"{c}{s}{Style.RESET_ALL}"

def is_valid_name(name):
    return re.match(r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$', name)

def has_git():
    from shutil import which
    return which("git") is not None

def get_current_folder_name():
    return os.path.basename(os.getcwd())

def update_makefile_with_main():
    if not os.path.exists("Makefile"):
        with open("Makefile", "w") as f:
            f.write(f"""build:
\tgo build -o main.exe

run:
\tgo run main.go

test:
\tgo test ./...

fmt:
\tgo fmt ./...
""")

def add_submodule_to_readme(submod, description=None):
    line = f"- `{submod}`"
    if description:
        line += f": {description}"
    line += "\n"
    content = ""
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        if "## Submodules" not in content:
            content += "\n## Submodules\n"
        lines = content.splitlines()
        # Remove existing line for the submodule
        lines = [l for l in lines if not l.lstrip().startswith(f"- `{submod}`")]
        content = "\n".join(lines)
        if not content.endswith("\n"):
            content += "\n"
        content += line
    else:
        content = f"# Submodules\n\n{line}"
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

def get_root_modpath():
    """Parse go.mod in root if exists and return module path, else construct from cwd."""
    if os.path.exists("go.mod"):
        with open("go.mod", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("module "):
                    return line.strip().split()[1]
    # Fallback: construct from cwd
    root = get_current_folder_name()
    return GITHUB_PREFIX + root

def create_go_project(name, use_git=True, description="Auto-generated Go project."):
    if not is_valid_name(name):
        print(color("❌ Invalid project name. Use only letters, numbers, _, - or . ; must start with a letter.", Fore.RED))
        return

    if os.path.exists("main.go"):
        print(color(f"⚠️  main.go already exists in this folder. Aborting.", Fore.YELLOW))
        return

    module_name = GITHUB_PREFIX + name

    print(color(f"📦 Creating Go project in: {os.getcwd()} (module: {module_name})", Fore.CYAN))
    with open("main.go", "w") as f:
        f.write(f'''package main

import "fmt"

func main() {{
    fmt.Println("Welcome to {name}!")
}}
''')

    subprocess.run(["go", "mod", "init", module_name], check=True)

    with open(".gitignore", "w") as f:
        f.write("""
# Go build
*.exe
*.out
*.test

# IDE
.vscode/
.idea/

# Vendor
/vendor/
""")

    with open("README.md", "w") as f:
        f.write(f"# {name}\n\n{description}\n")

    update_makefile_with_main()

    if use_git:
        if has_git():
            subprocess.run(["git", "init"])
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", "Initial commit"])
            print(color("✔️  Git repository initialized.", Fore.GREEN))
        else:
            print(color("⚠️  Git not found. Skipping git init.", Fore.YELLOW))
    else:
        print(color("ℹ️  Skipped Git initialization.", Fore.YELLOW))

    print(color("✅ Done! Your Go project is ready.", Fore.GREEN))

def import_submodule_in_main(subfolder, root_modpath):
    main_path = "main.go"
    module_import = f'"{root_modpath}/{subfolder}"'
    if not os.path.exists(main_path):
        print(color("⚠️  main.go not found; cannot import submodule.", Fore.YELLOW))
        return
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    if module_import in content:
        print(color(f"ℹ️  Submodule '{subfolder}' already imported in main.go.", Fore.YELLOW))
        return

    if 'import (\n' in content:
        content = re.sub(
            r'(import\s+\((?:.|\n)*?)(\))',
            lambda m: m.group(1) + f'\t{module_import}\n' + m.group(2) if module_import not in m.group(0) else m.group(0),
            content,
            count=1
        )
    elif re.search(r'import\s+"fmt"', content):
        content = re.sub(
            r'import\s+"fmt"',
            f'import (\n\t"fmt"\n\t{module_import}\n)',
            content,
            count=1
        )
    else:
        content = re.sub(
            r'(package main\s*)',
            r'\1\nimport (\n\t"fmt"\n\t' + module_import + '\n)\n',
            content,
            count=1
        )

    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(color(f"➕ Imported '{subfolder}' in main.go!", Fore.CYAN))

def create_go_submodule(subfolder, description=None):
    if not is_valid_name(subfolder):
        print(color("❌ Invalid subfolder/module name.", Fore.RED))
        return

    if not os.path.exists(subfolder):
        os.makedirs(subfolder)
    else:
        print(color(f"⚠️  Subfolder '{subfolder}' already exists.", Fore.YELLOW))

    root_modpath = get_root_modpath()
    sub_modpath = root_modpath + "/" + subfolder

    gofile = os.path.join(subfolder, f"{subfolder}.go")
    if not os.path.exists(gofile):
        with open(gofile, "w") as f:
            f.write(f'''package {subfolder}

''')
    os.chdir(subfolder)
    subprocess.run(["go", "mod", "init", sub_modpath], check=True)
    os.chdir("..")

    update_makefile_with_main()
    add_submodule_to_readme(subfolder, description)

    # Always try to import in main.go if present, with correct path
    import_submodule_in_main(subfolder, root_modpath)

    print(color(f"✅ Submodule '{subfolder}' created and registered!", Fore.GREEN))

def main():
    parser = ArgumentParser(
        description="Create a new Go project or Go submodule quickly."
    )
    parser.add_argument(
        "name", nargs="?", default=None,
        help="Project or submodule name (leave empty to use current folder as project)"
    )
    parser.add_argument(
        "--no-git", action="store_true",
        help="Do NOT initialize a git repository (main project only)"
    )
    parser.add_argument(
        "--desc", type=str, default=None,
        help="Project or submodule description for README"
    )

    args = parser.parse_args()
    if args.name is None:
        name = get_current_folder_name()
        desc = args.desc if args.desc else "Auto-generated Go project."
        create_go_project(
            name=name,
            use_git=not args.no_git,
            description=desc
        )
    else:
        create_go_submodule(args.name, description=args.desc)

if __name__ == "__main__":
    main()
