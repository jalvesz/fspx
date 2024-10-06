import os
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util import logging
from sphinx import addnodes  
from .fortran_parser import parse_fortran_file

logger = logging.getLogger(__name__)

class AutoFortranDirective(Directive):
    """
    A Sphinx directive to automatically document Fortran APIs with docstrings,
    subroutines, functions, and types styled similarly to Python.
    """
    has_content = True
    required_arguments = 1  # The path to the Fortran file
    
    def run(self):
        env = self.state.document.settings.env
        file_path = self.arguments[0]
        
        if not os.path.isabs(file_path):
            file_path = os.path.join(env.srcdir, file_path)

        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist")
            return []
        
        fortran_data = parse_fortran_file(file_path)
        
        section_node = nodes.section(ids=['fortran-api'])
        section_node += nodes.title(text="Fortran API Documentation")

        # Document modules
        if fortran_data['modules']:
            section_node += nodes.subtitle(text="Modules")
            for mod in fortran_data['modules']:
                section_node += self.create_signature("module", mod['name'], mod['doc'])

        # Document subroutines
        if fortran_data['subroutines']:
            section_node += nodes.subtitle(text="Subroutines")
            for subroutine in fortran_data['subroutines']:
                section_node += self.create_signature("subroutine", subroutine['name'], subroutine['doc'], subroutine['args'])

        # Document functions
        if fortran_data['functions']:
            section_node += nodes.subtitle(text="Functions")
            for func in fortran_data['functions']:
                section_node += self.create_signature("function", func['name'], func['doc'], func['args'])

        # Document derived types
        if fortran_data['types']:
            section_node += nodes.subtitle(text="Derived Types")
            for derived_type in fortran_data['types']:
                section_node += self.create_signature("type", derived_type['name'], derived_type['doc'])

        return [section_node]

    def create_signature(self, element_type, name, docstring=None, args=None):
        """
        Create a styled signature for subroutines, functions, and types, mimicking Python def/class styles.
        The arguments will be listed with their attributes inline.
        """
        # Create the description node using Sphinx-specific addnodes
        desc = addnodes.desc()
        
        # Signature (header)
        sig = addnodes.desc_signature('', '')
        sig += addnodes.desc_name(text=f"{element_type} {name}")
        
        # If arguments are present (for subroutines/functions), display them
        if args:
            params = addnodes.desc_parameterlist()
            for arg_name in args.keys():
                param = addnodes.desc_parameter(text=f"{arg_name}")
                params += param
            sig += params
        
        desc += sig

        # Content (body)
        if docstring or args:
            content = addnodes.desc_content()

            # Add the docstring as the body content if present
            if docstring:
                content += nodes.paragraph(text=docstring)

            # Add argument descriptions and attributes in the same line
            if args:
                arg_list = nodes.definition_list()
                for arg_name, arg_info in args.items():
                    # Argument name followed by attributes in the same line
                    term = nodes.term(text=f"{arg_name}: {arg_info['attributes']}")
                    # Argument description
                    definition = nodes.definition(text=arg_info['description'] or "No description provided.")
                    # Combine the term (arg_name + attributes) and definition (description)
                    item = nodes.definition_list_item('', term, definition)
                    arg_list += item
                content += arg_list

            desc += content

        return desc
