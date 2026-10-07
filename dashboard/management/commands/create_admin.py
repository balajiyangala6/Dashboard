"""Create the first MongoDB-backed Admin account."""

import getpass
import re
import sys

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import DuplicateKeyError

from dashboard.mongodb import create_account, get_collection


class Command(BaseCommand):
    help = 'Interactively create the first Admin account'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--email', default='')

    def handle(self, *args, **options):
        if get_collection('accounts').count_documents({'role': 'admin'}):
            raise CommandError(
                'An Admin account already exists. Create additional accounts from the Admin Console.'
            )

        username = options['username'].strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,80}', username):
            raise CommandError(
                'Username must be 3-80 characters using letters, numbers, dots, underscores, or hyphens.'
            )
        if not sys.stdin.isatty():
            raise CommandError('Run this command in an interactive terminal to enter a password securely.')

        password = getpass.getpass('Password (at least 12 characters): ')
        confirmation = getpass.getpass('Confirm password: ')
        if len(password) < 12:
            raise CommandError('Password must be at least 12 characters.')
        if password != confirmation:
            raise CommandError('The passwords do not match.')

        try:
            create_account(
                username,
                options['email'],
                username,
                'admin',
                make_password(password),
            )
        except DuplicateKeyError as exc:
            raise CommandError('That username is already in use.') from exc

        self.stdout.write(self.style.SUCCESS(
            f'Admin account "{username.lower()}" created.'
        ))
