"""
Tool to import metadata from SM4 audio files
Output is stored in the specified database.

Arguments: [directory to search]

Copyright (c) Damian Christey
License: LGPL
"""

import sys
from time import time
from datetime import datetime
from pathlib import Path

## Required for Azure Data Lake Storage Gen1 filesystem management
from azure.datalake.store import core, lib, multithread

# import things from Flask app
from app import db, create_app
from app.models import AudioFile
from app.audio.azure_datalake import get_azure_vfs

app = create_app()
app.app_context().push()

# get the Azure path from the command line
base_path = sys.argv[1]

try:
    t = time()
    imported = 0
    skipped = 0
    existing = 0
    moved = 0
    duplicate = 0

    vfs = get_azure_vfs()
    dir_contents = vfs.walk(base_path, details=True)
    for item in dir_contents:
        if item['type'] == 'FILE':
            path = Path(item['name'])
            name_ext = path.suffix
            if name_ext == '.wav':
                file_name = path.name
                file_path = str(path.parent)
                file_size = item['length']
                name_meta = path.stem.split('_')
                if len(name_meta) == 3:
                    sn = name_meta[0]
                    timestamp = datetime.strptime(name_meta[1]
                                                  + ' ' + name_meta[2],
                                                  '%Y%m%d %H%M%S')
                    # check for existing records for the file name
                    existing_file = AudioFile.query.filter_by(name=file_name).first()
                    if existing_file:
                        if existing_file.path == file_path:
                            # Skip over existing records if the path hasn't changed
                            existing += 1
                        elif vfs.exists(existing_file.path+'/'+file_name):
                            # Skip over duplicate files if the old file still exists
                           duplicate += 1
                        else:
                            # File has moved, update the database record
                            existing_file.path = file_path
                            moved += 1
                    else:
                        new_file = AudioFile()
                        new_file.name = file_name
                        new_file.path = file_path
                        new_file.sn = sn
                        new_file.timestamp = timestamp
                        new_file.size = file_size
                        # add new record to be committed later
                        db.session.add(new_file)
                        imported += 1
                else:
                    # Wrong number of underscores in file name
                    skipped += 1
            else:
                # Not a wav
                skipped += 1
    # attempt to commit all changes to the database
    db.session.commit()
except Exception as e:
    print('Something bad happened: {0}'.format(e))
    print('Stopped on: {0}/{1}'.format(file_path, file_name)) 
    print('The following changes were not saved!')
    # roll back changes on error
    db.session.rollback()

finally:
    print('Imported wav files: {0}'.format(imported))
    print('Moved wav files: {0}'.format(moved))
    print('Existing skipped: {0}'.format(existing))
    print('Duplicates skipped: {0}'.format(duplicate))
    print('Other files skipped: {0}'.format(skipped))
    print('Time elapsed: {0} seconds'.format(time() - t))
