function preloadCallback(src, elementId){
		var img = document.getElementById(elementId)
		img.src = src
	}

	function preloadImage(imgSrc, elementId){
		// console.log("attempting to load " + imgSrc + " on element " + elementId)
		var objImagePreloader = new Image();
		objImagePreloader.src = imgSrc;
		if(objImagePreloader.complete){
			preloadCallback(objImagePreloader.src, elementId);
			objImagePreloader.onload = function(){};
		}
		else{
			objImagePreloader.onload = function() {
				preloadCallback(objImagePreloader.src, elementId);
				//    clear onLoad, IE behaves irratically with animated gifs otherwise
				objImagePreloader.onload=function(){};
			}
		}
	}

	/*
		Build a <p> for messages using markdown
		https://github.com/markdown-it/markdown-it
	*/
	function validateText(str)
	{
		var md = window.markdownit({
			highlight: function (str, lang) {
				if (lang && hljs.getLanguage(lang)) {
					try {
						return '<pre class="hljs"><code>' +
							hljs.highlight(lang, str, true).value +
							'</code></pre>';
					} catch (__) {}
				}
				return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
			},
			linkify: true,
		});
		var result = md.render(str);
		return result
	}
