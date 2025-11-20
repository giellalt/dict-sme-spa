# Dictionary for sme — spa

This repository contains source files for a dictionary from North Sámi to Spanish. The content is licensed under the CC-BY-4.0 license.

Many of the dictionaries are published on [sátni.org](https://sátni.org) and [NDS](https://sanit.oahpa.no).

# Generating the XML file for use in NDS

The `/inc/` directory contains the original Excel source files. Whenever a Giellatekno-style XML file is needed, e.g. in NDS, this should be generated from the source using Python 3 and the script `scripts/xlsx2xml.py`.

Example usage: `python3 scripts/xlsx2xml.py inc/A_V_Saami_Spanish.xlsx`. More documentation can be found by running the script with `-h`.

# Contributions

Contributions are welcome, just clone and submit a pull request. Or use the in-place editor in GitHub to make your contributions. All contributions must be licensed under the same license as the original code.

# Citing

This dictionary is the work of Ángel Díaz de Rada at UNED and Kjell Kemi at UiT.