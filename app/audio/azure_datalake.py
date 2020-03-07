from flask import current_app
# Required for Azure Data Lake Storage Gen1 filesystem management
from azure.datalake.store import core, lib, multithread


# returns virtual file system object
def get_azure_vfs():

    # service-to-service authentication
    adlCreds = lib.auth(tenant_id = current_app.config['ADLS_TENANT'],
                    client_secret = current_app.config['ADLS_CLIENT_SECRET'],
                    client_id = current_app.config['ADLS_CLIENT_ID'],
                    resource = 'https://datalake.azure.net/')

    # Create a filesystem client object
    adls = core.AzureDLFileSystem(adlCreds, store_name=current_app.config['ADLS_ACCOUNT'])
    return adls
