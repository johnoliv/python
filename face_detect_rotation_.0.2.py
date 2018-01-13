# FACE DETECTION WITH HAAR CASCADE AND ROTATION
#
# face_detect_rotation.py
#
# Copyright 2017
#   Johnatan Oliveira (johnoliv@gmail.com)
#   www.johnatan.net

# import the necessary packages
import numpy as np
import argparse, imutils
import cv2, sys, glob, os, os.path, time
from shutil import copyfile

start_time = time.time()

# CONFIG
cascPath = "haarcascade_frontalface_default.xml"
count = 1
countIMGFail = 0
countIMGOK = 0
#sufixo = ".jpg"
prefixo = "F"
data = "17.04.17_72px"
minSizeSetado = 72
pastaRelatorios = "relatorios/"
pastaFotos = "documentos/"
pastaFotosFinais =  "documentos_finais/"
pasta_2Faces_FotosFinais =  "documentos_finais_2Faces/"
totalImagens = len([name for name in os.listdir(pastaFotos) if os.path.isfile(os.path.join(pastaFotos, name))])

fFail = open(pastaRelatorios + 'out_DOC_FAIL_' + data + '.txt', 'w')
fOK = open(pastaRelatorios + 'out_DOC_OK_' + data + '.txt', 'w')
fFinal = open(pastaRelatorios + 'out_rel_final_' + data + '.txt', 'w')
#print >> f, 'Filename:', filename
#f.write('...\n')
fFail.write("DOCUMENTOS QUE NAO FOI DETECTADO ROSTO:\n")
fOK.write("DOCUMENTOS QUE FOI DETECTADO ROSTO:\n")
fFinal.write("RELATORIO FINAL em " + data + "\n\n")
fFinal.write("minSizeSetado: " + str(minSizeSetado) + "\n")


def calculaRecorteFace(x,y,w,h,widthImage,heightImage):
    # CALCULO O CENTRO DA FACE
    centroX = (x + w) / 2
    centroY = (y + h) / 2
    # print("x,y,w,h: ",x,y,w,h)
    # print("centroX,centroY: ",centroX,centroY)
    novoW = int(centroX/2 + w)
    if(novoW > widthImage):
        novoW = w
    novoH = int(centroY + h)
    if(novoH > heightImage):
        novoH = h
    # print("novoW,novoH: ",w,h)
    novoX = int(x - centroX/4)
    if(novoX < 0):
        novoX = x
    novoY = int(y - centroY/2)
    if(novoY < 0):
        novoY = y
    # print("novoX,novoY: ",x,y)
    return novoX,novoY,novoW,novoH


def verificaImagem( image, imageName, angulo ):
    global minSizeSetado, pastaFotosFinais, pasta_2Faces_FotosFinais

    # print("# Verificando Imagem {0} em {1} graus".format(imageName, angulo))
    resultado = 0;

    try:

        # Create the haar cascade
        faceCascade = cv2.CascadeClassifier(cascPath)

        # Grayscale the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = faceCascade.detectMultiScale(
           gray,
           scaleFactor = 1.1,
           minNeighbors = 4,
           minSize = (minSizeSetado, minSizeSetado)
           #flags = cv2.cv.CV_HAAR_SCALE_IMAGE
        )

        resultado = int(len(faces))

        heightImage, widthImage, channels = image.shape

        # 1 FACE
        if(resultado == 1):
            for (x,y,w,h) in faces:
                nX, nY, nW, nH = calculaRecorteFace(x,y,w,h,widthImage,heightImage)
                cropdFoto = image[nY:(nY+nH), nX:(nX+nW)] # Crop from x, y, w, h
                cv2.imwrite(pastaFotosFinais + imageName, cropdFoto)

        # MAIS DE 1
        if(resultado > 1):
            cv2.imwrite(pasta_2Faces_FotosFinais + imageName, image)

    except Exception:
        # fFail.write(imageName + ' = ERRO \n')
        # countIMGFail = countIMGFail + 1
        pass
    except:
        # fFail.write(imageName + ' = ERRO \n')
        # countIMGFail = countIMGFail + 1
        pass

    # print("Encontrado {0} faces, in {1}".format(len(faces), imageName))
    return resultado


def verificaAngulosPredF(image, nomeImagem):
    angulos = [45,90,180,270]
    encontrado = 'n'
    for angle in angulos:
        try:
            rotated = imutils.rotate_bound(image, angle)
            qtdFaces = verificaImagem( rotated, nomeImagem, angle)
            if(qtdFaces >= 1):
                encontrado = 's'
                break
        except Exception:
            pass
        except:
            pass
    # Se não pegar, vai de 30 em 30
    if(encontrado=='n'):
        encontrado = verificaVariosAngulos(image, nomeImagem)

    return encontrado

def verificaVariosAngulos(image, nomeImagem):
    encontrado = 'n'
    for angle in np.arange(0, 300, 30):
        try:
            rotated = imutils.rotate_bound(image, angle)
            qtdFaces = verificaImagem( rotated, nomeImagem, angle)
            if(qtdFaces >= 1):
                encontrado = 's'
                break
        except Exception:
            pass
        except:
            pass
    return encontrado


for file in os.listdir( pastaFotos ):
    #if file.endswith(sufixo) and file.endswith(prefixo,0,1):
    if file.endswith(prefixo,0,1):
        encontrado = 'n'
        nomeImagem = file
        image = cv2.imread(pastaFotos + nomeImagem)
        # verificaOriginal
        qtdFaces = verificaImagem(image, nomeImagem, 0)
        if(qtdFaces >= 1):
            encontrado = 's'
        elif(qtdFaces==0):
            # verifica angulos predefinidos
            encontrado = verificaAngulosPredF(image,nomeImagem)
        # FINAL
        if(encontrado=='s'):
            fOK.write('('+str(count)+')' + nomeImagem + ' = FACE ENCONTRADA \n')
            countIMGOK = countIMGOK + 1
        else:
            fFail.write('('+str(count)+')' + nomeImagem + ' = FACE NAO ENCONTRADA \n')
            countIMGFail = countIMGFail + 1
        count = count + 1
        if count % 500 == 0:
            print("Verificando Documento {0} de {1} - {2}".format(count, totalImagens, nomeImagem))
        # if count > 50:
        #     print("# break, count > 50")
        #     break


fFail.write("\n\n QTD:" + str(countIMGFail) + "\n")
fOK.write("\n\n QTD:" + str(countIMGOK) + "\n")

fFinal.write("\nQTD DOC NA PASTA:" + str(totalImagens) + "\n")
fFinal.write("\nQTD DOC ANALISADAS:" + str(count) + "\n")
fFinal.write("QTD DOC OK:" + str(countIMGOK) + "\n")
fFinal.write("QTD DOC FAIL:" + str(countIMGFail) + "\n\n")

# fFinal.write("DOCUMENTOS BONS COPIADOS PARA A PASTA: " + str(pastaFotosFinais) + "\n\n")
fFinal.write("\nTEMPO DE EXECUCAO: %s segundos." % (time.time() - start_time) + "\n\n")

fFail.close()
fOK.close()
fFinal.close()
