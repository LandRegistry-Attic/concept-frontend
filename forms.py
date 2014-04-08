from wtforms import Form, BooleanField, TextField, RadioField, HiddenField, TextAreaField, validators

class SearchForm(Form):
    q = TextField('Search', [validators.Required()])
