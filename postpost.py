#!/bin/python3

import os, sys, shutil, subprocess, argparse, json

THUMB_MAX_SIZE = 360

def post_info_msg(post, msg):
    print(f'{post['filename']} ({post.get('title', 'no title')}): {msg}')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='run without altering any files')
    parser.add_argument('--force-rebuild', action='store_true', help='ignore timestamps and rebuild all files')


    return parser.parse_args(sys.argv[1:])


def is_up_to_date(a, b):
    if force_rebuild:
        return False
    return os.path.exists(a) and os.path.getmtime(a) > os.path.getmtime(b)


def process_post(index):
    post = catalog[index]
    content = ""

    if 'image' in post:
        post['images'] = [post['image']]

    for image in post['images']:
        url = image if type(image) == str else image['url']
        alt = image.get('alt') if type(image) == dict else None

        if 'thumbnail' not in post:
            post['thumbnail'] = url

        content += ' '.join([
            '<a',
            f'href = "{url}"' if url else '',
            '><img style="width: 100%;"',
            f'src = "{url}"' if url else '',
            f'alt = "{alt}"' if alt else '',
            '></a>'
        ])
    

    title = post.get('title', 'no title')
    desc = post.get('description', 'no description')
    prev = None if index == 0 else f'{index - 1:03}.html'
    next = None if index == len(catalog) - 1 else f'{index + 1:03}.html'

    post['filename'] = f'{index:03}.html'

    post['html'] = (
            f'<--template --name="post" $title="{title}">'
            '<div class="window">'
                '<div class="hnav", style="position:absolute; right: 0;">'
                    f'{
                        (f'<a href="{prev}"><- prev</a>' if prev else '')
                        + f'<span>{(index + 1)}/{len(catalog)}</span>'
                        + (f'<a href="{next}">next -></a>' if next else '')
                    }'
                '</div>'
                f'<h2 style="text-align: left">{title}</h2>'
                f'{content}'
            '</div>'
            '</--template>'
        )


def make_preview(index):
    post = catalog[index]
    image_count = len(post['images'])
    if 'thumbnail' in post:
        thumb_path = os.path.join('thumbs', post['thumbnail'])
    title = post.get('title', 'untitled')
    return f"""
    <a href="{index:03}.html" class="card"><div class="window" style="flex: 1 0 auto;">
        <h1>{index:03}</h1>
        <h3>{title}</h3>
        {('<span class="image-count-label">1/'
            + str(image_count)
            + '</span>') if image_count > 1 else ''
        }
        {f'<img src="{thumb_path}" style="width: 100%">' if 'thumbnail' in post else ''}
    </div></a>"""


def even_groups(total, divisor):
    ret = [int(total/divisor)] * divisor
    for i in range(0, total % divisor):
        ret[i] += 1
    return ret


def write_thumb(post):
    if 'thumbnail' not in post:
        return
    thumb_src = os.path.join(resource_dir, post['thumbnail'])
    thumb_dst = os.path.join(output_dir, 'thumbs', post['thumbnail'])

    if not dry_run:
        good_files.append(thumb_dst)

    if is_up_to_date(thumb_dst, thumb_src):
        return

    if not dry_run:
        try:
            subprocess.run([
                'magick', thumb_src, '-strip', '-resize',
                f'{THUMB_MAX_SIZE}x', thumb_dst
            ])
        except FileNotFoundError:
            subprocess.run([
                'convert', thumb_src, '-strip', '-resize',
                f'{THUMB_MAX_SIZE}x', thumb_dst
            ])

    post_info_msg(post, f'generated thumbnail from {post['thumbnail']}')


def write_images(post):
    if not 'images' in post: return

    for file in post['images']:
        src_path = os.path.join(resource_dir, file)
        dst_path = os.path.join(output_dir, file)

        if not dry_run:
            good_files.append(dst_path)

        if not is_up_to_date(dst_path, src_path):
            if not dry_run:
                shutil.copyfile(src_path, dst_path)
            post_info_msg(post, f'image added: {file}')



def write_post(index):
    post = catalog[index]
    path = os.path.join(output_dir, post['filename'])
    good_files.append(path)

    write_images(post)
    write_thumb(post)

    previews.append(make_preview(index))

    replace = os.path.exists(path)
    
    if replace:
        with open(path, 'r') as f:
            if post['html'] == f.read():
                return
    
    if not dry_run:
        with open(path, 'w') as f:
            f.write(post['html'])
        
    if replace:
        post_info_msg(post, 'post updated')
    else:
        post_info_msg(post, 'post added')




def write_gallery(page_index):
    index_path = os.path.join(
            output_dir, 'index.html' if page_index == 0 else f'index{page_index + 1}.html'
        )
    columns_html = ""
    previews_start = page_index * POSTS_PER_PAGE
    previews_count = min(POSTS_PER_PAGE, len(previews) - previews_start)

    for n in even_groups(previews_count, COLUMNS):
        columns_html += (
                '<div class="vertical" style="width: 220px; flex: 1 0 auto;">'
                f'{''.join(previews[previews_start:previews_start + n])}'
                '</div>'
            )
        previews_start += n
    
    prev = None if page_index == 0 else '.' if page_index == 1 else f'index{page_index}.html'
    next = None if page_index == page_count - 1 else f'index{page_index + 2}.html'
    nav_buttons_html = f'{
            (f'<a href="{prev}"><- prev</a> ' if prev else '')
            + (f'<a href="{next}">next -></a>' if next else '')
        }'

    if dry_run: return

    with open(index_path, 'w') as f:
        f.write('<--template --name="basic-page" $title="art gallery">'
                '<div id="gallery-wrapper">'
                '<div class="vertical" style="align-items: center;">'
                        '<div class="horizontal" style="flex-wrap: wrap">'
                            f'{columns_html}'
                        '</div>'
                        '<div class="window hnav">'
                            f'{nav_buttons_html} <a href="#">back to top</a>'
                        '</div>'
                    '</div>'
                    '<div class="vertical" id="gallery-info">'
                        '<div class="window">'
                            '<h1>art gallery</h1>'
                            f'page {page_index + 1}/{page_count}'
                            '<br>'
                            f'{nav_buttons_html}'
                        '</div>'
                    '</div>'
                '</div>'
                '</--template>'
            )
    
    good_files.append(index_path)


args = parse_args()

with open('posts.json') as file:
    posts_text = file.read()

decoder = json.JSONDecoder()
posts_data = decoder.decode(posts_text)

output_dir = posts_data['output_dir']
resource_dir = posts_data['resource_dir']
catalog = posts_data['catalog']
good_files = []

dry_run = args.dry_run
force_rebuild = args.force_rebuild


for i in range(0, len(catalog)):
    process_post(i)

previews = []
page_count = 0

POSTS_PER_PAGE = 8
COLUMNS = 2

if not dry_run:
    thumb_path = os.path.join(output_dir, 'thumbs')
    os.makedirs(thumb_path, exist_ok=True)
    good_files.append(thumb_path)


for i in range(len(catalog)):
    write_post(i)

previews.reverse()

page_count = int(len(previews)/POSTS_PER_PAGE)
if len(previews) % POSTS_PER_PAGE:
    page_count += 1

for i in range(0, page_count):
    write_gallery(i)

print(f'{len(previews)} previews written ({page_count} pages)')

if not dry_run:
    for (root, dirnames, filenames) in os.walk(output_dir):
        for filename in filenames:
            path = os.path.join(root, filename)
            if path not in good_files:
                print(f'stray file in build directory: {path}')

if dry_run:
    print('DRY RUN - no files altered')





