from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User
from flask_ckeditor import CKEditorField


class RegistrationForm(FlaskForm):
	username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
	email = StringField('Email',validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('That username is taken. Please choose a different one.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
	email = StringField('Email',validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

class EventForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	content =  CKEditorField('Enter Notes:', validators=[DataRequired()])
	link = StringField('Link', validators=[DataRequired()])
	submit = SubmitField('Add Event')

class EditForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	content = CKEditorField('Enter Notes:', validators=[DataRequired()])
	submit = SubmitField('Edit Event')

# Create A Search Form
class SearchForm(FlaskForm):
	searched = StringField("Search", validators=[DataRequired()])
	submit = SubmitField("Submit")

class StudentForm(FlaskForm):
	name = StringField('Name', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	year = StringField('Year', validators=[DataRequired()])
	submit = SubmitField('Add Student')

class UploadForm(FlaskForm):
	name = FileField('File')
	submit = SubmitField("Submit")