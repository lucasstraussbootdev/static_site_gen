from enum import Enum
import re
from htmlnode import ParentNode, LeafNode


class TextType(Enum):
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


class TextNode:
    def __init__(self, text, text_type, url=None):
        self.text = text
        self.text_type = text_type
        self.url = url

    def __eq__(self, other):
        return (
            self.text == other.text
            and self.text_type == other.text_type
            and self.url == other.url
        )

    def __repr__(self):
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"


def text_node_to_html_node(text_node):
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text)
    if text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    if text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    if text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    if text_node.text_type == TextType.LINK:
        return LeafNode("a", text_node.text, {"href": text_node.url})
    if text_node.text_type == TextType.IMAGE:
        return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})

    raise Exception("Invalid text type")


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        split_nodes = old_node.text.split(delimiter)

        if len(split_nodes) % 2 == 0:
            raise Exception("Invalid Markdown syntax")

        for i in range(len(split_nodes)):
            if split_nodes[i] == "":
                continue
            if i % 2 == 0:
                new_nodes.append(TextNode(split_nodes[i], TextType.TEXT))
            else:
                new_nodes.append(TextNode(split_nodes[i], text_type))

    return new_nodes


def extract_markdown_images(text):
    return re.findall(r"!\[([^\[\]]*)\]\(([^\(\)]*)\)", text)


def extract_markdown_links(text):
    return re.findall(r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)", text)


def split_nodes_image(old_nodes):
    new_nodes = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        text = old_node.text
        images = extract_markdown_images(text)

        if len(images) == 0:
            new_nodes.append(old_node)
            continue

        for alt, url in images:
            sections = text.split(f"![{alt}]({url})", 1)

            if sections[0] != "":
                new_nodes.append(TextNode(sections[0], TextType.TEXT))

            new_nodes.append(TextNode(alt, TextType.IMAGE, url))
            text = sections[1]

        if text != "":
            new_nodes.append(TextNode(text, TextType.TEXT))

    return new_nodes


def split_nodes_link(old_nodes):
    new_nodes = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        text = old_node.text
        links = extract_markdown_links(text)

        if len(links) == 0:
            new_nodes.append(old_node)
            continue

        for anchor, url in links:
            sections = text.split(f"[{anchor}]({url})", 1)

            if sections[0] != "":
                new_nodes.append(TextNode(sections[0], TextType.TEXT))

            new_nodes.append(TextNode(anchor, TextType.LINK, url))
            text = sections[1]

        if text != "":
            new_nodes.append(TextNode(text, TextType.TEXT))

    return new_nodes


def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes


class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"


def markdown_to_blocks(markdown):
    blocks = markdown.split("\n\n")
    result = []

    for block in blocks:
        block = block.strip()
        if block != "":
            result.append(block)

    return result


def block_to_block_type(block):
    if re.match(r"^#{1,6} .+", block):
        return BlockType.HEADING

    if block.startswith("```\n") and block.endswith("```"):
        return BlockType.CODE

    lines = block.split("\n")

    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    is_ordered = True
    for i, line in enumerate(lines):
        if not line.startswith(f"{i + 1}. "):
            is_ordered = False
            break

    if is_ordered:
        return BlockType.ORDERED_LIST

    return BlockType.PARAGRAPH


def text_to_children(text):
    text_nodes = text_to_textnodes(text)
    html_nodes = []

    for text_node in text_nodes:
        html_nodes.append(text_node_to_html_node(text_node))

    return html_nodes


def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    children = []

    for block in blocks:
        block_type = block_to_block_type(block)

        if block_type == BlockType.PARAGRAPH:
            text = block.replace("\n", " ")
            children.append(ParentNode("p", text_to_children(text)))

        elif block_type == BlockType.HEADING:
            level = 0
            for char in block:
                if char == "#":
                    level += 1
                else:
                    break
            text = block[level + 1:]
            children.append(ParentNode(f"h{level}", text_to_children(text)))

        elif block_type == BlockType.CODE:
            text = block[4:-3]
            code_node = text_node_to_html_node(TextNode(text, TextType.CODE))
            children.append(ParentNode("pre", [code_node]))

        elif block_type == BlockType.QUOTE:
            lines = block.split("\n")
            stripped_lines = []
            for line in lines:
                stripped_lines.append(line.lstrip(">").strip())
            text = " ".join(stripped_lines)
            children.append(ParentNode("blockquote", text_to_children(text)))

        elif block_type == BlockType.UNORDERED_LIST:
            list_items = []
            for line in block.split("\n"):
                text = line[2:]
                list_items.append(ParentNode("li", text_to_children(text)))
            children.append(ParentNode("ul", list_items))

        elif block_type == BlockType.ORDERED_LIST:
            list_items = []
            for line in block.split("\n"):
                text = line.split(". ", 1)[1]
                list_items.append(ParentNode("li", text_to_children(text)))
            children.append(ParentNode("ol", list_items))

    return ParentNode("div", children)