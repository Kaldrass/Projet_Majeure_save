#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 31 15:24:21 2022
@author: jonathan.bouyer
"""

import cv2
import numpy as np

def line_evaluator(rho,theta,x):
    return rho/np.sin(theta) - x*np.cos(theta)/np.sin(theta)

def lecture(img):
    img = img[int(0.02*img.shape[0]):int(0.98*img.shape[0]) , int(0.02*img.shape[1]):int(0.98*img.shape[1])]
    
    if (len(img.shape) == 3):
        ny,nx,nc = img.shape
        I = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    
    I = cv2.adaptiveThreshold(I, 255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 15)
    I = 255 - I
    
    d = int(0.9*I.shape[0]/168)
    d2 = int(0.25*I.shape[0]/168)
    SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d,d))
    SE2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d2,d2))
    
    d = int(I.shape[0]/168)
    
    I_f = cv2.morphologyEx(I, cv2.MORPH_CLOSE, SE2, iterations = 1)
    
    I_e = cv2.erode(I_f,SE)
    
    #Positionnement des portées (Transformée de Hough)
    res = img
    lines = cv2.HoughLines(I,1,np.pi/1000,int(img.shape[0]/2.5))
    s = np.sqrt(nx**2 + ny**2)
    T = []
    R = []
    dr = d
    nb = 0
    for l in lines:
        R.sort()
        for rho,theta in l:
            treated = False
            #On s'assure de ne pas avoir déjà une ligne similaire en mémoire
            if len(R) > 0:
                i = 0
                while (i < len(R) and R[i] < rho + d):
                    if abs(rho - R[i]) < 0.5*dr:
                        treated = True
                    i += 1
            if not(treated):
                R.append(rho)
                T.append(theta)
                nb += 1
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a*rho
                y0 = b*rho
                x1 = int(x0 + s*(-b))
                y1 = int(y0 + s*(a))
                x2 = int(x0 - s*(-b))
                y2 = int(y0 - s*(a))
                cv2.line(res,(x1,y1),(x2,y2),(255,0,0),1)
                
    #Repérage des notes
    notes = np.argwhere(I_e == 255) #Listes des coordonnées des "notes"
    notes_traitees = [] #Liste des positions des notes
    
    for n in notes:
        treated = False
        #On vérifie si la note a déjà été traitée
        for k in notes_traitees:
            if abs(k[0] - n[0]) < d and abs(k[1] - n[1]) < d:
                treated = True
                break
            
        V = [] #Voisinage de la note
        for k in notes:
            if abs(k[0] - n[0]) < d and abs(k[1] - n[1]) < d:
                V.append(k)
        #Calcul du barycentre du voisinage et ajout de ce dernier à la liste des notes traitées    
        if not(treated):
            B = [int(sum([V[k][0] for k in range(len(V))])/len(V)) , int(sum([V[k][1] for k in range(len(V))])/len(V))]
            notes_traitees.append(B)
            
    res_notes = img
    
    for b in notes_traitees:
        res_notes[b[0]-5:b[0]+5,b[1]-5:b[1]+5,0] = 255
        
    #Evaluation des notes
    tones = {}
    droites = sorted(zip(R,T))
    for n in notes_traitees:
        x = n[1]
        y = n[0]
        
        h = 0
        minimum = max(R) + 1
        
        i = 0
        #On recherche la droite la plus proche
        while i < len(droites) and droites[i][0] < y + 2*d:
            y_portee = line_evaluator(droites[i][0],droites[i][1],x)
            
            if abs(y_portee - y) < abs(minimum):
                minimum = y_portee - y
                h = i
                
            i += 1
        #Si l'écart à cette droite est trop grand, on ajoute/retire un demi-ton    
        h = h%5
        if minimum >= d/3:
            h -= 0.5
        elif minimum <= -d/3:
            h += 0.5
            
        tones[(y,x)] = h
    
    return tones
