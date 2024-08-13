"""
Convert North Saami – Spanish xlsx to GT-style xml.
"""
import argparse
from itertools import islice
from functools import partial
from collections import defaultdict, namedtuple
from pathlib import Path

MISSING_DEP_HELP = """
cannot run due to missing dependencies. hint, run:
python -m venv .venv && . .venv/bin/activate && pip install -r xlsx2xml-requirements.txt
...and then try again. (remember to run `deactivate` in the shell when you're done)
"""

try:
    from lxml.etree import Element, SubElement, tostring
    from openpyxl import load_workbook
except ImportError:
    exit(MISSING_DEP_HELP)


#  expected_column_names = (
#      "WORD",  # lemma, <l.text>
#      None,
#      None,
#      "INFLECTION", # inflection class, unsure about use yet
#      "WORD_CLASS_SAAMI",  # pos, attribute "pos" on <l>
#      "BASIC_FORM",  # unused
#      "TRANSLATION_NUMBER",
#      "RESTRICTION",  # tg -> <re> if not none
#      "SCIENTIFIC_NAME",  # mg -> <l_sci> if not none
#      "TRANSLATION",  # t value  if not none, else:
#      None,
#      "WORD_CLASS_SPANISH",  # t.pos if not none
#      "EXPLANATION",   # tg -> <expl> if not none
#      "TRANSLATION_SYNONYM1",
#      "TRANSLATION_SYNONYM2",
#      "TRANSLATION_SYNONYM3",
#      "TRANSLATION_SYNONYM4",
#      "TRANSLATION_SYNONYM5",
#      "TRANSLATION_SYNONYM6",
#      "SAAMI_EX_1",
#      "SPANISH_EX_1",
#      "SAAMI_EX_2",
#      "SPANISH_EX_2",
#      "SAAMI_EX_3",
#      "SPANISH_EX_3",
#      "SAAMI_EX_4",
#      "SPANISH_EX_4",
#  )


def check_and_insert(
    value,
    parent,
    tag_name,
    ppar=None,
    ppar_tag_name=None,
    t_element=None,
):
    if value is None:
        return
    value = str(value).strip()
    if value and t_element:
        if t_element[0]:
            if ppar is not None and ppar_tag_name is not None:
                parent = SubElement(ppar, ppar_tag_name)
            element = SubElement(parent, tag_name)
            element.text = value
            element = SubElement(parent, t_element[1])
            element.text = t_element[0]
            return element
    elif value:
        if ppar is not None and ppar_tag_name is not None:
            parent = SubElement(ppar, ppar_tag_name)
        element = SubElement(parent, tag_name)
        element.text = value
        return element


def t(entry, parent_tg, parent_mg):
    el = SubElement(parent_tg, "t")
    if entry.WORD_CLAss:
        el.set("pos", entry.WORD_CLAss)
    if entry.SCIENTIFIC_NAME:
        el.set("sci", entry.SCIENTIFIC_NAME)
    el.text = entry.TRANSLATION
    for n in range(1, 4):
        ex = getattr(entry, f"SAAMI_EX_{n}")
        if ex is not None:
            spanish_ex = getattr(entry, f"SPANISH_EX_{n}")
            check_and_insert(ex, "", "x", parent_tg, "xg", [spanish_ex, "xt"])
        if n <= 6: # Unnecessary here, but needed if the number of examples is increased, as in spa-sme
            syn = getattr(entry, f"TRANSLATION_SYNONYM{n}")
            check_and_insert(syn, "", "syn", parent_mg, "syng")


def dict2xml_bytestring(d):
    root = Element("r")
    for (lemma, pos), entries in d.items():
        # all_synonyms_are_the_same = all(
        #     entry.LEMMA_SYNONYM == entries[0].LEMMA_SYNONYM
        #     for entry in entries
        # )
        # assert all_synonyms_are_the_same

        e = SubElement(root, "e")
        lg = SubElement(e, "lg")
        l = SubElement(lg, "l")
        if pos is not None:
            l.set("pos", pos)
        if entries[0].LEMMA_SYNONYM is not None:
            l.set("syn", entries[0].LEMMA_SYNONYM)
        l.text = lemma

        for entry in entries:
            mg = SubElement(e, "mg")
            check_and_insert(entry.SCIENTIFIC_NAME, mg, "l_sci")
            tg = SubElement(mg, "tg")
            tg.set('{http://www.w3.org/XML/1998/namespace}lang', "spa")
            check_and_insert(entry.RESTRICTION, tg, "re")
            check_and_insert(entry.EXPLANATION, tg, "expl")
            check_and_insert(entry.INFLECTION, lg, "lsub") # Think this is the wrong tag
            t(entry, tg, mg)

    return tostring(root, encoding="utf-8", pretty_print=True)


def read_column_names(columns):
    field_counts = defaultdict(int)
    fields = []
    for col in columns:
        field = col[0].value.replace(" ", "_")
        n = field_counts[field]
        if n > 0:
            field = f"{field}_{n}"
        field_counts[field] += 1
        fields.append(field)

    return fields


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputfile")

    return parser.parse_args()


def main(args):
    wb = load_workbook(args.inputfile)

    # assume this is the dictionary one
    ws = wb.active

    field_names = read_column_names(ws.columns)
    Entry = namedtuple("Entry", field_names=field_names)

    lemmas = defaultdict(list)
    for row in islice(ws.rows, 1, None):
        e = Entry(*(
            col.value.strip() if isinstance(col.value, str) else col.value
            for col in row
        ))

        lemmas[(e.WORD, e.WORD_CLAš)].append(e) # This is not perfect, it merges homographs like beassi and vuovdi. Need input from Ángel

    
    xml_bytestring = dict2xml_bytestring(lemmas)
    with open(f"sme-spa.xml", "wb") as f:
        f.write(xml_bytestring)


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
