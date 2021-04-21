'''
Staatsarchiv Bestellschein Generator (StArBesGer)

ÜBER
Um Archivgut des Staatsarchivs der Stadt Hamburg zu bestellen, müssen Nutzer für jeden Artikel einen Bestellschein in doppelter Ausführung anfertigen. Eine Möglichkeit, mehrere Bestellscheine auf einmal anzufertigen, besteht nicht. Dieses Script vereinfacht diesen Vorgang: Es erlaubt Nutzern alle benötigten Artikel (entweder deren Signatur oder Link zum Rechercheportal des Archivs) in einer einzelnen CSV Tabelle einzutragen und extrahiert dann die benötigten Daten in PDF-Dokumente für jede Bestellung.

ABOUT (EN)
Requesting material from the Staatsarchiv in Hamburg requires the user to fill out a PDF form or excel sheet for each individual item, including a copy.

This script replaces this procedure with a single csv-table where the user only has to fill in name, date and the relevant IDs. The script can also retrieve the ID from the archive's search system, if a URL is provided.
'''
import os
import io
import zipfile
from pathlib import Path

import pdfrw
import requests
import bs4
from flask import Flask


class Constants():
	ROOT_DIR = Flask(__name__).root_path
	REL_PROJECT_PATH = '/projects/stahh_besger/'
	OUTPUT_DIR = Path(f'{ROOT_DIR}/output/')
	TEMPLATE_PDF = Path(f'{ROOT_DIR}/static/bestellschein.pdf')

	REQUIRED_DIRS = [OUTPUT_DIR] # used on app startup to create these directories

	QUERY_URL = 'https://recherche.staatsarchiv.hamburg.de/ScopeQuery5.2/detail.aspx?ID='
	NAME_KEY = "Name"
	DATE_KEY = "Datum"
	ID1_KEY = "Bestand"
	ID2_KEY = "Sig"

def parse_urls(url_data):
	''' Retrieve the signature from the search query '''
	signaturen = []
	for id in url_data:
		url = f'{Constants.QUERY_URL}{id}'
		page = requests.get(url)
		soup = bs4.BeautifulSoup(page.text, 'html.parser')
		signatur = soup.find("table", id="ctl00_cphMainArea_tblDetails").tr.contents[
			2].getText()  # akward navigation as the tds wrapping the data we want dont have ids
		signaturen.append(signatur)
	return signaturen

def parse_signatures(sig_data):
	'''
	Creates a list of two-value-tuples, representing the Bestandsnummer and the actual Signature. They need to be split,
	as the order form requires them to be written into separate fields.
	'''
	structured_sig = []
	for sig in sig_data:
		id1, id2 = sig.split('_',1)
		structured_sig.append((id1,id2),)
	return structured_sig

def write_order_pdf(output_folder, data):
	'''
	Creates a copy of the provided template pdf, filling in all form fields with the data
	See https://bostata.com/how-to-populate-fillable-pdfs-with-python/ for a lot of background information
	'''

	template_pdf = pdfrw.PdfReader(Constants.TEMPLATE_PDF)
	pdf_name = f'Bestellschein {data[Constants.NAME_KEY]} {data[Constants.DATE_KEY]} {data[Constants.ID1_KEY]}_{data[Constants.ID2_KEY].replace("/","")}'
	new_pdf_path = output_folder / f'{pdf_name}.pdf'

	# The interactive field inside a pdf are indicated by these /Keys
	annot_key = '/Annots' 
	annot_field_Key = '/T'
	subtype_key = '/Subtype'
	widget_subtype_key = '/Widget'

	# Collect all annotations in a simple array, then filter the annotation-fields we want using the passed data
	annotations = [annotation for annotation in template_pdf.pages[0][annot_key] if
				   annotation[subtype_key] == widget_subtype_key and annotation[annot_field_Key]]
	for a in annotations:
		key = a[annot_field_Key][1:-1]
		if key in data.keys():
			a.update(pdfrw.PdfDict(V=data[key])) # Write the intended data to the relevant fields

	pdfrw.PdfWriter().write(new_pdf_path, template_pdf)
	return pdf_name

def process_form_data(form):
	name = form.name.data
	datum = form.datum.data.strftime('%d.%m.%Y')
	sig_data = form.signaturen.data.split('\r\n') if form.signaturen.data != "" else [] # if/else to avoid an empty list containing only [""]
	url_data = form.urls.data.split('\r\n') if form.urls.data != "" else []

	return name,datum,sig_data,url_data

def create_zip(zip_path, folder):
	with zipfile.ZipFile(zip_path, 'w') as zip_file:
		for folderName, subfolders, filenames in os.walk(folder):
			for filename in filenames:
				if "pdf" in filename:
					file_path = folder / filename
					zip_file.write(file_path, filename)
	return

def stream_zip(zip_path):
	data = io.BytesIO()
	with open(zip_path, 'rb') as fo:
		data.write(fo.read())
	data.seek(0)

	return data