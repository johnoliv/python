
#!/usr/bin/python
# atenuar efeitos de iluminacao (CLAHE)

# Copyright 2017
#   Johnatan Oliveira (johnoliv@gmail.com)
#   www.johnatan.net

import cv2, sys, os

pastaEntrada = "../pessoas_effects_ace_retinex/"
pastaSaida = "../pessoas_effects_final/"

prefixo = "F"
count = 1

def applyEffectsCLAHE(count, file):
    print("{0} > apply CLAHE em {1}".format(count, file))
    nomeParaSalvar = pastaSaida + file

    bgr = cv2.imread(pastaEntrada + file)
    other = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCR_CB)
    lum = other[:, :, 0]
    clahe = cv2.createCLAHE()
    lum = clahe.apply(lum)
    other[:, :, 0] = lum
    bgr = cv2.cvtColor(other, cv2.COLOR_YCR_CB2BGR)
    cv2.imwrite(nomeParaSalvar, bgr)


for file in os.listdir( pastaEntrada ):
    # if count > 5:
    #     break
    if file.endswith(prefixo,0,1) :
        # print("arquivo: {0}".format(pastaEntrada + file))
        applyEffectsCLAHE(count, file)
        count = count + 1
    else:
        print("REJEITADO: {0}".format(file))
