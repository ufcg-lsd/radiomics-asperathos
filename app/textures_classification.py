#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This application is a use case from the EU-Brazil Atmosphere project. For more
information on the project, visit our website at https://www.atmosphere-eubrazil.eu/.
The original application is hosted at the project's GitHub repository at
https://github.com/eubr-atmosphere/radiomics.

Copyright: QUIBIM SL – Quantitative Imaging Biomarkers in Medicine - www.quibim.com
"""

import pickle
from pathlib import Path
import numpy as np

def classify(textures):
    model = pickle.load(open(Path('classifiers',
                                  'logisticRegression_classifier.sav'), 'rb'))
    mean = np.load(Path('classifiers', 
                        'mean_textures.npy'))
    std = np.load(Path('classifiers', 
                        'std_textures.npy'))

    textures = textures - mean
    textures = textures / std

    label = model.predict(textures)
    
    return label