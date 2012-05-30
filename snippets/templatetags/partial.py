from django.template import Library, Variable, Node
from django.template.loader import get_template
from django.template import TemplateSyntaxError
import settings

register = Library()

"""
Combines 'with' and 'include' to something useful:

For example: 
  {% partial "table_list.html" hot as urls and 1 as listid and "Hot items" as title %}

Will include the "table_list.html" file -- using the same include rules a django
and have the 'listid', 'urls', and 'title' variables set in the include context.
"""

class PartialNode(Node):
    def __init__(self, path, is_constant, params):
        self.params = params
        self.tmpl   = None
        self.vtmpl  = None

        if is_constant :
            try :
                self.tmpl = get_template(path)
            except : 
                if settings.TEMPLATE_DEBUG :
                    raise
        else :
            self.vtmpl = Variable(path)
    
    def render(self, context):
        tmpl = None

        if self.tmpl :
            tmpl = self.tmpl
        elif self.vtmpl :
            try :
                t = self.vtmpl.resolve(context)
                tmpl = get_template(t)
            except TemplateSyntaxError, e :
                if settings.TEMPLATE_DEBUG :
                    raise
                return ''
            except :
                return ''   # Fail silently for invalid included templates.

        if not tmpl :
            return ''

        update = {}
        for k, v in self.params.items() :
            val = v.resolve(context)
            #print "V = ", v, val
            update[k] = val

        context.push()
        context.update(update)
        output = tmpl.render(context)
        context.pop()
        return output

def render_partial(parser, token):
    params = {}

    bits = token.split_contents()
    if len(bits) < 2 :
        raise TemplateSyntaxError("%r tag takes at least one argument: the name of the template to be included" % bits[0])
    try:
        path = bits[1]

        state = 0
        val   = None
        idx   = 2
        if len(bits) > 2 and bits[2] != 'with':
            raise TemplateSyntaxError("%r syntax error TEMPLATE with NAME as VALUE and NAME as VALUE ...." % bits[0])
        for p in bits[3:] :
            if state == 0 :
                val = p
                state += 1
            elif state == 1 :
                if p.lower() != 'as' :
                    raise TemplateSyntaxError("%r expected format is 'value as name'" % bits[0])
                state += 1
            elif state == 2 :
                params[p] = Variable(val)
                state += 1
            elif state == 3 :
                if p.lower() != 'and' :
                    raise TemplateSyntaxError("%r expected format is 'value as name and'" % bits[0])
                state = 0 
            
    except ValueError:
        raise template.TemplateSyntaxError, '%r tag requires at least a single argument and no spaces in name:value list' % parts[0]

    if path[0] in ('"', "'") and path[0] == path[-1] :
        return PartialNode(path[1:-1], True, params)
    return PartialNode(path, False, params)

render_partial = register.tag('partial', render_partial)
