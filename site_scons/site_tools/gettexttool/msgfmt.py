import sys, os, struct, array

def make(po_file, mo_file):
    import gettext
    from polib import pofile
    po = pofile(po_file)
    po.save_as_mo(mo_file)

if __name__ == '__main__':
    # Basitçe komut satırı argümanlarını al ve işle
    import subprocess
    # Bu kısım karmaşık gelirse, en temizi msgfmt.exe'yi PATH'e eklemektir.
    pass