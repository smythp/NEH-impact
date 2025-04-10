import sqlite3
from app import app
from flask import flash, redirect, render_template
from flask import request, session, url_for, jsonify
from app.forms import ZipForm
from collections import Counter
import config

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
    '''Makes sequence of question marks\
    that is NUM long for use in building SQL statements.'''
    x = '?, ' * num
    return x[:-2]


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title="404"), 404


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html', title="About")


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', title="FAQ")


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html', title="500"), 500


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
            distance = 10

        return redirect(url_for('search', zip_input=zip_input, distance=distance))

        
    return render_template('index.html', form=form,
                               jquery=True, title="Home")


# Handler for searches using query parameters
# Take the form: http://www.nehimpact.org/search/?zip=10016&distance=2
@app.route('/search/', methods=['GET'])
def route_search():
    query_parameters = request.args
    zip = query_parameters.get("zip")
    distance = query_parameters.get("distance")    
    division = query_parameters.get("division")
    
    return search(zip, distance, division=division)


@app.route('/search/zip/<zip_input>/distance/<distance>', methods=['GET'])
def search(zip_input, distance, division=None):

    form = ZipForm(request.form)
    
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    distance_query = 'SELECT end_zip from distances WHERE start_zip=? AND distance<?;'
        
    zips_to_return = [zipcode[0] for zipcode in cur.execute(distance_query, (zip_input, distance,)).fetchall()]

    # Add the original zip back in to the set of zips to be searched
    zips_to_return.append(zip_input)

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

    if division: 
        query = query[:-1] + " AND division_reclassification=?;"
        zips_to_return.append(division)
    
    conn2 = db_connect(config.DATABASE)
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

    # Descriptions used for tooltops
    division_description = {
        "research_education": "Research into areas related to pedagogy.",
        "other_humanities": "Humanities projects that don't fit neatly into other categories.",
        "education": "Grants related to teaching and education.",
        "research": "Grants related to research in the humanities.",
        "public_programs": "Projects and programs that engage the public directly.",
        "federal_state": "Collaborations with state or federal government.",
        "challenge_grants": "Grants that challenge institutions to raise additional funds that are matched by the NEH at a set rate.",
        "preservation_access": "Grants for preserving, restoring, or digitizing culture.",
        "digital_humanities": "Grants related to the digital humanities.",
        }

    all_divisions = [grant['division_reclassification'].lower() for grant in grants]

    division_count = Counter(all_divisions)
    distinct_divisions = set(all_divisions)

    divisions = []
    for classification in distinct_divisions:
        divisions.append({
            "class": classification,
            "name": display_names[classification],
            "count": division_count[classification],
            "description": division_description[classification],
            "filter_url": "/search/?zip=%s&distance=%s&division=%s" % (zip_input, distance, classification,)
            
            })
    
    return render_template('results.html', grants=grants,
                           updated_on=config.DATA_UPDATED_ON,
                           form=form, divisions=divisions, original_zip=zip_input,
                           results_count=results_count, distance=int(distance),
                           jquery=True, division_filter=division,
                           title="Results")
        

    
@app.route('/grant/<grant_id>', methods=['GET'])
def project_entry(grant_id):
    conn = db_connect(config.DATABASE)
    cur = conn.cursor()
    grant = cur.execute('SELECT * FROM grants WHERE id=?;', (grant_id,)).fetchone()

    return render_template('project_entry.html',
                           grant=grant, title=grant['ProjectTitle'])
