import shutil

from flask import flash, send_from_directory, request, Response, url_for
from markupsafe import Markup

from projects.stahh_besger.stahh_besger import parse_signatures, parse_urls, write_order_pdf, process_form_data, \
    create_zip, stream_zip
from projects.stahh_besger.forms import InputForm
from projects.stahh_besger.stahh_besger import Constants
from pathlib import Path

from flask import Blueprint, render_template
stahh_besger_bp = Blueprint('stahh_besger', __name__, template_folder='templates/stahh_besger')

@stahh_besger_bp.route('/stahh_besger/', methods=["GET", "POST"])
def stahh_besger_form(debug=False, mk_zip=True):
    form = InputForm()
    if form.validate_on_submit():
        name, datum, sig_data, url_data = process_form_data(form) # extract strings and lists from submitted form

        order_dir = Path(f"{Constants.OUTPUT_DIR}/{name}_{datum}")
        if not order_dir.exists(): # In theory a permissions check would be in order or a try / except but given the app's scope this is perfectly feasible
            Path.mkdir(order_dir)

        if debug:
            flash(f'Schreibe in ordner {order_dir}')

        if len(url_data) > 0:
            sig_data.extend(parse_urls(url_data))
        structured_sigs = parse_signatures(sig_data)

        for sig in structured_sigs:
            data = {Constants.NAME_KEY:name, Constants.DATE_KEY: datum, Constants.ID1_KEY:sig[0], Constants.ID2_KEY:sig[1]}
            pdf_name = write_order_pdf(order_dir, data)
            if debug:
                flash(f'"{pdf_name}.pdf" erstellt')

        if mk_zip:
            zip_path = Path(f'{order_dir}/{name}_{datum}.zip')
            if debug:
                flash(f'ZIP: {zip_path}')
            create_zip(zip_path, order_dir)
            # Possible improvement documented here: https://medium.com/analytics-vidhya/receive-or-return-files-flask-api-8389d42b0684 (Improve)
            dl_url = url_for('.download_file', order = f'{name}_{datum}')
            if debug:
                flash(dl_url)
            message = Markup(f"<a href='{dl_url}?del={form.delete_after_dl.data}&leg={form.legacy_dl.data}'>ZIP herunterladen</a>")
            flash(message) # Not the fanciest way to display the download but it works and I don't have to deal with (de)activating buttons using css or javascript.

    return render_template("stahh_besger/form.html", form=form)

@stahh_besger_bp.route('/stahh_besger/output/<string:order>.zip')
def download_file(order):
    cleanup = request.args.get('del')
    legacy = request.args.get('leg')
    folder = Path(f"{Constants.OUTPUT_DIR}/{order}")
    zip_name = f'{order}.zip'
    zip_path = Path(f'{folder}/{zip_name}')
    if legacy == 'True': # legacy method simply sends the file and keeps all files on the server
        return send_from_directory(folder, zip_name, as_attachment=True)
    else: # stream from memory
        stream_data = stream_zip(zip_path)
        if cleanup == 'True': # cleanup does not work with legacy method
            shutil.rmtree(folder)
        return Response(stream_data, mimetype='application/zip', direct_passthrough=True) # required workaround as per https://help.pythonanywhere.com/pages/FlaskSendFileBytesIO/

@stahh_besger_bp.route('/stahh_besger/dryrun')
def dryrun():
    name = 'John Doe'
    datum = '12.12.1950'
    sig_data = ['abc_btt','123_456']
    url_data = []
    order_dir = Path(f"{Constants.OUTPUT_DIR}/{name}_{datum}")
    return f"""
            Outputfolder: {Path(f"{order_dir}")} <br/>
            Zip-Route: {url_for('.download_file', order = f"{name}_{datum}")}<br/>
            Zip-Location: {Path(f'{order_dir}/{name}_{datum}.zip')}
            """
