## Define mini-templates for each portion of the doco.
<%
    import inspect
    import re
    import textwrap
    from pdoc.html_helpers import _ToMarkdown

    def google(text):
        def googledoc_sections(match):
            section, body = match.groups('')
            if not body:
                return match.group()
            body = textwrap.dedent(body)
            section = section.title()
            if section in ('Args', 'Attributes', 'Returns', 'Yields', 'Raises', 'Warns'):
                body = re.compile(
                    r'^([\w*]+)(?: \(([\w.,=\[\] ]+)\))?: '
                    r'((?:.*)(?:\n(?: {2,}.*|$))*)', re.MULTILINE).sub(
                    lambda m: _ToMarkdown._deflist(*_ToMarkdown._fix_indent(*m.groups())),
                    inspect.cleandoc('\n' + body)
                )
            return '\n#### {}\n\n{}'.format(section, body)

        text = re.compile(r'^([A-Z]\w+):$\n'
                        r'((?:\n?(?: {2,}.*|$))+)', re.MULTILINE).sub(googledoc_sections, text)
        return text


    def to_markdown(text, docformat='numpy,google'):
        assert all(i in (None, '', 'numpy', 'google') for i in docformat.split(',')), docformat

        text = _ToMarkdown.admonitions(text, module)

        if 'google' in docformat:
            text = google(text)

        text = _ToMarkdown.doctests(text)
        text = _ToMarkdown.raw_urls(text)

        if 'numpy' in docformat:
            text = _ToMarkdown.numpy(text)

        if module and link:
            text = _code_refs(partial(_linkify, link=link, module=module, wrap_code=True), text)

        return text
%>


<%!
  def indent(s, spaces=4):
      new = s.replace('\n', '\n' + ' ' * spaces)
      return ' ' * spaces + new.strip()
%>

<%def name="deflist(s)">:${indent(s)[1:]}</%def>


<%def name="h1(s)"># ${s}</%def>
<%def name="h2(s)">## ${s}</%def>
<%def name="h3(s)">### ${s}</%def>
<%def name="h4(s)">#### ${s}</%def>

<%def name="function(func)" buffered="True">
<%
    returns = show_type_annotations and func.return_annotation() or ''
    if returns:
        returns = ' -> ' + returns

    params = [x.replace("{}", "{ }") for x in func.params(annotate=show_type_annotations)]
%>
${h3("`method " + func.name + "(" + ", ".join(params) + ")" + returns + "`")}

${func.docstring | to_markdown}
</%def>

<%def name="variable(var)" buffered="True">
`${var.name}`
${var.docstring | deflist}
</%def>

<%def name="class_(cls)" buffered="True">
${h2("`class " + cls.name + "(" + ", ".join(cls.params(annotate=show_type_annotations)) + ")`")}

${cls.docstring}
<%
  class_vars = cls.class_variables(show_inherited_members, sort=sort_identifiers)
  static_methods = cls.functions(show_inherited_members, sort=sort_identifiers)
  inst_vars = cls.instance_variables(show_inherited_members, sort=sort_identifiers)
  methods = cls.methods(show_inherited_members, sort=sort_identifiers)
  mro = cls.mro()
  subclasses = cls.subclasses()
%>
% if mro:
${h3('Ancestors (in MRO)')}

% for c in mro:
* ${c.refname}
% endfor

% endif
% if subclasses:
${h3('Descendants')}

% for c in subclasses:
* ${c.refname}
% endfor

% endif
% if class_vars:
${h3('Class variables')}
% for v in class_vars:
${variable(v)}

% endfor
% endif
% if static_methods:
${h3('Static methods')}
% for f in static_methods:
${function(f)}

% endfor
% endif
% if inst_vars:
${h3('Instance variables')}
% for v in inst_vars:
${variable(v)}

% endfor
% endif
% if methods:
% for m in methods:
${function(m)}

% endfor
% endif
</%def>

## Start the output logic for an entire module.

<%
  variables = module.variables()
  classes = module.classes()
  functions = module.functions()
  submodules = module.submodules()
  heading = 'Namespace' if module.is_namespace else 'Module'
%>

---
title: ${module.name}
geekdocRepo: False
---

${module.docstring}

{{< toc >}}

% if submodules:
${h2("Sub-modules")}

% for m in submodules:
* ${m.name}
% endfor
% endif

% if variables:
${h2("Variables")}

% for v in variables:
${variable(v)}

% endfor
% endif

% if functions:
${h2("Functions")}

% for f in functions:
${function(f)}

% endfor
% endif

% if classes:
% for c in classes:
${class_(c)}

% endfor
% endif
