from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FormField, FieldList, EmailField, ValidationError, BooleanField, TextAreaField
from wtforms.validators import DataRequired



class AddReceiverForm(FlaskForm):
    class Meta:
        csrf = False
    name = StringField('Receiver Name', validators=[DataRequired()])
    email_id = EmailField('Email', validators=[DataRequired()]) 

    def validate_email_id(self, email_id):
        if '@' not in email_id.data:
            raise ValidationError(f"Invalid email address: {email_id.data}")

class AddNoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    to_self = BooleanField("Self", default=True)
    receivers = FieldList(FormField(AddReceiverForm), min_entries=0)
    submit = SubmitField("Submit")

    def validate_receivers(self, receivers):
        emails = set()
        for receiver in receivers:
            if receiver.email_id.data in emails:
                raise ValidationError(f"Duplicate email found: {receiver.email_id.data}")
            emails.add(receiver.email_id.data)
    
    def validate(self, extra_validators=None):
        
        rv = super().validate()

        if not rv:
            return False
        
        if self.to_self.data and len(self.receivers.entries) > 0:
            self.receivers.errors.append("Self is checked, so no receivers should be added")
            return False

        return True