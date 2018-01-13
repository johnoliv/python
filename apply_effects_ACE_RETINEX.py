
#!/usr/bin/python
# atenuar efeitos de iluminacao (ACE E RETINEX)

# Copyright 2017
#   Johnatan Oliveira (johnoliv@gmail.com)
#   www.johnatan.net

import cv2, sys, glob, os, os.path, time
from PIL import Image
import colorcorrect.algorithm as cca
from colorcorrect.util import from_pil, to_pil

pastaEntrada = "../pessoas_align_crop_inner/"
pastaSaida = "../pessoas_align_crop_inner_effects/"

prefixo1 = "doc1"
prefixo2 = "selfie"
count = 1

def applyEffectsACE_RETINEX(count, filename, file):
    print("{0} > apply ACE/RETINEX em {1}".format(count, filename))
    chaveF = filename[28:36]
    nomeParaSalvar = pastaSaida + chaveF + '_' + file
    img = Image.open(filename)
    img = to_pil(cca.automatic_color_equalization(from_pil(img)))
    img = to_pil(cca.retinex(from_pil(img)))
    img.save(nomeParaSalvar)


# PEGA PASTAS E SUBPASTAS

for root, dirs, files in os.walk(pastaEntrada):
    # if count > 5:
    #     break
    for file in files:
        filename = os.path.join(root, file)
        if file.endswith(prefixo1,0,4) or file.endswith(prefixo2,0,6) :
            with open(filename, "r") as auto:
                applyEffectsACE_RETINEX(count, filename, file)
                count = count + 1
        else:
            print("REJEITADO: {0}".format(filename))
