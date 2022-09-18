from django import forms 
from .models import Choice, Comment, Content
from account.models import Account as BaseAccount





visibility_options_list = [
	'Friends',
	'Anyone',
]

visibility_options = [
	('Friends', 'Friends'),
	('Anyone', 'Anyone'),
]

types = [
	('Post', 'Post'),
	('Poll', 'Poll'),
	('Snippet', 'Snippet'),
]


class ContentCreationForm(forms.ModelForm):


	class Meta:
		model = Content
		fields = ('title', 'text', 'visibility', 'draft', 'tags')

	def clean(self):
		title = self.cleaned_data["title"]
		if title and len(title.replace(" ","")) <= 2:
			raise form.ValidationError("The title of your post is too small")

		visibility = self.cleaned_data["visibility"]
		if not visibility in visibility_options_list:
			raise forms.ValidationError("Please select a valid visibility option")

		draft = self.cleaned_data["draft"]
		if draft != True and draft != False:
			raise forms.ValidationError("Please check the draft checkbox or leave it unchecked")

		content_type = self.data["content_type"]
		if content_type!="Post" and content_type!="Poll":
			raise forms.ValidationError("Please do not alter the form or you will be banned from this platform")

		text = self.cleaned_data["text"]
		if content_type=="Post" and len(text.replace(' ','')) <= 2:
			raise forms.ValidationError("Your post content is too small")

		if content_type=="Poll" and len(text.replace('\r','').split('\n')) <= 1:
			raise forms.ValidationError("Poll choices should be 2 or more")

	def save(self, user, commit=True):
		content = Content.objects.create_content(
			author=user,
			text=self.cleaned_data["text"],
			content_type=self.data["content_type"],
			draft=self.cleaned_data["draft"],
			visibility=self.cleaned_data["visibility"],
			title=self.cleaned_data["title"],
			tags=[],
		)
		if commit:
			content.save()
		return content

class ContentUpdateForm(forms.ModelForm):

	class Meta:
		model = Content
		fields = ('title', 'text', 'visibility', 'draft', 'tags')

	def clean(self):
		title = self.cleaned_data["title"]
		if title and len(title.replace(" ","")) <= 2:
			raise form.ValidationError("The title of your post is too small")


		visibility = self.cleaned_data["visibility"]
		if not visibility in visibility_options_list:
			raise forms.ValidationError("Please select a valid visibility option")

		content_type = self.data["content_type"]
		if content_type!="Post" and content_type!="Poll":
			raise forms.ValidationError("Please do not alter the form or you will be banned from this platform")

		text = self.cleaned_data["text"]
		if content_type=="Post" and len(text.replace(' ','')) <= 2:
			raise forms.ValidationError("Your post content is too small")

		if content_type=="Poll" and len(text.replace('\r','').split('\n')) <= 1:
			raise forms.ValidationError("Poll choices should be 2 or more")


class CommentCreationForm(forms.ModelForm):

	class Meta:
		model = Comment
		fields = ('text',)

	def clean_text(self):
		text = self.cleaned_data['text']
		if len(text)<=2:
			# no need to be specifiv
			# once the form becomes invalid save() wont be invoked
			raise forms.ValidationError("---")
		return text

	def save(self, user, content, reply):
		comment = Comment.objects.create(
			author=user,
			text=self.cleaned_data['text'],
			content=content,
		)
		comment.save()
		if reply!=0:
			try:
				sub_comment = Comment.objects.get(id=reply)
				if sub_comment.content == content:
					comment.reply = sub_comment
				elif sub_comment.content != content:
					comment.delete()
					return None
			except:
				comment.delete()
				return None

		comment.save()
		return comment


class CommentUpdateForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ('text',)

	def clean_text(self):
		text = self.cleaned_data['text']
		if len(text)<=2:
			# no need to be specifiv
			# once the form becomes invalid save() wont be invoked
			raise forms.ValidationError("---")
		return text

	def save(self, comment):
		comment.text = self.cleaned_data['text']
		comment.save()
		return comment