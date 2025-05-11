#!/bin/python3

import os, sys, shutil, subprocess, argparse, json

THUMB_MAX_SIZE = 360

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')

    return parser.parse_args(sys.argv[1:])


def process_element(post, index):
    elem = post['content'][index]

    match elem['type']:
        case 'image':
            if 'thumbnail' not in post:
                post['thumbnail'] = elem['url']

            url = elem.get('url')
            alt = elem.get('alt')

            if url:
                resources.append(url)

            ret = ' '.join([
                '<a',
                f'href = "{url}"' if url else '',
                '><img style="width: 100%;"',
                f'src = "{url}"' if url else '',
                f'alt = "{alt}"' if alt else '',
                '></a>'
            ])
        case 'text':
            ret = elem.get('text', '')
    return ret


def process_post(index):
    post = catalog[index]
    elem_str_list = []
    for i in range(0, len(post.get('content', []))):
        elem_str_list.append(process_element(post, i))

    content = ''.join(elem_str_list)
    title = post.get('title', str(index))
    prev = None if index == 0 else f'{index - 1:03}.html'
    next = None if index == len(catalog) - 1 else f'{index + 1:03}.html'

    post['filename'] = f'{index:03}.html'

    post['html'] = f"""
<!DOCTYPE html><html lang="en"><head>
<title>{title}</title>
<link rel="stylesheet" href='/style.css'>
<meta name="viewport" content="width=device-width, initial-scale=1" /></head>
<body>
    <div class="horizontal centered">
    <div class="vertical align-start" style="max-width: 900px;">
        <div class="window hnav">
            <h2 class="inline">nav</h2><a href="/">home</a><a href="/art">gallery</a><a href="/com">commissions</a><a href="https://milobyte.atabook.org">guestbook</a>
        </div>
        <br>
        <div class="window">
            <div class="hnav", style="position:absolute; right: 0;">
                {
                    (f'<a href="{prev}"><- prev</a>' if prev else '')
                    + (f'<a href="{next}">next -></a>' if next else '')
                }
            </div>
            <h2>{title}</h2>
            {content}
        </div>
    </div>
    </div>
<footer>
    <p>milobit.net - est 2024</p>
</footer>
</body>
</html>
"""

def make_thumb(post):
    thumb_src = os.path.join(resource_dir, post['thumbnail'])
    thumb_dst = os.path.join(output_dir, 'thumbs', post['thumbnail'])
    subprocess.run([
        'magick', thumb_src, '-strip', '-resize',
        f'{THUMB_MAX_SIZE}x', thumb_dst
    ])

def make_preview(index):
    post = catalog[index]
    if 'thumbnail' in post:
        thumb_path = os.path.join('thumbs', post['thumbnail'])
    title = post.get('title', 'untitled')
    return f"""
    <a href="{index:03}.html" class="card"><div class="window" style="flex: 1 0 auto;">
        <h1>{index:03}</h1>
        <h3>{title}</h3>
        {f'<img src="{thumb_path}" style="width: 100%">' if 'thumbnail' in post else ''}
    </div></a>"""


args = parse_args()

with open('posts.json') as file:
    posts_text = file.read()

decoder = json.JSONDecoder()
posts_data = decoder.decode(posts_text)

output_dir = posts_data['output_dir']
resource_dir = posts_data['resource_dir']
catalog = posts_data['catalog']
resources = []


for i in range(0, len(catalog)):
    process_post(i)

previews = []
page_count = 0

POSTS_PER_PAGE = 8
COLUMNS = 2

def even_groups(total, divisor):
    ret = [int(total/divisor)] * divisor
    for i in range(0, total % divisor):
        ret[i] += 1
    return ret

def write_post(index):
    post = catalog[index]
    path = os.path.join(output_dir, post['filename'])
    if 'thumbnail' in post:
        make_thumb(post)
    previews.append(make_preview(index))
    with open(path, 'w') as f:
        f.write(post['html'])

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

    with open(index_path, 'w') as f:
        f.write('<--template --name="basic-page" $title="art gallery">'
                '<div id="gallery-wrapper">'
                '<div class="horizontal" style="flex-wrap: wrap">'
                f'{columns_html}'
                '</div>'
                '<div class="window">'
                '<h1>art gallery</h1>'
                f'page {page_index + 1}/{page_count}'
                '<br>'
                f'{
                    (f'<a href="{prev}"><- prev</a> ' if prev else '')
                    + (f'<a href="{next}">next -></a>' if next else '')
                }'
                '</div>'
                '</div>'
                '</--template>'
            )

if args.build:
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(os.path.join(output_dir, 'thumbs'))

    for res in resources:
        src_path = os.path.join(resource_dir, res)
        dst_path = os.path.join(output_dir, res)
        shutil.copyfile(src_path, dst_path)
    for i in range(len(catalog)):
        write_post(i)
    
    previews.reverse()

    page_count = int(len(previews)/POSTS_PER_PAGE)
    if len(previews) % POSTS_PER_PAGE:
        page_count += 1

    for i in range(0, page_count):
        write_gallery(i)





