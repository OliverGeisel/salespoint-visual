import pathlib
import re
import sys
from xml.dom import minidom

import svgwrite

import extension.minimalModel


def select_color(element: dict):
    color_start = ""
    if "selected" in element.keys():
        color_start = "\x1B[32m"  # green
    if "mandatory" in element.keys():
        color_start = "\x1B[31m"  # red
    color_end = "\x1B[0m" if element["element"].getAttribute(
        "mandatory") == "true" or "selected" in element.keys() else ""
    return color_start, color_end


def print_tree_info(tree, intent: int = 0):
    """
    Print the tree in console with attributes.
    @param tree: Tree to print.
    @type tree: dict
    @param intent: Number of intents line (default: 0)
    @type intent: int
    @return: Nothing
    @rtype: None
    """
    intent_str = "\t" * intent
    element = tree["element"]
    print(f"{intent_str}{element.tagName} - {element.attributes.items()}")
    if "children" in tree.keys():
        for child in tree["children"]:
            print_tree_info(child, intent + 1)


def print_tree_clean(tree: dict, intent: int = 0):
    """
    Print the tree in a cleaner version.
    @param tree: 
    @type tree: 
    @param intent: 
    @type intent: 
    @return: 
    @rtype: 
    """
    intent_str = "\t" * intent
    element = tree["element"]
    color_start, color_end = select_color(tree)
    print(f"{color_start}{intent_str}{element.getAttribute('name')} - {element.attributes.items()}{color_end}")

    if "children" in tree.keys():
        for child in tree["children"]:
            print_tree_clean(child, intent + 1)


def parse_prefix(name_complete: str):
    elements = name_complete.split("_")
    if re.fullmatch(r"[A-Z]", elements[0]):
        elements.pop(0)
    if re.match(r"\d+", elements[0]):
        elements.pop(0)
    return "_".join(elements)


def get_show_strings_mapping(tree_element: dict, intent: int = 0, chars: int = 4, back_list=None, color: bool = True,
                             space_char: str = " ", connect="-", prefix: bool = True) -> dict[str, list]:
    back = dict() if back_list is None else back_list
    senk = f'|{space_char * (chars - 1)}' * (intent - 1)
    intent_str = "" if intent == 0 else senk + "|" + connect * (chars - 1)
    # brach element
    element: minidom.Element = tree_element["element"]
    color_start, color_end = select_color(tree_element) if color else ("", "")

    if "selected" in tree_element.keys():
        name = element.getAttribute('name') if prefix else parse_prefix(element.getAttribute('name'))
        attributes = ["selected"]
        if "mandatory" in tree_element.keys():
            attributes.append("mandatory")
        if "minimal" in tree_element.keys():
            attributes.append("minimal")
        back[f"{color_start}{intent_str}{name}{color_end}"] = attributes
    if "children" in tree_element.keys():
        for child in tree_element["children"]:
            get_show_strings_mapping(child, intent + 1, chars, back, color, space_char, connect, prefix)
    return back


def get_show_strings(tree_element: dict, intent: int = 0, chars: int = 4, back_list=None, color: bool = True,
                     space_char: str = " ", connect="-", prefix: bool = True) -> list[str]:
    """
    Creates a list of strings, where every line is one element of the tree.
    @param tree_element: Tree to print.
    @type tree_element:dict
    @param intent: Number of intents. (default: 0)
    @type intent: int
    @param chars: length of one intent. (default: 4)
    @type chars: int
    @param back_list: list in which you store the lines. (default: None -> New list)
    @type back_list: list
    @param color: Add Ascii color. (default: True)
    @type color: bool
    @param space_char: Select the char in the intent. (default: " ")
    @type space_char: str
    @param connect: Select the char for a subelement intent-char. (default: "-")
    @type connect: str
    @param prefix: Removes prefixes (bevor last "_") in the name. (default: True)
    @type prefix: bool
    @return: List of strings.
    @rtype: list[str]
    """
    back = list() if back_list is None else back_list
    senk = f'|{space_char * (chars - 1)}' * (intent - 1)
    intent_str = "" if intent == 0 else senk + "|" + connect * (chars - 1)
    # brach element
    element: minidom.Element = tree_element["element"]
    color_start, color_end = select_color(tree_element) if color else ("", "")

    if "selected" in tree_element.keys():
        name = element.getAttribute('name') if prefix else parse_prefix(element.getAttribute('name'))
        back.append(f"{color_start}{intent_str}{name}{color_end}")
    if "children" in tree_element.keys():
        for child in tree_element["children"]:
            get_show_strings(child, intent + 1, chars, back, color, space_char, connect, prefix)
    return back


def print_tree_show(tree, intent=0, chars=4):
    gen = get_show_strings(tree, intent, chars)
    for line in gen:
        print(line)


def print_tree_selected(tree: dict, intent=0):
    intent_str = "\t" * intent
    element: minidom.Element = tree["element"]
    color_start, color_end = select_color(tree)
    if "selected" in tree.keys():
        print(
            f"{color_start}{intent_str}{element.getAttribute('name')} - {element.attributes.items()}{color_end}")
    if "children" in tree.keys():
        for child in tree["children"]:
            print_tree_selected(child, intent + 1)


def get_tree(element: minidom.Element, parent=None) -> dict:
    """
    Transform the dom to a simple tree version. 
    A dict with element, a list of children and attributes you want.
    @param element: Root-Element of the tree
    @type element: minidom.Element
    @param parent: Parent, if the tree should be inserted.
    @type parent: dict
    @return: The complete tree, if parent not None it's the parent.
    @rtype: dict
    """
    tree = {"element": element, "children": list()} if parent is None else parent
    children = tree["children"]
    for child in element.childNodes:
        # skip unused elements
        if isinstance(child, minidom.Text) or child.tagName == "description":
            continue
        # elements with subelements
        elif [x for x in child.childNodes if not (isinstance(x, minidom.Text) or x.tagName == "description")]:
            children.append({"element": child, "children": list()})
            get_tree(child, children[-1])
        else:
            children.append({"element": child})
    return tree


def _tree_as_list_sub(elements: list, back: list):
    for child in elements:
        back.append(child)
        try:
            _tree_as_list_sub(child["children"], back)
        except KeyError:
            pass


def tree_as_list(tree) -> list[dict]:
    """
    List every Node of the tree as a list. Deep-First.
    @param tree: Tree that should be listed.
    @type tree: dict
    @return: A list of the nodes in the tree.
    @rtype: list
    """
    back = list()
    back.append(tree)
    try:
        _tree_as_list_sub(tree["children"], back)
    except KeyError:
        pass
    return back


def in_tree_and_config(tree, elements: list):
    """
    Add all elements in tree the attribute 'selected', that are in the elements.  
    @param tree: The tree that will be compared
    @type tree: dict
    @param elements: List of element, that get the attribute "selected"
    @type elements: list
    @return: Nothing
    @rtype: None
    """
    for tree_element in tree_as_list(tree):
        if tree_element["element"].getAttribute("name") in elements:
            tree_element["selected"] = True
    _select_tree_transitive(tree)


def _select_tree_transitive(tree) -> bool:
    """
    Check the tree if a Top-level is selected, when a subelement is selected. 
    @param tree: Tree that will be checked.
    @type tree: dict
    @return: True if the top-element ist selected.
    @rtype: bool
    """
    # leaf or selected
    if "selected" in tree.keys() and "children" not in tree.keys():
        return tree["selected"]
    # not selected and no children
    if "children" not in tree.keys():
        return False
    # branch
    change = False
    for child in tree["children"]:
        if _select_tree_transitive(child):
            change = True
    if change:
        tree["selected"] = True
    return change


def _select_tree_transitive_func(tree, attribute, yes, no=None):
    # leaf or has attribute
    if attribute in tree.keys() and "children" not in tree.keys():
        return tree[attribute]
    if "children" not in tree.keys():
        return False
    # branch
    change = False
    for child in tree["children"]:
        if _select_tree_transitive_func(child, attribute, yes, no):
            change = True
    if change:
        tree[attribute] = yes
    else:
        if no is not None:
            tree[attribute] = no
    return change


def in_tree_and_config_func(tree, elements, func, attribute, yes, no=None, transitive=True):
    for tree_element in tree_as_list(tree):
        if func(tree_element, elements):
            tree_element[attribute] = yes
        else:
            if no is not None:
                tree_element[attribute] = no
    if transitive:
        _select_tree_transitive_func(tree, attribute, yes, no)


def get_structure(model_file: pathlib.Path):
    # prepare
    if not model_file.is_file():
        raise Exception("Datei ist nicht existent!")
    file_name = sys.argv[1]
    config_file = pathlib.Path(file_name)
    if not config_file.exists():
        raise Exception("Datei existiert nicht")
    elements = [x.strip() for x in config_file.open().readlines()]
    content: minidom.Document = minidom.parse(model_file.open("r"))
    structure: minidom.Element = content.getElementsByTagName("struct")[0]
    del content, file_name, config_file
    # edit and compare
    tree_structure = get_tree(structure)
    func = lambda x, y: x["element"].getAttribute("name") in y
    yes = True
    no = None
    in_tree_and_config_func(tree_structure, elements, func, "selected", yes, no)
    func = lambda x, y: x["element"].getAttribute("mandatory") == "true"
    in_tree_and_config_func(tree_structure, elements, func, "mandatory", yes, no)
    configs = extension.minimalModel.get_configs(pathlib.Path(""))
    minimal_model = extension.minimalModel.get_minimal_model(configs)
    func = lambda x, y: x["element"].getAttribute("name") in y
    in_tree_and_config_func(tree_structure, minimal_model, func, "minimal", yes, no)
    # print
    print_tree_show(tree_structure)
    draw_svg(tree_structure["children"][0], len(elements), 15)


def draw_svg(tree, num_lines: int, fontsize: int = 12):
    """
    Create SVG for the given tree.
    @param tree: Tree to draw.
    @type tree:dict
    @param num_lines: Number of lines in the tree.
    @type num_lines: int
    @param fontsize: Fontsize of the text (default: 12)
    @type fontsize: int
    @return:
    @rtype:
    """
    height = int((fontsize + 1) * num_lines * 1.3)
    picture = svgwrite.Drawing(f"{sys.argv[1].split('.')[0] if len(sys.argv) < 3 else sys.argv[2].split('.')[0]}.svg",
                               ("350", str(height)))
    # picture.append(drawSvg.Rectangle(0, 0, 400, 2400, ))
    for num, line in enumerate(
            get_show_strings_mapping(tree, color=False, prefix=False, intent=1, space_char="\xa0", connect="-").items(),
            1):
        fill = "#00e600" if "minimal" in line[1] else "black" if "mandatory" in line[1] else "#1aa3ff"
        style = f"font-size: {fontsize}px;"
        picture.add(
            picture.text(line[0], insert=(5, num * (fontsize + 1)), style=style, fill=fill))
    picture.save()


if __name__ == '__main__':
    get_structure(pathlib.Path("model.xml"))
