import sqlite3
from app import app
from flask import flash, redirect, render_template
from flask import request, session, url_for, jsonify
from app.forms import ZipForm
from collections import Counter

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
    return conn


def question_mark_sequence(num):
    "Makes sequence of question marks that is NUM long for use in building SQL statements."
    x = '?, ' * num
    return x[:-2]


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html'), 500


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    form = ZipForm(request.form)
    if request.method == 'POST' and form.validate():

        zip_input = request.form['zip']

        if 'distance' in request.form:
            distance = request.form['distance']
        else:
            distance = 2.0

        conn = sqlite3.connect('grants.db')
        cur = conn.cursor()
        distance_query = 'SELECT end_zip from distances WHERE start_zip=? AND distance<?;'

        zips_to_return = [zipcode[0] for zipcode in cur.execute(distance_query, (zip_input, distance,)).fetchall()]

        query = 'SELECT Institution, \
InstCity, \
id, \
InstState, \
InstCountry, \
YearAwarded, \
ProjectTitle, \
Program, \
ProjectDesc, \
ToSupport, \
division_reclassification, \
PrimaryDiscipline \
FROM grants WHERE ShortPostal in (%s) \
AND (ProjectDesc is not null OR ToSupport is not null);' % question_mark_sequence(len(zips_to_return))

        conn2 = db_connect('grants.db')
        cur = conn2.cursor()
        grants = cur.execute(query, tuple(zips_to_return)).fetchall()

        results_count = len(grants)

        display_names = {
            "research_education": "Research and Education",
            "other_humanities": "Other Humanities",
            "education": "Education",
            "research": "Research",
            "public_programs": "Public Programs",
            "federal_state": "Federal or State Collaborations",
            "challenge_grants": "Challenge Grants",
            "preservation_access": "Preservation and Access",
            "digital_humanities": "Digital Humanities",
            }

        all_divisions = [grant['division_reclassification'] for grant in grants]

        division_count = Counter(all_divisions)
        distinct_divisions = set(all_divisions)

        divisions = []
        for classification in distinct_divisions:
            divisions.append({
                "class" : classification,
                "name" : display_names[classification],
                "count" : division_count[classification]
                })

        return render_template('results.html', grants=grants,
                               form=form, divisions=divisions,
                               results_count=results_count,
                               jquery=True)
        
    else:
        return render_template('index.html', form=form, jquery=True)
    
@app.route('/grant/<grant_id>', methods=['GET'])
def project_entry(grant_id):
    conn = db_connect('grants.db')
    cur = conn.cursor()
    grant = cur.execute('SELECT * FROM grants WHERE id=?;', (grant_id,)).fetchone()

    return render_template('project_entry.html', grant=grant)
