from flask_wtf import FlaskForm
from secrets_app.model import User
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FormField, FieldList, EmailField
from wtforms.validators import InputRequired, DataRequired, Length, EqualTo, Email, ValidationError

class UserRegistrationForm(FlaskForm):
    firstName = StringField('First Name', validators=[DataRequired(), Length(min=3, max=15)])
    lastName = StringField('Last Name')
    password = PasswordField('New Password', [InputRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password  = PasswordField('Confirm Password')
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError( f'Email {email.data} already exists! Please use a different email.')
    
    def validate_password(self, password):
        special_char = ["@", "$", "%", "&"]
        lower_chars = [chr(i) for i in range(97, 123)]
        upper_chars = [chr(i) for i in range(65, 91)]
        digits = [chr(i) for i in range(48, 58)]

        valid = {'has_special_char': False, 'has_lower_char': False, 'has_upper_char': False, 'has_digit': False}
        for i in password.data:
            if i in special_char:
                valid['has_special_char'] = True
            elif i in lower_chars:
                valid['has_lower_char'] = True
            elif i in upper_chars:
                valid['has_upper_char'] = True
            elif i in digits:
                valid['has_digit'] = True
            
            if all(valid.values()):
                break
        print("--->",valid)
        if not all(valid.values()):
                raise ValidationError("Password should be atleast 8 char long and have atleast 1 lower char, 1 upper char, 1 special char and 1 digit")


class UserLoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class UserUpdateForm(FlaskForm):
    firstName = StringField("firstName", validators=[DataRequired()])
    lastName = StringField("lastName")
    required_login_per_days = IntegerField("Login Required Date", validators=[DataRequired()])
    submit = SubmitField("Update")

    def validate_required_login_per_days(self, required_login_per_days):
        if not (5 <= required_login_per_days.data <= 30) :
            raise ValidationError("Login Required Date should be greater than 5 days and less than 30 days")
        

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


class EmailVerificationForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    otp = StringField('otp', validators=[DataRequired()])
    submit = SubmitField('verify', validators=[DataRequired()])
