#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import random

from expsuite import PyExperimentSuite
import numpy
from pybrain.datasets import SequentialDataSet
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure.modules import LSTMLayer
from pybrain.supervised import RPropMinusTrainer



class Encoder(object):

  def __init__(self, num):
    self.num = num


  def encode(self, symbol):
    pass


  def random(self):
    pass


  def classify(self, encoding):
    pass



class BasicEncoder(Encoder):

  def encode(self, symbol):
    encoding = numpy.zeros(self.num)
    encoding[symbol] = 1
    return encoding


  def randomSymbol(self):
    return random.randint(self.num)


  def classify(self, encoding):
    return numpy.argmax(encoding)



class Dataset(object):

  def generateSequence(self):
    pass



class ReberDataset(Dataset):

  def generateSequence(self):
    pass



class SimpleDataset(Dataset):

  def __init__(self):
    self.sequences = [
      [6, 8, 7, 4, 2, 3, 0],
      [2, 9, 7, 8, 5, 3, 4, 6],
    ]

  def generateSequence(self):
    return list(random.choice(self.sequences))



class Suite(PyExperimentSuite):

  def reset(self, params, repetition):
    if params['encoding'] == 'basic':
      self.encoder = BasicEncoder(params['encoding_num'])
    else:
      raise Exception("Encoder not found")

    if params['dataset'] == 'simple':
      self.dataset = SimpleDataset()
    else:
      raise Exception("Dataset not found")

    self.computeCounter = 0

    self.history = []
    self.resets = []
    self.currentSequence = self.dataset.generateSequence()

    self.net = None


  def iterate(self, params, repetition, iteration):
    self.history.append(self.currentSequence.pop(0))

    reset = (len(self.currentSequence) == 0 and
             params['separate_sequences_with'] == 'reset')
    self.resets.append(reset)

    if len(self.currentSequence) == 0:
      self.currentSequence = self.dataset.generateSequence()

    if iteration < params['compute_after']:
      return None

    if iteration % params['compute_every'] == 0:
      self.computeCounter = params['compute_for']

    if self.computeCounter == 0:
      return None
    else:
      self.computeCounter -= 1

    n = params['encoding_num']

    net = self.net

    if iteration < params['disable_learning_after']:
      net = buildNetwork(n, params['num_cells'], n,
                         hiddenclass=LSTMLayer, bias=True, outputbias=False, recurrent=True)
      self.net = net
      net.reset()

      ds = SequentialDataSet(n, n)
      trainer = RPropMinusTrainer(net, dataset=ds)

      for i in xrange(1, len(self.history)):
        if not self.resets[i-1]:
          ds.addSample(self.encoder.encode(self.history[i-1]),
                       self.encoder.encode(self.history[i]))
        if self.resets[i]:
          ds.newSequence()

      if len(self.history) > 1:
        trainer.trainEpochs(params['num_epochs'])
        net.reset()

    prediction = None

    for i, symbol in enumerate(self.history):
      output = net.activate(self.encoder.encode(symbol))
      prediction = self.encoder.classify(output)

      if self.resets[i]:
        net.reset()

    truth = None if self.resets[-1] else self.currentSequence[0]

    return {"iteration": iteration,
            "current": self.history[-1],
            "reset": self.resets[-1],
            "prediction": prediction,
            "truth": truth}



if __name__ == '__main__':
  suite = Suite()
  suite.start()
