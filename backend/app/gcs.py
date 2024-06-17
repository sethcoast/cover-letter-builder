from google.cloud import storage

def upload_to_gcs(bucket_name, source_file, destination_blob_name, upload_from_file=False):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # if upload_from_file is True, source_file is a FileStorage object
    if upload_from_file:
        source_file_name = source_file.filename
        blob.upload_from_file(source_file)
    else:
        source_file_name = source_file
        blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
    
def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")