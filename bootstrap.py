#!/usr/bin/env python3
import argparse
from jinja2 import (
    FileSystemLoader,
    Environment,
)
import os

root = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(root, 'templates')
env = Environment(
    loader=FileSystemLoader(template_dir),
    keep_trailing_newline=True,
)

template_mappings = {
    '__main__.py': 'src',
}


def template_name_to_filename(template_name):
    return template_name.rstrip('.j2')


def one_of(choices):
    def _one_of(value):
        if value not in choices:
            raise TypeError('must be one of {}'.format(choices))
        return value
    return _one_of


def bool_ex(value):
    if value.lower() in {'yes', 'y', 'true', '1'}:
        return True
    if value.lower() in {'no', 'n', 'false', '0'}:
        return False
    raise TypeError('must be a boolean response')


def prompt(
    prompt_text,
    default='',
    whitespace_stripping='all',
    required=True,
    type=str,
    end=None,
):
    """
    args:
        prompt_text             Prompt text
        default                 Default value
        whitespace_stripping    One of: all, left, right, none
        required                If True, cannot be empty
        type                    Value type
        end                     Prompt text ending

    returns:
        User-entered value
    """
    if end is None:
        if type == bool_ex:
            end = '? '
        else:
            end = ': '
    while True:
        value = input('{}{}'.format(prompt_text, end))
        if whitespace_stripping in ('all', 'left'):
            value = value.lstrip()
        if whitespace_stripping in ('all', 'right'):
            value = value.rstrip()
        if not value:
            value = default
        if not value and required:
            print('Field required')
        else:
            try:
                return type(value)
            except ValueError as e:
                print(e)


def generate_template(filename, data, outdir='.'):
    template = env.get_template(filename + '.j2')
    with open(os.path.join(outdir, filename), 'w') as f:
        f.write(template.render(**data))


def interactive():
    return dict(
        name=prompt('Package name'),
        repository=prompt('Repository URL', required=False),
        author_name=prompt('Author name'),
        author_email=prompt('Author email'),
        description=prompt('Description', required=False),
        console_script=prompt(
            'Is this a console script [yes]',
            type=bool_ex,
            default='yes',
        )
    )


def cleanup():
    for template_name in os.listdir(template_dir):
        filename = template_name_to_filename(template_name)
        filepath = os.path.join(template_mappings.get(filename, '.'), filename)
        if os.path.isfile(filepath):
            os.remove(filepath)


def get_parser():
    parser = argparse.ArgumentParser()
    sps = parser.add_subparsers(dest='command')
    sps.add_parser('interactive')
    manual_parser = sps.add_parser('manual')
    manual_parser.add_argument('name')
    manual_parser.add_argument('author_name')
    manual_parser.add_argument('author_email')
    manual_parser.add_argument('-r', '--repository', default='')
    manual_parser.add_argument('-d', '--description', default='')
    manual_parser.add_argument(
        '--no-cli',
        action='store_false',
        dest='console_script',
    )
    sps.add_parser('undo')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    opts = parser.parse_args()
    if opts.command == 'undo':
        cleanup()
    else:
        if opts.command is None or opts.command == 'interactive':
            data = interactive()
        else:
            if os.path.isfile(opts.description):
                with open(opts.description) as f:
                    opts.description = f.read()
            data = opts.__dict__
        for template_name in os.listdir(template_dir):
            filename = template_name_to_filename(template_name)
            outdir = template_mappings.get(filename, '.')
            generate_template(filename, data, outdir)
