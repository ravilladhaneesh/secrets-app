from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FormField, FieldList, EmailField
from wtforms.validators import DataRequired



class AddNomineeForm(FlaskForm):
    class Meta:
        csrf = False
    name = StringField('Nominee Name', validators=[DataRequired()])
    email_id = EmailField('Email', validators=[DataRequired()])        
    

class AddSecretsForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    secret = StringField("Secret", validators=[DataRequired()])
    nominees = FieldList(FormField(AddNomineeForm), min_entries=0)
    submit = SubmitField("Submit")
