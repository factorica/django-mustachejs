from django import template

from ..conf import conf
from ..loading import find, MustacheJSTemplateNotFound

register = template.Library()

class MustacheJSNode(template.Node):
    """
    Locates the appropriate template, normalises it, and writes it to the output.

    Prelude and Postlude contain text that should be written before
    and after the actual mustache template.
    """
    preamble ='<script id="{prefix}-{name}" name="{name}" type="text/x-mustache-template">\n'
    postamble =  '\n</script>'

    def __init__(self, name, preamble=None, postamble=None, fixup=False):
        self.name = template.Variable(name)
        if preamble:
            self.preamble = preamble
        if postamble:
            self.postamble = postamble

        self.fixup = fixup

    def render(self, context):
        name = self.name.resolve(context)
        try:
            filepath = find(name)

            with open(filepath, "r") as fp:
                output = fp.read().decode(conf.FILE_CHARSET)

            # fixup special characters to allow them to be embedded in JavaScript strings.
            # Note necessary if it's embedded as a type="text/x-mustache-template"
            if self.fixup:
                output = output.replace('\\', r'\\')
                output = output.replace('\n', r'\n')
                output = output.replace("'", r"\'")

            data = {
                'prefix' : "mustache",
                'name'   :  name
            }
            output = self.preamble.format(**data) + output + self.postamble.format(**data)

        except (IOError, MustacheJSTemplateNotFound):
            output = ""
            if conf.DEBUG:
                raise

        return output


@register.tag
def mustachejs(parser, token):
    """
    Finds the MustacheJS template for the given name and renders it surrounded by
    the requisite MustacheJS <script> tags.
    """
    preamble = "<script>Mustache.TEMPLATES=Mustache.TEMPLATES||{{}}; Mustache.TEMPLATES['{name}']='"
    postamble = "';</script>"

    bits = token.contents.split()
    if len(bits) not in [2, 3]:
        raise template.TemplateSyntaxError(
            "'mustachejs' tag takes one argument: the name/id of the template")
    return MustacheJSNode(bits[1], preamble, postamble, fixup=True)


@register.tag
def mustache_include(parser, token):
    bits = token.contents.split()
    if len(bits) not in [2, 3]:
        raise template.TemplateSyntaxError(
            "'mustache_include' tag takes one argument: the name/id of the template")
    return MustacheJSNode(bits[1])

@register.tag
def mustache_raw(parser, token):
    if len(bits) not in [2, 3]:
        raise template.TemplateSyntaxError(
            "'mustache_include' tag takes one argument: the name/id of the template")
    return MustacheJSNode(bits[1], preamble="", postamble="")


@register.tag
def mustache_inline(parser, token):
    # TODO: Get inline mustache working...
    pass

@register.tag
def mustache_render(parser, token):
    pass
