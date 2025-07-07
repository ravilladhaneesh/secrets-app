from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FormField, FieldList, EmailField, ValidationError
from wtforms.validators import DataRequired



class AddNomineeForm(FlaskForm):
    class Meta:
        csrf = False
    name = StringField('Nominee Name', validators=[DataRequired()])
    email_id = EmailField('Email', validators=[DataRequired()]) 

    def validate_email_id(self, email_id):
        if '@' not in email_id.data:
            raise ValidationError(f"Invalid email address: {email_id.data}")      
    

class AddSecretsForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    secret = StringField("Secret", validators=[DataRequired()])
    nominees = FieldList(FormField(AddNomineeForm), min_entries=0)
    submit = SubmitField("Submit")

    def validate_nominees(self, nominees):
        emails = set()
        for nominee in nominees:
            if nominee.email_id.data in emails:
                raise ValidationError(f"Duplicate email found: {nominee.email_id.data}")
            emails.add(nominee.email_id.data)
    

