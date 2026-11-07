"""Repository inventory scope; private agent state is not public project content."""
import os


def walk_public_tree(root='.'):
    for directory, directories, files in os.walk(root):
        relative = os.path.relpath(directory, root)
        directories[:] = [name for name in directories
                          if name not in {'.git', '__pycache__'}
                          and not (relative == 'agent_system' and name == 'local')]
        yield directory, directories, files
