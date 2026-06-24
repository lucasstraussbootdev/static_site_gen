import os
import sys
import shutil
from textnode import markdown_to_html_node


def copy_directory(source, destination):
    if os.path.exists(destination):
        shutil.rmtree(destination)

    os.mkdir(destination)

    for item in os.listdir(source):
        source_path = os.path.join(source, item)
        destination_path = os.path.join(destination, item)

        if os.path.isfile(source_path):
            print(f"Copying file: {source_path} -> {destination_path}")
            shutil.copy(source_path, destination_path)
        else:
            copy_directory(source_path, destination_path)


def extract_title(markdown):
    lines = markdown.split("\n")

    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    raise Exception("No h1 header found")


def generate_page(from_path, template_path, dest_path, basepath):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")

    with open(from_path) as f:
        markdown = f.read()

    with open(template_path) as f:
        template = f.read()

    html_node = markdown_to_html_node(markdown)
    html = html_node.to_html()
    title = extract_title(markdown)

    full_html = template.replace("{{ Title }}", title)
    full_html = full_html.replace("{{ Content }}", html)

    full_html = full_html.replace('href="/', f'href="{basepath}')
    full_html = full_html.replace('src="/', f'src="{basepath}')

    dest_dir = os.path.dirname(dest_path)
    if dest_dir != "":
        os.makedirs(dest_dir, exist_ok=True)

    with open(dest_path, "w") as f:
        f.write(full_html)

def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basepath):
    for item in os.listdir(dir_path_content):
        source_path = os.path.join(dir_path_content, item)

        if os.path.isdir(source_path):
            generate_pages_recursive(
                source_path,
                template_path,
                os.path.join(dest_dir_path, item),
                basepath,
            )

        elif item.endswith(".md"):
            if item == "index.md":
                dest_path = os.path.join(dest_dir_path, "index.html")
            else:
                name = item.replace(".md", "")
                dest_path = os.path.join(dest_dir_path, name, "index.html")

            generate_page(source_path, template_path, dest_path, basepath)
def main():
    basepath = "/"
    if len(sys.argv) > 1:
        basepath = sys.argv[1]

    copy_directory("static", "docs")
    generate_pages_recursive("content", "template.html", "docs", basepath)

main()