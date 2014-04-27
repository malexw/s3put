# s3put

s3put is a script for uploading files to Amazon S3.

```
usage: s3put [-h] [-c CONFIG] source dest

example: s3put test_file.txt my-s3-bucket/directory/test_file
```

source is a path pointing to a local file
dest is an Amazon S3 bucket and key. If the key ends with a '/', then the file name and extension of the source file will be appended to the provided dest.

The uploaded file will automatically be assigned the same Access Control List as the containing bucket.

## Configuration

s3put looks for a .s3_config file in the user's home directory for configuration information. The configuration file should have the following form:

```
[s3]
access_key_id=MY_KEY_ID
secret_access_key=MY_SECRET_KEY

[alias]
mybucket=my-long-s3-bucket-name
```

The alias section is optional.

## Aliases

Aliases give you the ability to refer to S3 buckets with a more convenient name. For example:

```
s3put test_file.txt mybucket/test
```

will upload test_file.txt to my-long-s3-bucket-name/test (using the above config file). Currently, aliases only work with bucket names.