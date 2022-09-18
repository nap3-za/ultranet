
from django import forms
from .models import Question, Feedback, Report

class QuestionCreationForm(forms.ModelForm):

	class Meta:
		model = Question
		fields = ('question',)
    
	def clean(self):
		question = self.cleaned_data['question']
		if len(question.replace(" ",""))<=3:
			raise forms.ValidationError("Your question is too small")

class FeedbackCreationForm(forms.ModelForm):

	class Meta:
		model = Feedback
		fields = ('content',)
    
	def clean(self):
		question = self.cleaned_data['feedback']
		if len(question.replace(" ",""))<=3:
			raise forms.ValidationError("Your feedback is too small")

obj_choices = [
	'Account',
	'Content',
	'Comment',
]
reasons = [
	'Contains sensetive/inappropriate content',
	'Racist',
	'False facts',
	'default',
	# ...
]
class ReportCreationForm(forms.ModelForm):

	class Meta:
		model = Report
		fields = ('obj','obj_id', 'reason')
    
	def clean(self):
		obj = self.cleaned_data.get('obj')
		if not obj in obj_choices:
			raise forms.ValidationError("Invalid data , please do not alter the form")
		reason = self.cleaned_data.get('reason')
		if not reason in reasons:
			raise forms.ValidationError("Invalid data , please do not alter the form")

	def save(self, user):
		report = None
		try:
			obj_type = self.cleaned_data.get('obj')
			obj_id = self.cleaned_data.get('obj_id')
			reason = self.cleaned_data.get('reason')
			report = Report.objects.create(
				repotee=user,
				reason=reason,
				obj=obj_type,
				obj_id=obj_id
				)
			report.save()
		except:
			pass
		return report




