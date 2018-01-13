
#!/usr/bin/python
# atenuar efeitos de iluminacao (Apenas ACE)

# Copyright 2017
#   Johnatan Oliveira (johnoliv@gmail.com)
#   www.johnatan.net

# EXECUTAR COM PYTHON 2 : python2 apply_effects_ACE.py

import cv2, sys, glob, os, os.path, time
from PIL import Image
import colorcorrect.algorithm as cca
from colorcorrect.util import from_pil, to_pil

pastaEntrada = "../pessoas_224x224_crop_bruta/"
pastaSaida = "../pessoas_224x224_ACE/"

count = 1

def applyEffectsACE(count, filename, file):
    # print("{0} > apply ACE em {1}".format(count, pastaSaida + file))
    nomeParaSalvar = pastaSaida + file
    img = Image.open(filename)
    img = to_pil(cca.automatic_color_equalization(from_pil(img)))
    img.save(nomeParaSalvar)

# PEGA PASTAS E SUBPASTAS

for root, dirs, files in os.walk(pastaEntrada):
    # TESTE
    if count > 5:
        break
    for file in files:
        filename = os.path.join(root, file)
        if "_id" in filename or "_selfie" in filename:
            with open(filename, "r") as auto:
                applyEffectsACE(count, filename, file)
                count = count + 1
        else:
            print("### REJEITADO: {0}".format(filename))

print("QTD ARQUIVOS COPIADOS: {0}".format(count))
