from blog.models import Content



def get_content(q, con_type, recent=False):
	contents = []
	if con_type == "post":
		contents = Content.objects.filter(draft=False, kind="Post").order_by("-timestamp")
	elif con_type == "poll":
		contents = Content.objects.filter(draft=False, kind="Poll").order_by("-timestamp")
	try:
		for content in contents:
			if (q in content.title) or (q in content.text):
				if recent:
					if content.was_published_recently():
						pass 
					else:
						contents.remove(content)
			else:
				contents.remove(content)
	except Exception as e:
		print(str(e))

	return contents


# T.B.C
def get_trending():
	contents = Content.objects.filter(draft=False, content_type='Post')
	if len(contents)>=1:
		return contents[0]






