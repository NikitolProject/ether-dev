import requests

# Import the following modules
from captcha.image import ImageCaptcha

# Create an image instance of the given size
image = ImageCaptcha(width=280, height=90)

response = requests.get('https://www.random.org/strings/?num=1&len=6&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new')

print(response.text.replace("\n", ""))

# Image captcha text
captcha_text = response.text.replace("\n", "")

# write the image on the given file and save it
image.write(captcha_text, 'captcha.png')
