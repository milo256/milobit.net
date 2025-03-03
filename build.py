#!/bin/python3

# milobit.net build script

class options:
    template_path = "templates"
    docs_path = "docs"
    out_path = "build"
    verbose = False

#### USAGE ####

# Summary:
    # this script copies site files from docs_path to out_path,
    # using pseudo-tags to perform basic replacement operations on the
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
    #   inner-html is any html.Sets are unordered sequences of unique values. a | b, or a.union(b), is the union of the two sets — i.e., a new set with all values found in either set. This is a class of operations called "set operations", which Python set types are equipped with.

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
import sys
import shutil
import subprocess
from os import listdir
from os.path import isfile, join, split, getmtime


def tput(args):
    try: return subprocess.check_output(["tput"] + args.split()).decode('latin1')
    except: return ""

class textfmt:
    bold = tput("bold")
    reset = tput("sgr0")
    blue = tput("setaf 4")
    yellow = tput("setaf 3")
    green = tput("setaf 2")
    red = tput("setaf 1")

class BuildError(Exception):
    pass

class DocumentError(Exception):
    pass

class page:
    def __init__(self, relpath, is_html, content, mtime):
        self.relpath = relpath
        self.is_html = is_html
        self.html_content = content
        self.mtime = mtime

warnings = []
def warn(msg):
    warnings.append(textfmt.yellow + "Warning: " + msg + textfmt.reset)

def print_warnings():
    for warning in warnings:
        print(warning);

def to_build_err(doc_name, err):
    return BuildError(f"in {doc_name}: " + str(err))

def log(msg):
    if options.verbose: print(msg)

# find first innermost tag of given name in given html
# returns: tuple of indicies (start, html_start, html_end, end)
#          or None if the tag does not appear in the text.
# raises DocumentError if the tag is invalid
def get_first_innermost(tag_name, text):
    start, html_start, html_end, end = (0, 0, 0, 0)
    while True:
        match = re.search("</?" + tag_name, text[html_start:])
        if (match == None):
            if (html_start == 0): return None
            else: raise DocumentError("opening tag with no matching close")

        new_start = match.span()[0] + html_start
        new_html_start = text.index(">", new_start) + 1

        if text[new_start + 1] == '/':
            if (html_start == 0): raise DocumentError("closing tag with no matching open")
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
def process_template(page, fields_provided, inner_html):
    log(f"  -> applying: {page.relpath} with:")
    
    text = page.html_content

    fields_required = set()
    for m in re.findall(r"<--field.*>", text):
        attr = parse_attributes(m)
        try:
            fields_required.add(attr["--name"]) 
        except KeyError:
            raise BuildError(f"in template `{page.relpath}` a field tag is missing the attribute --name")

    for field in fields_required:
        if not field in fields_provided:
            raise DocumentError(f"field `{field}` required for template `{page.relpath}`")

    for key, value in fields_provided.items():
        (text, nsubs) = re.subn(f"<--field +--name *= *\"{key}\" */?>", value, text)
        if (nsubs > 0):
            log(f"      - {key} = {value} ({nsubs} substitutions)")
        else:
            warn(f"in `{page.relpath}` field `{key}` provided not used")

    matches = re.findall("<--inner-html>", text)
    if len(matches) > 1:
        raise BuildError(f"template `{page.relpath}` contains more than one --inner-html tag")
    if inner_html != "" and len(matches) == 0:
        warn(f"in template `{page.relpath}` --inner-html provided but not used")

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
            raise DocumentError("template name required")
        name = attr["--name"]

        fields_str = ""
        if "--fields" in attr:
            fields_str = attr["--fields"]

        template = templates[name]

        # dictionary of fields provided
        fields = {}

        for field_str in fields_str.split(";"):
            field_list = field_str.split(":");
            if len(field_list) != 2: raise DocumentError(f"couldn't parse field `{field_str}`") 
            fields[field_list[0].strip()] = field_list[1].strip()

        repl = process_template(template, fields, html)

        text = text[:start] + repl + text[end:]
        text = process_document(text, templates, True)
    else:
        if not rec:
            log("  -- no templates")

    return text

# returns list of pages in wd and subdirectories
# wd is the path all rel(paths) are relative too, it doesn't change
# in recursive calls.
def find_build_files(wd, dir_rel = ""):
    pages = []
    for entname in listdir(join(wd, dir_rel)):
        ent_rel = join(dir_rel, entname)
        if isfile(join(wd, ent_rel)):
            content = ""
            is_html = entname.endswith(".html") or entname.endswith(".htm")
            mtime = getmtime(join(wd, ent_rel))
            if is_html:
                with open(join(wd, ent_rel)) as file:
                    content = file.read()
            pages += [page(ent_rel, is_html, content, mtime)]
        else:
            pages += find_build_files(wd, ent_rel)
    return pages

# returns set of string file relative paths
def find_existing_files(wd, relpath = ""):
    st = set();
    path = join(wd, relpath);
    if not os.path.exists(path):
        return st
    for f in listdir(path):
        filepath = join(path, f)
        filerelpath = join(relpath, f)
        if isfile(filepath):
            st.add(filerelpath)
        else:
            st |= (find_existing_files(wd, f))
    return st

def get_dependencies(page):
    deps = set()
    if not page.is_html:
        return deps

    text = page.html_content
    while(m := get_first_innermost("--template", text)):
        start, html_start, html_end, end = m
        attr = parse_attributes(text[start:html_start])
        if "--name" not in attr:
            raise BuildError("template name required")
        deps.add(attr["--name"])
        text = text[html_start:html_end]
    return deps

# when was the most recent modification of the document or any of the
# templates used in it.
def page_deps_mtime(page, templates):
    deps = get_dependencies(page)
    mtime = page.mtime
    for dep in deps:
        if not dep in templates:
            raise BuildError(f"{page.relpath}: reference to nonexistent template `{dep}`")
        mtime = max(mtime, templates[dep].mtime)
    return mtime

# returns 2-tuple of string copies and direct copies
def build(docs_path, template_path, out_path, unchecked_files):
    
    docs = find_build_files(docs_path)
    templates_list = find_build_files(template_path)
    
    templates = {re.sub(r'\.html?$', '', page.relpath): page for page in templates_list}

    outdated_docs = []

    for page in docs:
        if page.relpath in unchecked_files:
            last_built = getmtime(join(out_path, page.relpath))
            unchecked_files.remove(page.relpath)
            if page_deps_mtime(page, templates) > last_built:
                outdated_docs.append(page)
        else:
            outdated_docs.append(page)
    
    if len(unchecked_files) > 0:
        warn("stray files in build directory\n  - " + "\n  - ".join(unchecked_files))

    strcp = [] # (text, relpath)
    filecp = [] # (srcpath, relpath)


    for page in outdated_docs:
        log(textfmt.bold + page.relpath + textfmt.reset);
        if page.is_html:
            try:
                content = process_document(page.html_content, templates)
            except DocumentError as e:
                raise to_build_err(page.relpath, e)

            strcp.append((content, page.relpath))
        else:
            log("  -> direct copy")
            filecp.append((join(docs_path, page.relpath), page.relpath))

    return (strcp, filecp)

def save(string_copies, file_copies, out_path): 
    if len(string_copies) + len(file_copies) == 0:
        print("nothing to do; all files up to date")
        return
    
    os.makedirs(out_path, exist_ok=True)
    unbuilt = find_existing_files(out_path)

    for pair in string_copies:
        content, relpath = pair
        path = join(out_path, relpath)

        os.makedirs(split(path)[0], exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

        if relpath in unbuilt:
            print(f"- replaced: {relpath}")
            unbuilt.remove(relpath)
        else:
            print(f"- new: {relpath}")
    for pair in file_copies:
        srcpath, relpath = pair
        dstpath = join(out_path, relpath)

        os.makedirs(split(dstpath)[0], exist_ok=True)
        shutil.copyfile(srcpath, dstpath)

        if relpath in unbuilt:
            print(f"- replaced (direct copy): {relpath}")
            unbuilt.remove(relpath)
        else:
            print(f"- new (direct copy): {relpath}")

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        out_path = sys.argv[1]
    else: out_path = options.out_path

    existing_files = find_existing_files(out_path)
    try:
        string_copies, file_copies = build(options.docs_path, options.template_path, out_path, existing_files)
    except BuildError as e:
        print(textfmt.red + "Error while processing. No files altered." + textfmt.reset)
        print(f"  {e}")
    else:
        save(string_copies, file_copies, out_path)
    print_warnings()








