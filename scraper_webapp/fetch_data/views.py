
import os
import json
import tempfile
import zipfile
from cStringIO import StringIO

from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.core.servers.basehttp import FileWrapper

from .forms import URLForm
from spiders import MySpider
from .models import Webpage



def index(request):	
	return  render(request, 'fetch_data/index.html', { 'form': URLForm(), })


def get_url(request):
	if request.method == 'POST' :
		form = URLForm(request.POST)
		if form.is_valid():
			form.save()
			url = form.cleaned_data['page_url']
			conf_url = change_url(url)
			os.system("scrapy crawl fetch_data -a start_url="+url+" -s IMAGES_STORE='files/images/"+conf_url+"'")
			data = json.loads(open('fetch_data_items.json').read())
			title = data['title']
			headings = data['headings']
			links = data['links']
			paragraphs = data['paragraphs']
			return render(request, 'fetch_data/get_url.html', { 
																'page_url':conf_url, 
																'title':title, 
																'headings':headings, 
																'links':links, 
																'paragraphs':paragraphs, 
																})

	return  HttpResponse("Form submission failed.")

	
def downloads(request, page_url):
	return render(request, 'fetch_data/downloads.html', { 'page_url' :page_url })


def generate_text_file():
	# This method generates a text file which will be provided to user
	data = json.loads(open('fetch_data_items.json').read())
	title = data['title']
	headings = data['headings']
	links = data['links']
	paragraphs = data['paragraphs']

	with open('content.txt', 'w') as f:
		f.write("Page title: \n")
		for t in title:
			t.encode("utf8")
			f.write(t+"\n")
		
		f.write("\nPage headings: \n")
		for heading in headings:
			heading.encode("utf8")
			f.write(heading+"\n")
		
		f.write("\nParagraphs: \n")
		for para in paragraphs:
			para.encode("utf8")
			f.write(para+"\n")
		
		i = 0
		f.write("\nLinks: \n")
		for l in links:
			i+=1
			l.encode("utf8")
			f.write(str(i)+". "+l+"\n")

	return 'content.txt'


def download_text_files(request, page_url):
	filename = generate_text_file()
	wrapper = FileWrapper(file(filename))
	response = HttpResponse(wrapper, content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename=content.txt'
	response['Content-Length'] = os.path.getsize(filename)
	
	return response


def download_images(request, page_url):
	filenames = []
	#conf_url = change_url(url)
	for fn in os.listdir("files/images/"+page_url+"/full/"):
	    filenames.append("files/images/"+page_url+"/full/"+fn)

	# Folder name in ZIP archive which contains the above files
	# E.g [thearchive.zip]/somefiles/file2.txt
	# FIXME: Set this to something better
	zip_subdir = "images"
	zip_filename = "%s.zip" % zip_subdir

	# Open StringIO to grab in-memory ZIP contents
	s = StringIO()

	# The zip compressor
	zf = zipfile.ZipFile(s, "w")

	for fpath in filenames:
	    # Calculate path for file in zip
	    fdir, fname = os.path.split(fpath)
	    zip_path = os.path.join(zip_subdir, fname)

	    # Add file, at correct path
	    zf.write(fpath, zip_path)

	# Must close zip for all contents to be written
	zf.close()

	# Grab ZIP file from in-memory, make response with correct MIME-type
	resp = HttpResponse(s.getvalue(), content_type = "application/zip")
	# ..and correct content-disposition
	resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

	return resp


def download_all_files(request, page_url):
	textfile = generate_text_file()
	#conf_url = change_url(url)
	#temp = tempfile.TemporaryFile()
	zip_subdir = "images"
	zip_filename = "files.zip"

	s = StringIO()
	archive = zipfile.ZipFile(s, 'w')
	
	archive.write(textfile, textfile)

	imagefiles = []
	for fn in os.listdir("files/images/"+page_url+"/full/"):
	    imagefiles.append("files/images/"+page_url+"/full/"+fn)
	
	for imagefile in imagefiles:
		fdir, fname = os.path.split(imagefile)
		zip_path = os.path.join(zip_subdir, fname)

		archive.write(imagefile, zip_path)

	archive.close()
	#wrapper = FileWrapper(s)
	response = HttpResponse(s.getvalue(), content_type='application/zip')
	response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

	return response


def change_url(url):
	# change the url to be replaced as directory name for storing images.
	# now files can be differentiate on the basis of this parameter
	# mapping this parameter with actual url will give proper information about file.
	url1 = url.replace("/", "_").replace(":", "_").replace(".", "_").replace("?", "_")
	return url1