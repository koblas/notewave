from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import StrAndUnicode, smart_unicode, force_unicode
from django.forms.util import ErrorList

register = template.Library()

def divfield(bf, tooltip=None) :
    error_row = u'%s'
    help_text_html = u' %s'
    errors_on_separate_row = False
    label_suffix = ':'
    field = bf.field

    error_class = ErrorList

    def _gen_normal(**kwargs) :
        parts = [ u'<div%(html_class_attr)s>' % kwargs ]
        if tooltip :
            parts.append('<div rel="formtip" class="tip_right">%s</div>' % tooltip)
        parts.append(u'%(label)s%(errors)s<div>%(field)s</div>' % kwargs)
        if kwargs['help_text'] :
            parts.append('<div><small>%s</small></div>' % kwargs['help_text'])
        parts.append('</div>')
        return ''.join(parts)

    html_class_attr = ''

    bf_errors = error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
    if bf.is_hidden:
        if bf_errors:
            top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
        hidden_fields.append(unicode(bf))
    else:
        # Create a 'class="..."' atribute if the row should have any
        # CSS classes applied.
        css_classes = bf.css_classes()
        if bf_errors :
            css_classes += ' errors'
        if css_classes:
            html_class_attr = ' class="%s"' % css_classes

        if errors_on_separate_row and bf_errors:
            output.append(error_row % force_unicode(bf_errors))

        if bf.label:
            label = conditional_escape(force_unicode(bf.label))
            # Only add the suffix if the label does not end in
            # punctuation.
            if label_suffix:
                if label[-1] not in ':?.!':
                    label += label_suffix
            label = bf.label_tag(label) or ''
        else:
            label = ''

        if field.help_text:
            help_text = help_text_html % force_unicode(field.help_text)
        else:
            help_text = u''

    return mark_safe(_gen_normal(errors=force_unicode(bf_errors),
                                 label= force_unicode(label),
                                 field= unicode(bf),
                                 help_text= help_text,
                                 html_class_attr= html_class_attr))

register.filter(divfield)
