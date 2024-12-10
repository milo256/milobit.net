#!/bin/python3

# milobit.net build script

#### OPTIONS #####
template_path = "src/templates"
docs_path = "src/docs"
out_path = "docs"

#### USAGE ####

# Summary:
    # this script takes no argunments and copies site files from docs_path to
    # out_path, using pseudo-tags to perform basic replacement operations on the
    # source documents. As not to conflict with real html tags and attributes,
    # pseudo-tags and attributes used by this script always begin with the -- prefix.
    # unlike real html, pseudo-tags and attributes are case-sensitive

# Using Templates:
    # templates can be used anywhere in an html document in docs_path, including
    # within other templates (but not in the template definition).
    #
    # the basic structure is as follows:
    #
    # <--template --name="template-name" --field="field-name: field-value; field-name1: field-value1">
    #   <inner-html>
    # </--template>
    #
    # where:
    #   template-name is filename of template to insert, .html extension omitted.
    #   field-name(1) and field-value(1) are names and values of fields defined in
    #       the template.
    #   inner-html is any html.

# Defining Templates:
    # Templates are nearly ordinary html files, and should use the file extension .html.
    #
    # Within a template, fields can be defined using the --field tag:
    #
    # <--field --name="field-name">
    #
    # when the template is used, any --field tag will be replaced by the field value
    # corresponding to field-name as defined in the --fields pseudo-attribute of --template.
    #
    # footgun warning: unused fields aren't checked for and will be wrongly left in
    # the final document if present.
    #
    # fields do not have to be used like normal html tags. they can be used anywhere,
    # including inside of strings or other tags.
    #
    # template definitions optionally contain no more than one --inner-html tag.
    # 
    # <--inner-html>
    #
    # --inner-thml is a so called void tag that must not include any content.
    # when the template is used, the inner-html tag will be replaced with the content
    # within the --template tag in the source document.



import re
import os
import shutil
from os import listdir
from os.path import isfile, join, split

class page:
    def __init__(self, relpath, typ, content):
        self.relpath = relpath
        self.typ = typ
        self.html_content = content

# find first innermost tag of given name in given html
# returns: tuple of indicies (start, html_start, html_end, end)
#          or None if the tag does not appear in the text.
# raises ValueError if the tag is invalid
def get_first_innermost(tag_name, text):
    start, html_start, html_end, end = (0, 0, 0, 0)
    while True:
        match = re.search("</?" + tag_name, text[html_start:])
        if (match == None):
            if (html_start == 0): return None
            else: raise ValueError("opening tag with no matching close")

        new_start = match.span()[0] + html_start
        new_html_start = text.index(">", new_start) + 1

        if text[new_start + 1] == '/':
            if (html_start == 0): raise ValueError("closing tag with no matching open")
            html_end = new_start
            end = new_html_start
            break;
        else:
            start, html_start = (new_start, new_html_start)
    return (start, html_start, html_end, end)

# parse attributes of an (opening) html tag, given as a string
# returns dictionary of attributes as strings
def parse_attributes(tag):
    attr = {}
    tag = tag.strip("<>");
    for m in re.finditer("([\\w-]+) *= *\"(.*?)\"", tag):
        attr[m.groups()[0]] = m.groups()[1]
    return attr

# insert given content into template so it can be used in a document
# returns string
def process_template(page, fields, inner_html):
    print(f"  -> applying: {page.relpath} with:")

    text = page.html_content
    for field in fields.split(";"):
        pair = field.split(":")
        if len(pair) != 2: raise ValueError("couldn't parse field: " + field) 
        key, value = pair[0].strip(), pair[1].strip()
        print("      - %s = %s" % (key, value))
        text = re.sub("<--field +--name *= *\"%s\" */?>" % key, value, text)

    matches = re.findall("<--inner-html>", text)
    if len(matches) > 1:
        raise ValueError(f"{page.relpath} contains more than one --inner-html tag")
    if inner_html != "" and len(matches) == 0:
        print("Warning: inner-html provided but not used")

    text = re.sub("<--inner-html>", inner_html, text)
    return text

def process_document(html_content, templates, rec=False):
    text = html_content

    m = get_first_innermost("--template", text)
    if m:
        start, html_start, html_end, end = m
        tag = text[start:html_start]
        html = text[html_start:html_end]

        attr = parse_attributes(tag)

        if "--name" not in attr:
            raise ValueError("template name required")
        name = attr["--name"]

        fields = ""
        if "--fields" in attr:
            fields = attr["--fields"]

        template = templates[name + ".html"]

        repl = process_template(template, fields, html)

        text = text[:start] + repl + text[end:]
        text = process_document(text, templates, True)
    else:
        if not rec:
            print("  -- no templates")

    return text

def find_build_files(wd, relpath = "", dct = None):
    if not dct:
        dct = dict()
    path = join(wd, relpath);
    for f in listdir(path):
        filepath = join(path, f)
        filerelpath = join(relpath, f)
        if isfile(filepath):
            content = ""
            name, typ = f.split(".")
            if (typ == "html"):
                with open(filepath) as file:
                    content = file.read()
            dct[filerelpath] = page(filerelpath, typ, content)
        else:
            dct = find_build_files(wd, f, dct)
    return dct

def find_existing_files(wd, relpath = "", st = set()):
    path = join(wd, relpath);
    for f in listdir(path):
        filepath = join(path, f)
        filerelpath = join(relpath, f)
        if isfile(filepath):
            st.add(filerelpath)
        else:
            find_existing_files(wd, f, st)
    return st
    

# returns 2-tuple of string copies and direct copies
def build(docs_path, template_path):

    template_pages = find_build_files(template_path)
    doc_pages = find_build_files(docs_path)

    strcp = [] # (text, relpath)
    filecp = [] # (srcpath, relpath)

    for name, page in doc_pages.items():
        print(page.relpath);
        if page.typ == "html":
            content = process_document(page.html_content, template_pages)
            strcp.append((content, page.relpath))
        else:
            print("  -> direct copy")
            filecp.append((join(docs_path, page.relpath), page.relpath))

    return (strcp, filecp)

def save(string_copies, file_copies, out_path):
    unbuilt = find_existing_files(out_path)
    for copy in string_copies:
        content = copy[0]
        relpath = copy[1]
        path = join(out_path, relpath)


        os.makedirs(split(path)[0], exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

        if relpath in unbuilt:
            print(f"  - replace: {relpath}")
            unbuilt.remove(relpath)
        else:
            print(f"  - new: {relpath}")
    for copy in file_copies:
        srcpath = copy[0]
        relpath = copy[1]
        dstpath = join(out_path, copy[1])

        os.makedirs(split(dstpath)[0], exist_ok=True)
        shutil.copyfile(srcpath, dstpath)

        if relpath in unbuilt:
            print(f"  - replace: {relpath}")
            unbuilt.remove(relpath)
        else:
            print(f"  - new: {relpath}")
    if len(unbuilt) > 0:
        print("Warning: unbuilt files in build directory")
        for file in unbuilt:
            print(f"  - {file}")

if __name__ == '__main__':
    try:
        string_copies, file_copies = build(docs_path, template_path)
    except Exception as e:
        print("Error while processing. No files altered.")
        print(f"  {e}")
        exit(1)
    else:
        print("")
        try:
            save(string_copies, file_copies, out_path)
        except Exception as e:
            print("Error while writing.")
            print(f"  {e}")








