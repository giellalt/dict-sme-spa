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
#      "G3_NomAg", # inflection types: G3 and NomAg
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

def insert_custom_paradigms(lg, l):
    if l.text == "gii" and l.get("pos") == "Pron, Interr":
        insert_pronoun_paradigm(lg, "Interr", "Sg", "gii", "gean", "geasa", "geas", "geainna", "geanin")
    elif l.text == "gii" and l.get("pos") == "Pron, Rel":
        insert_pronoun_paradigm(lg, "Rel", "Sg", "gii", "gean", "geasa", "geas", "geainna", "geanin")
    elif l.text == "mii" and l.get("pos") == "Pron, Interr":
        insert_mii_paradigm(lg, "Interr")
    elif l.text == "mii" and l.get("pos") == "Pron, Rel":
        insert_mii_paradigm(lg, "Rel")
    elif l.text == "goabbá" and l.get("pos") == "Pron, A, Interr":
        insert_pronoun_paradigm(lg, "Interr", "Sg", "goabbá", "goappá", "goabbái", "goappás", "goappáin", "goabbán")
    elif l.text == "goabbá" and l.get("pos") == "Pron, Rel":
        insert_pronoun_paradigm(lg, "Rel", "Sg", "goabbá", "goappá", "goabbái", "goappás", "goappáin", "goabbán")
    elif l.text == "goappašat" and l.get("pos") == "Pron, Indef":
        insert_pronoun_paradigm(lg, "Interr", "Pl", "goappašat", "goappašiid", "goappašiide", "goappašiin", "goappašiiguin", "goappašin")
    elif l.text == "guhte" and l.get("pos") == "Pron, A, Interr":
        insert_pronoun_paradigm(lg, "Interr", "Sg", "guhte", "guđe", "guhtii", "guđes", "guđiin", "guhten")
    elif l.text == "guhte" and l.get("pos") == "Pron, Rel":
        insert_pronoun_paradigm(lg, "Rel", "Sg", "guhte", "guđe", "guhtii", "guđes", "guđiin", "guhten")
    elif l.text == "guktot" and l.get("pos") == "Pron, Indef":
        insert_pronoun_paradigm(lg, "Indef", "Pl", "guktot", "guktuid", "guktuide", "guktuin", "guktuin", None)
    elif l.text == "juoga" and l.get("pos") == "Pron, Indef":
        insert_juoga_paradigm(lg, "Indef")
    elif l.text == "ieš" and l.get("pos") == "Pron":
        insert_ieš_paradigm(lg, "Refl")
    elif l.text == "mun" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Sg1", "mun", "mu", "munnje", "mus", "muinna", "munin")
    elif l.text == "don" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Sg2", "don", "du", "dutnje", "dus", "duinna", "dunin")
    elif l.text == "son" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Sg3", "son", "su", "sutnje", "sus", "suinna", "sunin")
    elif l.text == "moai" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Du1", "moai", "munno", "munnuide", "munnos", "munnuin", "munnon")
    elif l.text == "doai" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Du2", "doai", "dudno", "dudnuide", "dudnos", "dudnuin", "dudnon")
    elif l.text == "soai" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Du3", "soai", "sudno", "sudnuide", "sudnos", "sudnuin", "sudnon")
    elif l.text == "mii" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Pl1", "mii", "min", "midjiide", "mis", "minguin", "minin")
    elif l.text == "dii" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Pl2", "dii", "din", "didjiide", "dis", "dinguin", "dinin")
    elif l.text == "sii" and l.get("pos") == "Pron":
        insert_pronoun_paradigm(lg, "Pers", "Pl3", "sii", "sin", "sidjiide", "sis", "singuin", "sinin")


def insert_pronoun_paradigm(parent, type, num, nom, accgen, ill, loc, com, ess):
    mp = SubElement(parent, "mini_paradigm")
    a_nom = SubElement(mp, "analysis", ms=f"Pron_{type}_{num}_Nom")
    wf_nom = SubElement(a_nom, "wordform")
    wf_nom.text = nom
    a_accgen = SubElement(mp, "analysis", ms=f"Pron_{type}_{num}_Acc/Gen")
    wf_accgen = SubElement(a_accgen, "wordform")
    wf_accgen.text = accgen
    a_ill = SubElement(mp, "analysis", ms=f"Pron_{type}_{num}_Ill")
    wf_ill = SubElement(a_ill, "wordform")
    wf_ill.text = ill
    a_loc = SubElement(mp, "analysis", ms=f"Pron_{type}_{num}_Loc")
    wf_loc = SubElement(a_loc, "wordform")
    wf_loc.text = loc
    a_com = SubElement(mp, "analysis", ms=f"Pron_{type}_{num}_Com")
    wf_com = SubElement(a_com, "wordform")
    wf_com.text = com
    if ess is not None:
        a_ess = SubElement(mp, "analysis", ms=f"Pron_{type}_Ess")
        wf_ess = SubElement(a_ess, "wordform")
        wf_ess.text = ess

def insert_mii_paradigm(parent, type):
    mp = SubElement(parent, "mini_paradigm")
    a_gen = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Gen")
    wf_gen = SubElement(a_gen, "wordform")
    wf_gen.text = "man"
    a_acc = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Acc")
    wf_acc = SubElement(a_acc, "wordform")
    wf_acc.text = "maid"
    wf_acc2 = SubElement(a_acc, "wordform")
    wf_acc2.text = "man"
    a_ill = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Ill")
    wf_ill = SubElement(a_ill, "wordform")
    wf_ill.text = "masa"
    a_loc = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Loc")
    wf_loc = SubElement(a_loc, "wordform")
    wf_loc.text = "mas"
    a_com = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Com")
    wf_com = SubElement(a_com, "wordform")
    wf_com.text = "mainna"
    a_ess = SubElement(mp, "analysis", ms=f"Pron_{type}_Ess")
    wf_ess = SubElement(a_ess, "wordform")
    wf_ess.text = "manin"

def insert_ieš_paradigm(parent, type):
    mp = SubElement(parent, "mini_paradigm")
    a_du = SubElement(mp, "analysis", ms=f"Pron_{type}_Du_Nom")
    wf_du = SubElement(a_du, "wordform")
    wf_du.text = "ieža"
    a_pl = SubElement(mp, "analysis", ms=f"Pron_{type}_Pl_Nom")
    wf_pl = SubElement(a_pl, "wordform")
    wf_pl.text = "ieža"

def insert_juoga_paradigm(parent, type):
    mp = SubElement(parent, "mini_paradigm")
    a_nom = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Nom")
    wf_nom = SubElement(a_nom, "wordform")
    wf_nom.text = "juoga"
    wf_nom2 = SubElement(a_nom, "wordform")
    wf_nom2.text = "juoiddá"
    wf_nom3 = SubElement(a_nom, "wordform")
    wf_nom3.text = "juoidá"
    a_gen = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Gen")
    wf_gen = SubElement(a_gen, "wordform")
    wf_gen.text = "juoga"
    a_acc = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Acc")
    wf_acc = SubElement(a_acc, "wordform")
    wf_acc.text = "juoga"
    wf_acc2 = SubElement(a_acc, "wordform")
    wf_acc2.text = "juoiddá"
    wf_acc3 = SubElement(a_acc, "wordform")
    wf_acc3.text = "juoidá"
    a_ill = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Ill")
    wf_ill = SubElement(a_ill, "wordform")
    wf_ill.text = "juosat"
    a_loc = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Loc")
    wf_loc = SubElement(a_loc, "wordform")
    wf_loc.text = "juostá"
    a_com = SubElement(mp, "analysis", ms=f"Pron_{type}_Sg_Com")
    wf_com = SubElement(a_com, "wordform")
    wf_com.text = "juoidáin"
    a_ess = SubElement(mp, "analysis", ms=f"Pron_{type}_Ess")
    wf_ess = SubElement(a_ess, "wordform")
    wf_ess.text = "juoidán"
    wf_ess2 = SubElement(a_ess, "wordform")
    wf_ess2.text = "juonin"
    a_pl = SubElement(mp, "analysis", ms=f"Pron_{type}_Pl_Nom")
    wf_pl = SubElement(a_pl, "wordform")
    wf_pl.text = "juoidáid"


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
    if entry.WORD_CLASS_SPANISH:
        el.set("pos", entry.WORD_CLASS_SPANISH)
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
    for (lemma, pos, type), entries in d.items():

        e = SubElement(root, "e")
        lg = SubElement(e, "lg")
        l = SubElement(lg, "l")
        if pos is not None:
            l.set("pos", pos)
        if type is not None:
            l.set("type", type)
        l.text = lemma
        if pos.startswith("Pron"):
            insert_custom_paradigms(lg, l)

        for entry in entries:
            mg = SubElement(e, "mg")
            check_and_insert(entry.SCIENTIFIC_NAME, mg, "l_sci")
            tg = SubElement(mg, "tg")
            tg.set('{http://www.w3.org/XML/1998/namespace}lang', "spa")
            check_and_insert(entry.RESTRICTION, tg, "re")
            check_and_insert(entry.EXPLANATION, tg, "expl")
            #check_and_insert(entry.INFLECTION, lg, "lsub") # Think this is the wrong tag
            t(entry, tg, mg)

    return tostring(root, encoding="utf-8", pretty_print=True)


def read_column_names(columns):
    field_counts = defaultdict(int)
    fields = []
    for col in columns:
        if col[0].value is not None:
            orig_field = field = col[0].value.replace(" ", "_").replace("/", "_").replace("¿", "Q")
        else:
            orig_field = field = "Empty_field"
        n = field_counts[orig_field]
        if n > 0:
            field = f"{field}_{n}"
        field_counts[orig_field] += 1
        fields.append(field)

    return fields


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputfile")
    parser.add_argument("outputfile", type=Path)

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

        lemmas[(e.WORD, e.WORD_CLASS_SAAMI, e.G3_NomAg)].append(e)

    args.outputfile.parent.mkdir(exist_ok=True)
    xml_bytestring = dict2xml_bytestring(lemmas)
    with open(args.outputfile, "wb") as f:
        f.write(xml_bytestring)


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
