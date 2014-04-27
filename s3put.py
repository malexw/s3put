#!/usr/bin/python

import argparse
import boto
import ConfigParser
from os import path
import sys


class ConfigurationError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class S3Config:

    def __init__(self, key_id, secret_key, aliases=None):
        self.key_id = key_id
        self.secret_key = secret_key
        self.aliases = aliases

def get_s3_config(s3_config_path=None):
    conf_file_path = s3_config_path if s3_config_path else path.expanduser('~') + '/.s3_config'

    cparser = ConfigParser.SafeConfigParser()
    cparser.read(conf_file_path)

    def get_with_default(parser, section, option, default):
        return parser.get(section, option) if parser.has_option(section, option) else default

    s3_key_id = get_with_default(cparser, 's3', 'access_key_id', None)
    s3_secret_key = get_with_default(cparser, 's3', 'secret_access_key', None)

    if not s3_key_id or not s3_secret_key:
        raise ConfigurationError('S3 configuration is missing access_key_id or secret_access_key')

    aliases = dict(cparser.items('alias')) if cparser.has_section('alias') else {}

    return S3Config(s3_key_id, s3_secret_key, aliases)

def calculate_destination(dest, source, s3conf):
    key_parts = dest.split('/')
    bucket = s3conf.aliases[key_parts[0]] if key_parts[0] in s3conf.aliases else key_parts[0]
    key_path = '/'.join(key_parts[1:])
    key = key_path + source.split('/')[-1] if len(key_path) == 0 or key_path[-1] == '/' else key_path

    return (bucket, key)

def is_acl_public(acl):
    for grant in acl.acl.grants:
        if grant.uri == u'http://acs.amazonaws.com/groups/global/AllUsers' and grant.permission == u'READ':
            return True

    return False

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Upload a file to Amazon S3')
    arg_parser.add_argument('source', help='The path to the file to upload.')
    arg_parser.add_argument('dest', help='The bucket and key to store the file in on S3.')
    arg_parser.add_argument('-c', '--config', help='Path to optional config file.')
    arg_parser.add_argument('-v', '--verbose', action='store_true', help='More detailed output when sending files.')
    # TODO: Add flag to automatically create the bucket if it doesn't exist.
    # TODO: Add flag to overwrite existing key if it already exists.
    args = arg_parser.parse_args()

    if not path.isfile(args.source):
        print 'Error: source file not found.'
        sys.exit(1)

    s3conf = get_s3_config(args.config)
    bucket_id, key_id = calculate_destination(args.dest, args.source, s3conf)

    if args.verbose:
        print 'Sending file to ' + bucket_id + '/' + key_id

    s3c = boto.connect_s3(s3conf.key_id, s3conf.secret_key)

    try:
        bucket = s3c.get_bucket(bucket_id)
    except boto.exception.S3ResponseError as e:
        # TODO: Be more specific about this error. Auth details wrong (403)? Bucket 403? Bucket 404?
        print 'Error: Failed to fetch S3 bucket'
        sys.exit(1)

    test_key = bucket.get_key(key_id)

    if test_key is not None:
        print 'Error: File already exists.'
        sys.exit(1)

    acl = bucket.get_acl()
    key = bucket.new_key(key_id)

    key.set_contents_from_filename(args.source)
    key.set_acl(acl)

    if is_acl_public(acl):
        print key.generate_url(0, query_auth=False)