import sqlite3
from app import app
from flask import flash, redirect, render_template
from flask import request, session, url_for, jsonify
from app.forms import ZipForm

# This lets us import dictionaries from the database instead of tuples
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def db_connect(db_name):
    """Connect to named database and returns cursor object."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = dict_factory
    return conn.cursor()




@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    form = ZipForm(request.form)
    if request.method == 'POST' and form.validate():
        zip_input = request.form['zip']
        grants = []
        zip_input = request.form['zip']

        import xml.etree.ElementTree as ET

        tree = ET.parse('NEH_Grants2010s.xml')
        root = tree.getroot()

        for grant in root:
            xml_zip = grant.find('InstPostalCode').text

            if xml_zip and xml_zip[:5] == zip_input:
                title = grant.find('ProjectTitle').text
                grants.append(title)
            
        return render_template('results.html', grants=grants, form=form)
    else:
        return render_template('index.html', form=form)
        


    form = ZipForm(request.form)
    return render_template('index.html', form=form)
