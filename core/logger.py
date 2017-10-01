import sys
sys.dont_write_bytecode = True
import logging
import config.log_config as config

class Logging:
    def __init__(self,name,fname):
        # fname = 'logs/logfile.log'
        fid = open(fname,'w')
        fid.close()
        # create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(config.LOG_LEVEL)

        # create formatter
        formatter = logging.Formatter('[%(asctime)s : %(name)s : %(levelname)s] %(message)s')

        if not config.LOG_TO_FILE:
            # create console handler and set level to debug
            ch = logging.StreamHandler()
            ch.setLevel(config.LOG_LEVEL)


            # add formatter to ch
            ch.setFormatter(formatter)

            # add ch to logger
            self.logger.addHandler(ch)

        else:
            ch = logging.FileHandler(fname)
            ch.setLevel(config.LOG_LEVEL)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
