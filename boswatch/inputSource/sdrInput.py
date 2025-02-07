#!/usr/bin/python
# -*- coding: utf-8 -*-
"""!
    ____  ____  ______       __      __       __       _____
   / __ )/ __ \/ ___/ |     / /___ _/ /______/ /_     |__  /
  / __  / / / /\__ \| | /| / / __ `/ __/ ___/ __ \     /_ <
 / /_/ / /_/ /___/ /| |/ |/ / /_/ / /_/ /__/ / / /   ___/ /
/_____/\____//____/ |__/|__/\__,_/\__/\___/_/ /_/   /____/
                German BOS Information Script
                     by Bastian Schroll

@file:        sdrInput.py
@date:        28.10.2018
@author:      Bastian Schroll
@description: Input source for sdr with rtl_fm
"""
import logging
import time
from boswatch.utils import paths
from boswatch.processManager import ProcessManager
from boswatch.inputSource.inputBase import InputBase

logging.debug("- %s loaded", __name__)


class SdrInput(InputBase):
    """!Class for the sdr input source"""

    def _runThread(self, dataQueue, sdrConfig, decoderConfig):
        sdrProc = None
        mmProc = None
        try:
            sdrProc = ProcessManager(str(sdrConfig.get("rtlPath", default="rtl_fm")))
            sdrProc.addArgument("-d " + str(sdrConfig.get("device", default="0")))     # device id
            sdrProc.addArgument("-f " + str(sdrConfig.get("frequency")))               # frequencies
            sdrProc.addArgument("-p " + str(sdrConfig.get("error", default="0")))      # frequency error in ppm
            sdrProc.addArgument("-l " + str(sdrConfig.get("squelch", default="1")))    # squelch
            sdrProc.addArgument("-g " + str(sdrConfig.get("gain", default="100")))     # gain
            if (sdrConfig.get("fir_size", default=None) is not None):
                sdrProc.addArgument("-F " + str(sdrConfig.get("fir_size")))            # fir_size
            sdrProc.addArgument("-M fm")                                               # set mode to fm
            sdrProc.addArgument("-E DC")                                               # set DC filter
            sdrProc.addArgument("-s 22050")                                            # bit rate of audio stream
            sdrProc.setStderr(open(paths.LOG_PATH + "rtl_fm.log", "a"))
            sdrProc.start()

            mmProc = self.getDecoderInstance(decoderConfig, sdrProc.stdout)
            mmProc.start()

            logging.info("start decoding")
            while self._isRunning:
                if not sdrProc.isRunning:
                    logging.warning("rtl_fm was down - trying to restart in 10 seconds")
                    time.sleep(10)

                    sdrProc.start()
                    if sdrProc.isRunning:
                        logging.info("rtl_fm is back up - restarting multimon...")
                        mmProc.setStdin(sdrProc.stdout)
                        mmProc.start()
                elif not mmProc.isRunning:
                    logging.warning("multimon was down - try to restart")
                    mmProc.start()
                elif sdrProc.isRunning and mmProc.isRunning:
                    line = mmProc.readline()
                    if line:
                        self.addToQueue(line)
        except:
            logging.exception("error in sdr input routine")
        finally:
            mmProc.stop()
            sdrProc.stop()
