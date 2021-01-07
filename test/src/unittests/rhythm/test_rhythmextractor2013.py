#!/usr/bin/env python

# Copyright (C) 2006-2016  Music Technology Group - Universitat Pompeu Fabra
#
# This file is part of Essentia
#
# Essentia is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the Affero GNU General Public License
# version 3 along with this program. If not, see http://www.gnu.org/licenses/

from essentia_test import *
from essentia.standard import MonoLoader, RhythmExtractor2013
from math import fabs

class TestRhythmExtractor2013(TestCase):

    def testRegression(self):
        audio = MonoLoader(filename=join(testdata.audio_dir, 'recorded', 'techno_loop.wav'))()
        rhythm = RhythmExtractor2013()

        bpm, _, _, _ ,_= rhythm(audio)
        self.assertAlmostEqualFixedPrecision(bpm, 124, 0) 
    def _runInstance(self, input, method="degara"):
        return RhythmExtractor2013(method=method)(input) 

    def _pulseTrain(self, bpm, sr, offset, dur):
        from math import floor
        period = int(floor(sr/(bpm/60.)))
        size = int(floor(sr*dur))
        phase = int(floor(offset*sr))

        if phase > period:
            phase = 0

        impulse = [0.0]*size
        for i in range(size):
            if i%period == phase:
                impulse[i] = 1.0
        return impulse

    def _assertVectorWithinVector(self, found, expected, precision=1e-7):
        for i in range(len(found)):
            for j in range(1,len(expected)):
                if found[i] <= expected[j] and found[i] >= expected[j-1]:
                    if fabs(found[i] - expected[j-1]) < fabs(expected[j] - found[i]):
                        self.assertAlmostEqual(found[i], expected[j-1], precision)
                    else:
                        self.assertAlmostEqual(found[i], expected[j], precision)

    def _assertEqualResults(self, result, expected):
        self.assertEqual(result[0], expected[0]) #bpm
        self.assertEqualVector(result[1], expected[1]) # ticks
        self.assertEqual(result[2], expected[2]) # confidence
        self.assertEqualVector(result[3], expected[3]) # estimates
        self.assertEqualVector(result[4], expected[4]) # bpmIntervals

    def testEmptyMultiFeature(self):
        input = array([0.0]*100*1024) # 100 frames of size 1024
        expected = [0.0, [], 0.0, [],[]]
        result = self._runInstance(input, method="multifeature")
        self.assertEqualVector(result, expected)


    def testEmptyDegara(self):
        input = array([0.0]*100*1024) # 100 frames of size 1024
        expected = [0.0, [], 0.0, [], []]
        result = self._runInstance(input, method="degara")
        self.assertEqualVector(result, expected)

    def testZeroMultiFeature(self):
        input = array([0.0]*100*1024) # 100 frames of size 1024
        expected = [0.0, [], 0.0, [], []] # extra frame for confidence
        result = self._runInstance(input, method="multifeature" )
        self._assertEqualResults(result, expected)

    def testZeroDegara(self):
        input = array([0.0]*100*1024) # 100 frames of size 1024
        expected = [0.0, [], 0.0, [], []] # extra frame for confidence
        result = self._runInstance(input, method="degara" )
        self._assertEqualResults(result, expected)

    def _createPulseTrain140(self): 
        return(self._pulseTrain(bpm=140, sr=44100., offset=.1, dur=10))

    def _createPulseTrainCombo(self):
        # Define impulse train at 90bpm no offset
        impulseTrain90 = self._pulseTrain(bpm=90., sr=44100., offset=0., dur=20.)
        # Define impulse train at 140bpm no offset
        impulseTrain140 = self._pulseTrain(bpm=140., sr=44100., offset=.1, dur=10.)
        # Define impulse train at 200bpm with offset
        impulseTrain200 = self._pulseTrain(bpm=200., sr=44100., offset=.2, dur=10.)
        # Define impulse train at 200bpm with no offset
        impulseTrain200b = self._pulseTrain(bpm=200., sr=44100., offset=0., dur=25.)
        # Define Combination impulse train at 140-90-200-200 bpm
        return(impulseTrain90 + impulseTrain140 + impulseTrain200 + impulseTrain200b)
    
    def testImpulseTrainMultifeature(self):
        # Define expected values
        impulseTrain140=self._createPulseTrain140()
        expectedBpm = 140
        expectedTicks = [i/44100. for i in range(len(impulseTrain140)) if impulseTrain140[i]!= 0]
        expectedConfidence =3.8
        #print("\nExpected Ticks Multifeature\n")
        #print(expectedTicks)
        # Test Multifeature with impulseTrain140
        result = self._runInstance(impulseTrain140,method="multifeature")
        # Check bpm
        self.assertAlmostEqual(result[0], expectedBpm, 1e-2)
        # Check ticks
        self._assertVectorWithinVector(result[1], expectedTicks, 0.2)
        #print("\nActual Ticks Multifeature\n")
        #print(result[1])
        # Check confidence
        self.assertAlmostEqual(result[2], expectedConfidence,1.0)
        # Check estimated bpm
        for i in range(len(result[3])):
            self.assertAlmostEqual(result[3][i], expectedBpm, 1.)
        # Check bpm intervals
        for i in range(len(result[4])):
            self.assertAlmostEqual(result[4][i], 60./expectedBpm, 0.2)
        # Test Multifeature with this combo impulseTrain
        result = self._runInstance(self._createPulseTrainCombo(),method="multifeature")
        # Define expected values
        impulseTrainCombo= self._createPulseTrainCombo()
        expectedBpm = 117 
        expectedTicks = [i/44100. for i in range(len(impulseTrainCombo)) if impulseTrainCombo[i]!= 0]
        expectedConfidence = 0.0
        #print("\nExpected Ticks Combo Multifeature\n")
        #print(expectedTicks)
        # Check bpm
        self.assertAlmostEqual(result[0], expectedBpm, .5)
        # Check ticks
        self._assertVectorWithinVector(result[1], expectedTicks,0.5 )
        # Check confidence
        expectedConfidence = 3.0
        self.assertAlmostEqual(result[2], expectedConfidence, 1.0)
        # Check estimate bpm
        for i in range(len(result[3])):
            self.assertAlmostEqual(result[3][i], expectedBpm, 5.0)
        # bpm intervals: we may need to take into account also multiples of 90,
        # 140 and 200.
        # Check bpm intervals
        expectedBpmIntervals = [60/90., 60/140., 60/200.]
        self._assertVectorWithinVector(result[4], expectedBpmIntervals)
        result = self._runInstance(self._createPulseTrainCombo(),method="multifeature")
        expectedBpmVector = [50, 100, 200]
        #print("Actual Ticks Combo Multifeature")
        #print(result[1])
        # bpm: here rhythmextractor is choosing 0.5*expected_bpm, that's why we are
        # comparing the resulting bpm with the expected_bpm_vector:
        self._assertVectorWithinVector([result[0]], expectedBpmVector, 1.)
        self._assertVectorWithinVector(result[1], expectedTicks, 0.24)
        self.assertAlmostEqual(result[2], expectedConfidence, 1.0)
        self._assertVectorWithinVector(result[3], expectedBpmVector, 0.5)
        self._assertVectorWithinVector(result[4], expectedBpmIntervals, 0.05)

    def testImpulseTrainDegara(self):
        # Define expected values
        impulseTrain140=self._createPulseTrain140()
        expectedBpm = 139.68
        expectedTicks = [i/44100. for i in range(len(impulseTrain140)) if impulseTrain140[i]!= 0]
        #print("\nExpected Ticks Degara\n")
        #print(expectedTicks)
        # Degara has no confidence, set expected value to zero.
        expectedConfidence = 0.0  
        # Test Multifeature with impulseTrain140
        result = self._runInstance(impulseTrain140,method="degara")
        #print("\nn Actual Ticks Degara\n")
        #print(result[1])
        # Check bpm
        self.assertAlmostEqual(result[0], expectedBpm, 1e-2)
        # Check ticks
        self._assertVectorWithinVector(result[1], expectedTicks, 0.2)
        # NB Degara has no confidence
        self.assertEqual(result[2], expectedConfidence)
        # Check estimated bpm
        for i in range(len(result[3])):
            self.assertAlmostEqual(result[3][i], expectedBpm, 1.)
        # Check bpm intervals
        for i in range(len(result[4])):
            self.assertAlmostEqual(result[4][i], 60./expectedBpm, 0.2)
        # Test Multifeature with this combo impulseTrain
        result = self._runInstance(self._createPulseTrainCombo(),method="degara")
        # Define expected values
        impulseTrainCombo=self._createPulseTrainCombo()
        expectedBpm = 117 
        expectedTicks = [i/44100. for i in range(len(impulseTrainCombo)) if impulseTrainCombo[i]!= 0]
        #print("\nExpected Ticks Combo Degara\n")
        #print(expectedTicks)
        # Check bpm
        self.assertAlmostEqual(result[0], expectedBpm, .5)
        # Check ticks
        self._assertVectorWithinVector(result[1], expectedTicks,0.24)
        # No confidence for degara, should always check to be zero.
        self.assertEqual(result[2], expectedConfidence)
        # Check estimate bpm
        for i in range(len(result[3])):
            self.assertAlmostEqual(result[3][i], expectedBpm, 5.0)
        # bpm intervals: we may need to take into account also multiples of 90,
        # 140 and 200.
        # Check bpm intervals
        expectedBpmIntervals = [60/90., 60/140., 60/200.]
        self._assertVectorWithinVector(result[4], expectedBpmIntervals)
        result = self._runInstance(self._createPulseTrainCombo(),method="degara")
        #print("\nActual Ticks Combo Degara\n")
        #print(result[1])
        expectedBpmVector = [50, 100, 200]
        # bpm: here rhythmextractor is choosing 0.5*expected_bpm, that's why we are
        # comparing the resulting bpm with the expected_bpm_vector:
        self._assertVectorWithinVector([result[0]], expectedBpmVector, 1.)
        self._assertVectorWithinVector(result[1], expectedTicks, 0.24)
        # NB Degara has no confidence
        self.assertEqual(result[2], expectedConfidence)
        self._assertVectorWithinVector(result[3], expectedBpmVector, 0.5)
        self._assertVectorWithinVector(result[4], expectedBpmIntervals, 0.05)


suite = allTests(TestRhythmExtractor2013)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(suite)
