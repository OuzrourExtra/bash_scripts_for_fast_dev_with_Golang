import os
import sys
import subprocess
import shutil

GO_ROOT = r"D:\Go"

def list_projects():
    projects = [f for f in os.listdir(GO_ROOT) if os.path.isdir(os.path.join(GO_ROOT, f))]
    projects.sort()
    print("Select a project to open (number):")
    for idx, name in enumerate(projects, 1):
        print(f"{idx}. {name}")
    print("0. Exit")
    try:
        choice = int(input("Your choice: "))
        if choice == 0:
            print("Exit.")
            sys.exit(0)
        elif 1 <= choice <= len(projects):
            return projects[choice-1]
        else:
            print("Invalid choice.")
            sys.exit(1)
    except Exception as e:
        print("Invalid input.", e)
        sys.exit(1)

def run_tool(tool_name, args_list, cwd=None):
    exe_path = shutil.which(tool_name)
    if not exe_path:
        print(f"Error: '{tool_name}' not found in your PATH.")
        return False
    try:
        subprocess.run([exe_path] + args_list, cwd=cwd, check=True)
        return True
    except Exception as e:
        print(f"Error running {tool_name}:", e)
        return False

def main():
    args = sys.argv[1:]
    project_name = None
    desc = None

    # Simple argument parsing
    if "-l" in args or len(args) == 0:
        project_name = list_projects()
    else:
        for i, arg in enumerate(args):
            if arg == "--desc" and i+1 < len(args):
                desc = args[i+1]
            elif not arg.startswith("-") and project_name is None:
                project_name = arg

    if not project_name:
        print("No project specified.")
        sys.exit(1)

    project_path = os.path.join(GO_ROOT, project_name)

    # If project exists, just open in VSCode
    if os.path.exists(project_path) and os.path.isdir(project_path):
        print(f"Project exists: {project_path}")
    else:
        # Create it and run goc with desc if present
        os.makedirs(project_path, exist_ok=True)
        print(f"Created project: {project_path}")
        goc_args = []
        if desc:
            goc_args += ["--desc", desc]
        run_tool("goc", goc_args, cwd=project_path)

    # Open VS Code using robust PATH search
    if not run_tool("code", [project_path]):
        print("Could not open VS Code! Please check your PATH.")

if __name__ == "__main__":
    main()
