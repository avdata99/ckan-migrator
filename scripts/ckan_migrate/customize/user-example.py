"""
To use something like this, you should rename this file to user.py
"""


def transform_user(user):
    """ Apply custom transformations
        Example: skip users with 'about' filled or created after 2017-03-21
        If we return None, the user will be skipped
        If we return the user, it will be migrated as is
    """
    if user.get('about'):
        return None

    created = user.get('created')
    created_str = str(created)
    created_date = created_str.split(' ')[0]
    if created_date > '2017-03-21':
        return None

    return user
