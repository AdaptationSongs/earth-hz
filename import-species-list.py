"""
Tool to import list of species and common names from Catalogue of Life

Arguments: [Download url]

Copyright (c) Damian Christey
License: LGPL
"""

import sys
from time import time
import urllib.request as req
import zipfile
import pandas as pd
import numpy as np

# import things from Flask app
from app import db, create_app
from app.models import Label, LabelType, CommonName, Language
from app.audio.azure_datalake import get_azure_vfs


def import_row(row, type_id, language_ids):
    imported_species = False
    imported_common_name = False
    language_id = language_ids.get(row['col:language'])
    label = Label.query.filter(Label.name == row['col:scientificName']).first()
    if not label: # scientific name not found in database
        label = Label(name=row['col:scientificName'], type_id=type_id)
        db.session.add(label)
        imported_species = True
    if row['col:name'] is not np.NaN: # common name is not blank
        if language_id: # language exists in database
            common_name = CommonName.query.join(Label).filter(Label.name == row['col:scientificName'], CommonName.name == row['col:name'], CommonName.language_id == language_id).first()
            if not common_name: # common name not found in database
                common_name = CommonName(name=row['col:name'], label=label, language_id=language_id)
                db.session.add(common_name)
                imported_common_name = True
    return [imported_species, imported_common_name]


app = create_app()
app.app_context().push()

# get the download url from the command line
url = sys.argv[1]

try:
    t = time()
    imported_species = 0
    imported_cnames = 0
    existing_species = 0
    existing_cnames = 0

    print('Downloading dataset...')
    zip_data, _ = req.urlretrieve(url)
    print('Extracting archive...')
    with zipfile.ZipFile(zip_data,"r") as zip_ref:
        name_usage = zip_ref.open('NameUsage.tsv')
        vernacular_name = zip_ref.open('VernacularName.tsv')

    print('Reading files...')
    scientific_name_df = pd.read_csv(name_usage, sep='\t')
    common_name_df = df = pd.read_csv(vernacular_name, sep='\t')
    species_df = scientific_name_df[scientific_name_df['col:rank'] == 'species']
    combined_df = pd.merge(species_df, common_name_df, left_on='col:ID', right_on='col:taxonID', how='left')
    deduped_df = combined_df.drop_duplicates(subset=['col:ID', 'col:language'])

    print('Importing...')
    type_id = LabelType.query.filter(LabelType.name == 'species').first().id
    languages = Language.query.all()
    language_ids = {lang.code3: lang.id for lang in languages}
    deduped_df[['imported_species', 'imported_common_name']] = deduped_df.apply(lambda row: import_row(row, type_id, language_ids), axis=1, result_type='expand')
    # attempt to commit all changes to the database
    db.session.commit()

except Exception as e:
    print('Something bad happened: {0}'.format(e))
    print('The following changes were not saved!')
    # roll back changes on error
    db.session.rollback()

finally:
    unique_species = len(deduped_df['col:ID'].unique())
    imported_species = len(deduped_df[deduped_df['imported_species'] == True])
    imported_common_names = len(deduped_df[deduped_df['imported_common_name'] == True])
    print('Species downloaded from CoL: {0}'.format(unique_species))
    print('Imported species: {0}'.format(imported_species))
    print('Imported common_names: {0}'.format(imported_common_names))
    print('Time elapsed: {0} seconds'.format(time() - t))
