#!/usr/bin/python3
"""
An example sts2015/sick2014 classifier using the (Tai, 2015) approach
http://arxiv.org/abs/1503.00075 with mean vectors and model as in 4.2,
using the awesome Keras deep learning library.

Play with it to see effect of GloVe dimensionality, hidden layer
(and its size), various regularization etc.!

TODO: KL cost function

Prerequisites:
    * Get glove.6B.100d.txt from http://nlp.stanford.edu/projects/glove/
"""

from __future__ import print_function

import argparse

from keras.models import Graph
from keras.layers.core import Activation, Dense, Dropout
from keras.regularizers import l2
import numpy as np

import pysts.embedding as emb
import chios
import pysts.eval as ev


def prep_model(glove, dropout=0, l2reg=1e-4):
    model = Graph()

    # Process sentence embeddings
    model.add_input(name='e0', input_shape=(glove.N,))
    model.add_input(name='e1', input_shape=(glove.N,))
    model.add_node(name='e0_', input='e0',
                   layer=Dropout(dropout))
    model.add_node(name='e1_', input='e1',
                   layer=Dropout(dropout))

    # Generate element-wise features from the pair
    # (the Activation is a nop, merge_mode is the important part)
    model.add_node(name='sum', inputs=['e0_', 'e1_'], layer=Activation('linear'), merge_mode='sum')
    model.add_node(name='mul', inputs=['e0_', 'e1_'], layer=Activation('linear'), merge_mode='mul')

    # Use MLP to generate classes
    model.add_node(name='hidden', inputs=['sum', 'mul'], merge_mode='concat',
                   layer=Dense(50, W_regularizer=l2(l2reg)))
    model.add_node(name='hiddenS', input='hidden',
                   layer=Activation('sigmoid'))
    model.add_node(name='out', input='hiddenS',
                   layer=Dense(1, W_regularizer=l2(l2reg)))
    model.add_node(name='outS', input='out',
                   layer=Activation('sigmoid'))

    model.add_output(name='score', input='outS')
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark kst1503 on binary classification / point ranking task (anssel-yodaqa)")
    parser.add_argument("-N", help="GloVe dim", type=int, default=100)
    parser.add_argument("--enw", help="whether to run on enwiki inst. of CK12 dataset", type=int, default=0)
    args = parser.parse_args()

    glove = emb.GloVe(N=args.N)
    if args.enw == 1:
        ptrain = chios.load_chios('chios/trainmodel-enw4k.csv')
        ptest = chios.load_chios('chios/localval-enw4k.csv')
    else:
        ptrain = chios.load_chios('chios/trainmodel-ck12.csv')
        ptest = chios.load_chios('chios/localval-ck12.csv')

    model = prep_model(glove)
    model.compile(loss={'score': 'binary_crossentropy'}, optimizer='adam')
    model.fit_generator(chios.sample_questions(glove, ptrain), nb_epoch=20, samples_per_epoch=len(ptrain), callbacks=[chios.SampleValCB(glove, ptest)])
