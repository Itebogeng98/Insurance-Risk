from django import forms


def add_bootstrap_classes(form: forms.BaseForm) -> None:
    for field in form.fields.values():
        is_checkbox = isinstance(field.widget, forms.CheckboxInput)
        css_class = 'form-check-input' if is_checkbox else 'form-control'
        existing = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f'{existing} {css_class}'.strip()
        if not is_checkbox:
            field.widget.attrs.setdefault('placeholder', field.label or '')
